import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_query_metadata_success(client):
    response = client.post(
        "/api/query", json={"question": "how many students are there", "source_id": "demo-source-id"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "row_count" in data
    assert data["row_count"] >= 0
    assert "execution_time_ms" in data
    assert data["execution_time_ms"] >= 0
    assert data["query_source"] in ["ai", "fallback", "nlp_lite"]

    # Check explanations and suggestions exist (may be None or [])
    assert "explanation" in data
    assert "follow_up_suggestions" in data


def test_query_zero_rows_success(client, monkeypatch):
    from app.services.text_to_sql_service import TextToSQLService

    # Mock translator to return a valid SQL that yields 0 rows
    def mock_translate(*args, **kwargs):
        return "SELECT * FROM students WHERE first_name = 'asdfghjklqwerty';"

    monkeypatch.setattr(TextToSQLService, "translate", mock_translate)

    # Ask a question that will return 0 rows
    response = client.post(
        "/api/query", json={"question": "list students named asdfghjklqwerty", "source_id": "demo-source-id"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should be success, not error
    assert data["status"] == "success"
    assert data["row_count"] == 0
    assert data["error"] is not None  # We set a friendly message here


def test_query_unsupported_error(client):
    response = client.post(
        "/api/query", json={"question": "what is the meaning of life?"}
    )
    assert response.status_code == 200  # the endpoint returns 200 with status="error"
    data = response.json()

    assert data["status"] == "error"
    assert data["error"] is not None
    assert (
        "couldn't find data" in data["error"].lower()
        or "unavailable" in data["error"].lower()
        or "designed to answer questions using the connected database"
        in data["error"].lower()
    )


def test_query_empty_question(client):
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400
