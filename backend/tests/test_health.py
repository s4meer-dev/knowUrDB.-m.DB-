from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_success():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "knowUrDB-backend"
    assert "version" in data

def test_invalid_route():
    response = client.get("/api/invalid")
    assert response.status_code == 404
