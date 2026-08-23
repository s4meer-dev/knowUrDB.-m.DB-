from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_schema_success():
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert isinstance(data["tables"], list)

    # We should have some tables from our demo db
    table_names = [table["name"] for table in data["tables"]]
    assert "students" in table_names
    assert "departments" in table_names

    # Ensure internal tables aren't exposed
    assert not any(name.startswith("sqlite_") for name in table_names)


def test_get_schema_summary():
    response = client.get("/api/schema/summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "students" in data["summary"]
    assert "departments" in data["summary"]


def test_get_table_schema_success():
    response = client.get("/api/schema/students")
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "students"
    assert "columns" in data
    assert "primary_keys" in data
    assert "foreign_keys" in data

    column_names = [col["name"] for col in data["columns"]]
    assert "student_id" in column_names
    assert "first_name" in column_names

    # Check primary key
    assert "student_id" in data["primary_keys"]

    # Check foreign keys
    fk_tables = [fk["referenced_table"] for fk in data["foreign_keys"]]
    assert "departments" in fk_tables


def test_get_table_schema_not_found():
    response = client.get("/api/schema/nonexistent_table")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_get_table_schema_internal_table():
    # Attempting to access an internal table should fail gracefully
    response = client.get("/api/schema/sqlite_sequence")
    assert response.status_code == 404
    assert "not allowed" in response.json()["detail"]


def test_existing_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_existing_query_endpoint():
    response = client.post(
        "/api/query", json={"question": "how many students are there"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["row_count"] > 0
