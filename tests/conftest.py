"""Shared test configuration and fixtures."""

import pytest

from stadium_assistant import app as app_mod
from stadium_assistant.config import Settings


@pytest.fixture(autouse=True)
def mock_settings() -> None:
    """Mock application settings for all tests to use standard test values."""
    app_mod.settings = Settings(
        ops_api_key="testkey",
        allowed_origins="http://localhost:8000,http://127.0.0.1:8000",
        trust_proxy=True,
        max_message_chars=800,
    )
