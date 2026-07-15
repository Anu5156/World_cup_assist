"""Multilingual helpers.

World Cup 2026 is hosted across the United States, Canada and Mexico, so
English, Spanish and French are first-class. We additionally recognise a
broad set of common visitor languages. The LLM handles free-form generation
in any language; this module only normalises language codes and provides the
small set of fixed UI strings used by the deterministic offline engine.
"""

from __future__ import annotations

import json
from pathlib import Path

# Host-nation and high-traffic visitor languages. The value is the endonym,
# shown back to the user so they can confirm the assistant understood them.
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "pt": "Portugues",
    "de": "Deutsch",
    "it": "Italiano",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "ru": "Russian",
}

DEFAULT_LANGUAGE = "en"

_WEB_DIR = Path(__file__).resolve().parents[2] / "web"
_cache: dict[str, dict[str, str]] = {}


def normalize_language(code: str | None) -> str:
    """Reduce an arbitrary language tag to a supported base code.

    Accepts values such as "en", "EN", "en-US", "es_MX". Unknown or empty
    inputs fall back to the default language rather than raising, so a bad
    client value never breaks a request.
    """
    if not code:
        return DEFAULT_LANGUAGE
    base = code.strip().lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def language_name(code: str) -> str:
    """Human-readable endonym for a supported code."""
    return SUPPORTED_LANGUAGES.get(normalize_language(code), "English")


def phrase(language: str, slot: str) -> str:
    """Return a fixed offline phrase, falling back to English."""
    lang = normalize_language(language)
    if lang not in _cache:
        try:
            path = _WEB_DIR / "i18n" / f"{lang}.json"
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except Exception:
            _cache[lang] = {}

    val = _cache[lang].get(slot)
    if val is not None:
        return val

    # Fallback to English
    if "en" not in _cache:
        try:
            path = _WEB_DIR / "i18n" / "en.json"
            with open(path, encoding="utf-8") as f:
                _cache["en"] = json.load(f)
        except Exception:
            _cache["en"] = {}

    return _cache["en"].get(slot, "")

