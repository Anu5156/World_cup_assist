"""HTTP API and static UI host.

Exposes a small, well-validated surface:
  GET  /health        liveness + whether the cloud LLM is active
  GET  /languages     supported languages for the UI selector
  POST /api/assist    the assistant endpoint
  GET  /              the accessible single-page UI

Security choices: Pydantic validates every field; a lightweight per-client
rate limiter blunts abuse; CORS is restricted; internal errors never leak
stack traces to the client.
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .assistant import Assistant
from .config import get_settings
from .context import AccessibilityNeed, Role, StadiumStatus, UserContext
from .guardrails import ValidationError
from .i18n import SUPPORTED_LANGUAGES

_WEB_DIR = Path(__file__).resolve().parents[2] / "web"

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

if not settings.ops_api_key:
    logger.warning(
        "\n========================================================================\n"
        "WARNING: OPS_API_KEY is not set. All operations write routes (POST) will\n"
        "fail closed and reject status updates.\n"
        "========================================================================"
    )

assistant = Assistant(settings)


class StadiumStatusStore:
    """Thread-safe store for the global StadiumStatus object."""

    def __init__(self) -> None:
        self._status = StadiumStatus()
        self._lock = threading.Lock()

    def get(self) -> StadiumStatus:
        with self._lock:
            return self._status

    def set(self, status: StadiumStatus) -> None:
        with self._lock:
            self._status = status


_stadium_status_store = StadiumStatusStore()


app = FastAPI(
    title="World Cup 2026 Accessible Fan Assistant",
    version=__version__,
    description=(
        "Context-aware, multilingual GenAI assistant for venue accessibility "
        "and navigation."
    ),
)

# CORS setup using ALLOWED_ORIGINS setting.
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Ops-Key"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    csp_directives = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "connect-src 'self'",
        "img-src 'self' data:",
        "frame-ancestors 'none'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    return response


class AssistRequest(BaseModel):
    """Validated request body for the assist endpoint."""

    message: str = Field(..., min_length=1, max_length=settings.max_message_chars)
    language: str = Field(default="en", max_length=10)
    role: Role = Field(default=Role.FAN)
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=120)


class AssistResponse(BaseModel):
    """Response body, including auditable metadata about the decision."""

    reply: str
    intent: str
    language: str
    used_llm: bool
    injection_suspected: bool
    cache_hit: bool = False
    facts_used: list[str]


# --- Proxy-aware client IP resolution -----------------------------------------
def _resolve_client_ip(request: Request) -> str:
    """Resolve the client's IP address.

    If TRUST_PROXY is enabled, retrieves the leftmost IP in the X-Forwarded-For header.
    Otherwise, defaults to request.client.host.
    """
    if settings.trust_proxy:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --- Minimal in-process rate limiter (per client IP) --------------------------
_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(client_key: str) -> bool:
    now = time.monotonic()
    window = settings.rate_limit_window_seconds
    bucket = _hits[client_key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()

    # Sweep empty buckets on write to avoid unbounded memory growth when keys exceed 1000
    if len(_hits) > 1000:
        for k in list(_hits.keys()):
            b = _hits[k]
            while b and now - b[0] > window:
                b.popleft()
            if not b:
                _hits.pop(k, None)

    if len(bucket) >= settings.rate_limit_requests:
        return True
    bucket.append(now)
    return False


# --- Operations authorization dependency --------------------------------------
def require_ops_key(x_ops_key: str | None = Header(None, alias="X-Ops-Key")) -> None:
    """Validate X-Ops-Key header against the configured OPS_API_KEY.

    Fails closed if OPS_API_KEY is not configured on the server.
    """
    if not settings.ops_api_key:
        raise HTTPException(
            status_code=401,
            detail="Operations write access is disabled because OPS_API_KEY is not configured.",
        )
    if not x_ops_key or not secrets.compare_digest(x_ops_key, settings.ops_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid X-Ops-Key header.")


_sse_clients: set[asyncio.Queue] = set()


@app.get("/api/stadium/status", response_model=StadiumStatus)
def get_stadium_status() -> StadiumStatus:
    return _stadium_status_store.get()


@app.get("/api/stadium/stream")
async def stadium_stream(request: Request) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue()
    # Send current state immediately on connect
    current_status = _stadium_status_store.get()
    queue.put_nowait(current_status.model_dump_json())
    _sse_clients.add(queue)

    async def event_generator() -> AsyncIterator[str]:
        try:
            while True:
                # Wait for updates or heartbeat ping every 25 seconds
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _sse_clients.discard(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/stadium/status", response_model=StadiumStatus)
async def update_stadium_status(
    status: StadiumStatus,
    request: Request,
    _auth: None = Depends(require_ops_key),
) -> StadiumStatus:
    # Rate limit the ops status update POST too.
    client_key = _resolve_client_ip(request)
    if _rate_limited(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )
    _stadium_status_store.set(status)
    # Broadcast to all connected SSE clients
    status_json = status.model_dump_json()
    for q in list(_sse_clients):
        try:
            q.put_nowait(status_json)
        except Exception:
            pass
    return _stadium_status_store.get()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "llm_online": settings.llm_online,
        "max_message_chars": settings.max_message_chars,
    }


@app.get("/languages")
def languages() -> dict:
    return {"languages": SUPPORTED_LANGUAGES}


@app.post("/api/assist", response_model=AssistResponse)
def assist(body: AssistRequest, request: Request) -> AssistResponse:
    client_key = _resolve_client_ip(request)
    if _rate_limited(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )

    try:
        context = UserContext(
            message=body.message,
            language=body.language,
            role=body.role,
            accessibility_needs=body.accessibility_needs,
            location=body.location,
        )
        result = assistant.respond(context, stadium_status=_stadium_status_store.get())
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as err:  # noqa: BLE001 - never leak internals to the client
        logger.exception("assist failed")
        raise HTTPException(
            status_code=502,
            detail="The assistant is temporarily unavailable. Please try again.",
        ) from err

    return AssistResponse(
        reply=result.reply,
        intent=result.intent.value,
        language=result.language,
        used_llm=result.used_llm,
        injection_suspected=result.injection_suspected,
        cache_hit=result.cache_hit,
        facts_used=result.facts_used,
    )


@app.post("/api/assist/stream")
def assist_stream(body: AssistRequest, request: Request) -> StreamingResponse:
    """Streaming variant of /api/assist.

    Yields ``text/event-stream`` SSE events:
    - Token chunks:  ``data: {"token": "..."}\n\n``
    - Final event:   ``data: {"done": true, "reply": "...", ...}\n\n``

    The existing ``/api/assist`` endpoint is unchanged and used by all tests.
    """
    client_key = _resolve_client_ip(request)
    if _rate_limited(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )

    try:
        context = UserContext(
            message=body.message,
            language=body.language,
            role=body.role,
            accessibility_needs=body.accessibility_needs,
            location=body.location,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def _generate() -> Iterator[str]:  # noqa: ANN202
        try:
            for chunk in assistant.respond_stream(
                context, stadium_status=_stadium_status_store.get()
            ):
                yield f"data: {chunk}\n\n"
        except ValidationError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except Exception:
            logger.exception("assist_stream failed")
            yield f"data: {json.dumps({'error': 'Assistant temporarily unavailable.'})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_WEB_DIR / "index.html")


# Serve CSS/JS. Mounted last so it does not shadow the API routes above.
if _WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")
