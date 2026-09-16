from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_unconfigured_settings():
    with patch("app.core.config.settings.GEMINI_API_KEY", None):
        yield


@pytest.fixture
def mock_configured_settings():
    with patch(
        "app.core.config.settings.GEMINI_API_KEY",
        "AIza-test-api-key-that-is-long-enough-12345",
    ):
        yield


@pytest.fixture
def mock_placeholder_settings():
    with patch("app.core.config.settings.GEMINI_API_KEY", "your-api-key-here"):
        yield


@pytest.fixture
def mock_short_settings():
    with patch("app.core.config.settings.GEMINI_API_KEY", "short-key"):
        yield


@pytest.fixture
def mock_gemini_client():
    with patch("google.genai.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_ai_status_unconfigured(mock_unconfigured_settings):
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "gemini"
    assert data["configured"] is False
    assert data["status"] == "missing_api_key"


def test_ai_status_configured(mock_configured_settings, mock_gemini_client):
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "gemini"
    assert data["configured"] is True
    assert data["status"] == "ready"
    assert "api_key" not in data


def test_ai_status_placeholder(mock_placeholder_settings):
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["status"] == "invalid_api_key"


def test_ai_status_short_key(mock_short_settings):
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["status"] == "invalid_api_key"


def test_ai_generate_missing_prompt(mock_configured_settings):
    # Validation error from pydantic (422) for missing field
    response = client.post("/api/ai/generate", json={})
    assert response.status_code == 422


def test_ai_generate_empty_prompt(mock_configured_settings):
    # Validation error for empty prompt (422) min_length=1
    response = client.post("/api/ai/generate", json={"prompt": ""})
    assert response.status_code == 422


def test_ai_generate_whitespace_prompt(mock_configured_settings):
    # Our custom validation in the router (400)
    response = client.post("/api/ai/generate", json={"prompt": "   "})
    assert response.status_code == 400
    assert "cannot be empty or whitespace-only" in response.json()["detail"]


def test_ai_generate_unconfigured(mock_unconfigured_settings):
    response = client.post("/api/ai/generate", json={"prompt": "test prompt"})
    assert response.status_code == 503
    assert "AI provider is not configured" in response.json()["detail"]


def test_ai_generate_success(mock_configured_settings, mock_gemini_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "This is a mocked response."
    mock_gemini_client.models.generate_content.return_value = mock_response

    response = client.post("/api/ai/generate", json={"prompt": "Explain SQLite"})

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "This is a mocked response."
    assert data["model"].endswith(settings.GEMINI_MODEL)
    assert data["status"] == "success"


def test_ai_generate_provider_error(mock_configured_settings, mock_gemini_client):

    # Simulate a provider API error using generic Exception as fallback handler
    mock_gemini_client.models.generate_content.side_effect = Exception(
        "Rate limit exceeded"
    )

    response = client.post("/api/ai/generate", json={"prompt": "test prompt"})

    assert response.status_code == 502
    assert "AI provider error" in response.json()["detail"]
