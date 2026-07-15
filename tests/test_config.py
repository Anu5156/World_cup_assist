"""Tests for the dynamic settings loading behavior."""

from stadium_assistant.config import get_settings


def test_get_settings_re_reads_env(monkeypatch) -> None:
    """Verify that get_settings() correctly reflects environment variables

    that are monkeypatched/modified after import time.
    """
    # 1. Clear env vars to establish baseline defaults
    monkeypatch.delenv("OPS_API_KEY", raising=False)
    monkeypatch.delenv("MAX_MESSAGE_CHARS", raising=False)

    baseline = get_settings()
    assert baseline.ops_api_key == ""
    assert baseline.max_message_chars == 800

    # 2. Monkeypatch new values
    monkeypatch.setenv("OPS_API_KEY", "monkeykey")
    monkeypatch.setenv("MAX_MESSAGE_CHARS", "123")

    # 3. Retrieve settings again and assert they reflect the changes
    updated = get_settings()
    assert updated.ops_api_key == "monkeykey"
    assert updated.max_message_chars == 123
