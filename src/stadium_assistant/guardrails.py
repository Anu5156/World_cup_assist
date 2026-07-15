"""Guardrails: input sanitisation, prompt-injection defence and output checks.

Security posture for a public-facing assistant:
  * Reject empty or over-long input before it reaches the model.
  * Strip control characters that could corrupt logs or prompts.
  * Flag (but do not silently execute) common prompt-injection patterns so the
    orchestrator can neutralise them and the model is told to ignore them.
  * Sanity-check model output before returning it to the user.

These are defence-in-depth measures, not a claim of perfect safety.
IMPORTANT NOTE: The regex in _INJECTION_PATTERNS is a telemetry signal (heuristic check)
rather than a robust blocklist. It is expected to miss paraphrases, non-English inputs,
or obfuscation (e.g. base64). The primary, true defence against injection is structuring
untrusted user text strictly as data wrapped in <user_question> delimiters, coupled with
system prompt instructions that mandate treating all such data as untrusted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Patterns that frequently appear in attempts to override system instructions.
# Matching is case-insensitive and used only to set a flag, never to block a
# legitimate question outright.
_INJECTION_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore (?:all |previous |the )*(?:instructions|prompt|rules)",
        r"disregard (?:the |all )*(?:above|previous|system)",
        r"you are now",
        r"forget (everything|your instructions)",
        r"system prompt",
        r"reveal (your )?(prompt|instructions|system)",
        r"act as (a |an )?(?:dan|jailbreak)",
    )
)

# Control characters except common whitespace (tab, newline, carriage return).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ValidationError(ValueError):
    """Raised when input cannot be safely processed."""


@dataclass
class SanitizedInput:
    """Result of sanitising a raw user message."""

    text: str
    injection_suspected: bool


def sanitize_message(raw: str, max_chars: int) -> SanitizedInput:
    """Validate and clean a raw user message.

    Raises ValidationError for input that is empty after trimming or that
    exceeds the configured length. Removes control characters and collapses
    excessive whitespace. Sets ``injection_suspected`` when a known override
    pattern is present so the caller can harden the prompt.
    """
    if raw is None:
        raise ValidationError("Message is required.")

    text = _CONTROL_CHARS.sub("", raw).strip()
    text = re.sub(r"\s{3,}", "  ", text)

    if not text:
        raise ValidationError("Message cannot be empty.")
    if len(text) > max_chars:
        raise ValidationError(f"Message exceeds {max_chars} characters.")

    injection = any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
    return SanitizedInput(text=text, injection_suspected=injection)


def check_output(text: str) -> str:
    """Final safety pass on model output before it reaches the user.

    Trims whitespace and guards against an empty response by substituting a
    safe fallback. Kept intentionally small; heavier moderation would plug in
    here without changing callers.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return (
            "I could not generate a full answer just now. Please rephrase, or "
            "ask a staff member or volunteer at the nearest Guest Services booth."
        )
    return cleaned
