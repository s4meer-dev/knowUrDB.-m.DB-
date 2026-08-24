import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_get_suggestions(client):
    response = client.get("/api/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)

    # Should have some suggestions generated from demo db
    assert len(data["suggestions"]) > 0

    # Verify no duplicate suggestions
    assert len(data["suggestions"]) == len(set(data["suggestions"]))
