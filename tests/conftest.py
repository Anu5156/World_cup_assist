import os
# Clear LLM API keys from environment before importing application modules
# to guarantee tests run offline and do not trigger cloud API calls.
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

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
        gemini_api_key="",
        anthropic_api_key="",
    )
