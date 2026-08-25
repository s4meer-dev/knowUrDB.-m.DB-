import pytest
from fastapi.testclient import TestClient

from app.core.app_database import app_db_provider
from app.main import app

app_db_provider.init_db()


# Provide a client fixture that uses the lifespan context
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_query_history_workflow(client):
    # 1. Clear history first
    response = client.delete("/api/history")
    assert response.status_code == 200

    # 2. Verify empty history
    response = client.get("/api/history")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # 3. Create a query
    from unittest.mock import patch

    with (
        patch(
            "app.api.query.ai_service.get_status",
            return_value={"configured": True, "status": "ready"},
        ),
        patch(
            "app.api.query.ai_service.generate",
            return_value={"response": "```sql\nSELECT COUNT(*) FROM students;\n```"},
        ),
        patch(
            "app.services.query_intelligence_service.AIService.generate",
            return_value={"response": "VALID"},
        ),
    ):
        response = client.post(
            "/api/query", json={"question": "how many students are there?"}
        )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 4. Verify history has 1 entry
    response = client.get("/api/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1

    item = history[0]
    assert item["question"] == "how many students are there?"
    assert item["query_source"] in ["ai", "fallback"]
    assert item["status"] == "success"
    assert item["row_count"] is not None
    assert item["execution_time_ms"] is not None
    assert "id" in item

    # 5. Get specific item
    query_id = item["id"]
    response = client.get(f"/api/history/{query_id}")
    assert response.status_code == 200
    assert response.json()["id"] == query_id

    # 6. Delete specific item
    response = client.delete(f"/api/history/{query_id}")
    assert response.status_code == 200

    # 7. Verify deletion
    response = client.get(f"/api/history/{query_id}")
    assert response.status_code == 404


def test_history_not_found(client):
    response = client.get("/api/history/nonexistent_id")
    assert response.status_code == 404

    response = client.delete("/api/history/nonexistent_id")
    assert response.status_code == 404
