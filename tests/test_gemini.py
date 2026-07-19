import json
import logging
from unittest.mock import MagicMock, patch
import pytest
import httpx
from stadium_assistant.config import Settings
from stadium_assistant.llm import GeminiEngine, build_engine


def test_build_engine_gemini():
    settings = Settings(llm_provider="gemini", gemini_api_key="AIzaSyTest")
    engine = build_engine(settings)
    assert isinstance(engine, GeminiEngine)


def test_gemini_generate_success():
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="AIzaSyTest",
        llm_model="gemini-1.5-flash",
    )
    engine = GeminiEngine(settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Hello world from Gemini!"}]}}]
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        reply = engine.generate("sys", "user", "en")
        assert reply == "Hello world from Gemini!"
        mock_post.assert_called_once()


def test_gemini_generate_error_fallback():
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="AIzaSyTest",
        llm_model="gemini-1.5-flash",
    )
    engine = GeminiEngine(settings)

    with patch("httpx.Client.post", side_effect=httpx.HTTPError("Network down")):
        reply = engine.generate("sys", "Where is Gate A?", "en")
        assert "offline" in reply.lower() or "welcome" in reply.lower() or "gate a" in reply.lower()


def test_gemini_sk_warning(caplog):
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="sk-openai-key-in-gemini",
        llm_model="gemini-1.5-flash",
    )
    engine = GeminiEngine(settings)

    with patch("httpx.Client.post", side_effect=httpx.HTTPError("Network down")):
        with caplog.at_level(logging.WARNING):
            engine.generate("sys", "user", "en")
            assert any("starts with 'sk-'" in record.message for record in caplog.records)


def test_gemini_stream_success():
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="AIzaSyTest",
        llm_model="gemini-1.5-flash",
    )
    engine = GeminiEngine(settings)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = [
        "data: "
        + json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Streamed token"}]}}]}
        ),
    ]

    # Mock the stream context manager
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.stream.return_value.__enter__.return_value = mock_response

    with patch("httpx.Client", return_value=mock_client):
        tokens = list(engine.generate_stream("sys", "user", "en"))
        assert len(tokens) == 1
        assert tokens[0] == "Streamed token"


def test_gemini_stream_error_fallback():
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="AIzaSyTest",
        llm_model="gemini-1.5-flash",
    )
    engine = GeminiEngine(settings)

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.stream.side_effect = httpx.HTTPError("Stream down")

    with patch("httpx.Client", return_value=mock_client):
        tokens = list(engine.generate_stream("sys", "user", "en"))
        assert len(tokens) == 1
        assert "welcome" in tokens[0].lower() or "offline" in tokens[0].lower()
