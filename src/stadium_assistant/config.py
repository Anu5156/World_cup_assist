"""Application configuration.

All secrets and tunables are read from the environment so that nothing
sensitive is ever committed to source control. The app is designed to run
fully offline (deterministic fallback) when no API key is present, which keeps
it testable and reproducible for reviewers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_int(name: str, default: int) -> int:
    """Read an int from the environment, falling back safely on bad input."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings resolved once at startup."""

    # LLM provider. "gemini" or "anthropic" uses the cloud API when a key is set;
    # otherwise the deterministic offline engine is always used.
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gemini-1.5-flash")
    )
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    llm_timeout_seconds: int = field(
        default_factory=lambda: _get_int("LLM_TIMEOUT_SECONDS", 20)
    )

    # Guardrails
    max_message_chars: int = field(default_factory=lambda: _get_int("MAX_MESSAGE_CHARS", 800))

    # Simple in-process rate limiting (requests per window, per client key)
    rate_limit_requests: int = field(default_factory=lambda: _get_int("RATE_LIMIT_REQUESTS", 30))
    rate_limit_window_seconds: int = field(
        default_factory=lambda: _get_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    )

    # Operations & CORS settings
    ops_api_key: str = field(default_factory=lambda: os.getenv("OPS_API_KEY", ""))
    allowed_origins: str = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
    )
    trust_proxy: bool = field(
        default_factory=lambda: os.getenv("TRUST_PROXY", "false").lower() in ("true", "1")
    )

    @property
    def llm_online(self) -> bool:
        """True only when a real cloud call can be made."""
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key)
        elif self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False


def get_settings() -> Settings:
    """Return a fresh Settings snapshot (re-reads env; handy for tests)."""
    return Settings()
