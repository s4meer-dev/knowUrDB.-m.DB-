from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_phase6_query_metadata_and_intelligence():
    response = client.post(
        "/api/query",
        json={"question": "How many students have GPA above 3.5?", "source_ids": ["demo-source-id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["execution_time_ms"] >= 0
    assert data["row_count"] == 1
    assert data["answer"] is not None
    assert data["answer"]["headline"] is not None
    assert isinstance(data["follow_up_suggestions"], list)
    assert len(data["follow_up_suggestions"]) > 0
