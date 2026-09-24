from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_schema_success():
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "collections" in data
    assert isinstance(data["tables"], list)

    collection_names = [col["name"] for col in data["tables"]]
    assert "products" in collection_names
    assert "customers" in collection_names
    assert "orders" in collection_names
    assert "employees" in collection_names
    assert "students" in collection_names
    assert not any(name.startswith("_sys_") for name in collection_names)


def test_get_schema_summary():
    response = client.get("/api/schema/summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "products" in data["summary"]
    assert "customers" in data["summary"]
    assert "students" in data["summary"]


def test_get_collection_schema_success():
    response = client.get("/api/schema/customers")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "customers"
    assert data["document_count"] == 50

    field_names = [col["name"] for col in data["columns"]]
    assert "customer_id" in field_names
    assert "name" in field_names
    assert "contact.email" in field_names
    assert "address.city" in field_names
    assert "customer_id" in data["primary_keys"]
    assert len(data["indexes"]) >= 2


def test_get_collection_schema_not_found():
    response = client.get("/api/schema/nonexistent_collection")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_collection_schema_system_collection_blocked():
    response = client.get("/api/schema/_sys_sources")
    assert response.status_code == 404
