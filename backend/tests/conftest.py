import os

import pytest

from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    # Disable real AI calls by default for all tests
    settings.GEMINI_API_KEY = ""
    os.environ["GEMINI_API_KEY"] = ""

    # Also disable the globally instantiated ai_service in query.py
    # since it was instantiated at import time before this fixture ran.
    from app.api.query import ai_service

    ai_service.provider.api_key = ""
    ai_service.provider.client = None

    yield
