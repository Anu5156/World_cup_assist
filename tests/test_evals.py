"""Parametrized behavioural evaluation suite.

Each case in ``eval_cases.yaml`` is run against the deterministic offline engine
in CI (no ANTHROPIC_API_KEY required, zero cost, <1 s per case).

Pass ``--live`` on the pytest command line to also run ``live_only`` cases against
the real Anthropic API:

    pytest tests/test_evals.py --live

The ``--live`` flag only takes effect when ANTHROPIC_API_KEY is set in the
environment; otherwise ``live_only`` cases are skipped regardless.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from stadium_assistant.assistant import Assistant
from stadium_assistant.config import Settings
from stadium_assistant.context import AccessibilityNeed, UserContext
from stadium_assistant.llm import AnthropicEngine, OfflineEngine

# ── CLI option ────────────────────────────────────────────────────────────────

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run live_only eval cases against the real Anthropic API.",
    )


# ── Fixture: load all cases ───────────────────────────────────────────────────

_CASES_FILE = Path(__file__).parent / "eval_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    with _CASES_FILE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["cases"]


_ALL_CASES = _load_cases()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_assistant(live: bool) -> Assistant:
    """Return an Assistant backed by the offline engine (or Anthropic if live)."""
    if live and os.getenv("ANTHROPIC_API_KEY"):
        settings = Settings()  # picks up real key from env
        return Assistant(settings, engine=AnthropicEngine(settings))
    return Assistant(settings=Settings(anthropic_api_key=""), engine=OfflineEngine())


def _make_context(case: dict[str, Any]) -> UserContext:
    needs = [AccessibilityNeed(n) for n in case.get("needs", [])]
    return UserContext(
        message=case["message"],
        language=case.get("language", "en"),
        accessibility_needs=needs,
    )


# ── Parametrized test ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", _ALL_CASES, ids=[c["id"] for c in _ALL_CASES])
def test_eval(case: dict[str, Any], request: pytest.FixtureRequest) -> None:
    """Assert behavioural properties for each golden eval case."""
    live: bool = request.config.getoption("--live", default=False)

    if case.get("live_only"):
        if not live:
            pytest.skip("live_only: pass --live to run against the real API")
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("live_only: ANTHROPIC_API_KEY not set")

    assistant = _build_assistant(live=case.get("live_only", False) and live)
    ctx = _make_context(case)
    result = assistant.respond(ctx)
    reply_lower = result.reply.lower()

    # ── Intent classification ─────────────────────────────────────────────────
    if expected_intent := case.get("intent"):
        assert result.intent.value == expected_intent, (
            f"[{case['id']}] Expected intent={expected_intent!r}, "
            f"got {result.intent.value!r}\nReply: {result.reply[:200]}"
        )

    # ── Forbidden phrases ─────────────────────────────────────────────────────
    for phrase in case.get("must_not_contain", []):
        assert phrase.lower() not in reply_lower, (
            f"[{case['id']}] Forbidden phrase {phrase!r} found in reply.\n"
            f"Reply: {result.reply[:400]}"
        )

    # ── Required phrases (at least one must match) ────────────────────────────
    required = case.get("must_contain", [])
    if required:
        matched = any(phrase.lower() in reply_lower for phrase in required)
        assert matched, (
            f"[{case['id']}] None of {required!r} found in reply.\n"
            f"Reply: {result.reply[:400]}"
        )
