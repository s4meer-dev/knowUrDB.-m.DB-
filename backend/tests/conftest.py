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

    # Globally mock query_router to default to SINGLE_SOURCE so tests pass
    from unittest.mock import patch
    patcher = patch(
        "app.api.query.query_router.route_query",
        return_value={
            "decision": "SINGLE_SOURCE",
            "sources": [{"source_id": "demo-source-id", "type": "sqlite3"}],
            "candidates": [],
            "confidence": 1.0
        }
    )
    patcher.start()
    
    yield
    
    patcher.stop()
