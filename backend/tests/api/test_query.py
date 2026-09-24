from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_query_count_students():
    response = client.post(
        "/api/query",
        json={"question": "How many students are in the database?", "source_ids": ["demo-source-id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "db.students.aggregate" in data["generated_mongo_query"]
    assert len(data["rows"]) == 1
    assert data["rows"][0]["total_students"] == 100


def test_query_top_products_by_revenue():
    response = client.post(
        "/api/query",
        json={"question": "What are the top 10 products by revenue?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "db.products.aggregate" in data["generated_mongo_query"]
    assert len(data["rows"]) == 10
    assert "revenue" in data["columns"]


def test_query_customers_spent_over_one_lakh():
    response = client.post(
        "/api/query",
        json={"question": "Which customers have spent more than ₹1 lakh?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["rows"]) > 0
    for row in data["rows"]:
        assert row["total_spent"] > 100000


def test_query_compare_sales_january_february():
    response = client.post(
        "/api/query",
        json={"question": "Compare sales between January and February."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["rows"]) == 2
    months = {r["month"] for r in data["rows"]}
    assert months == {"January", "February"}


def test_query_average_salary_by_department():
    response = client.post(
        "/api/query",
        json={"question": "Average salary by department"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "department" in data["columns"]
    assert "average_salary" in data["columns"]
    assert len(data["rows"]) == 6


def test_invalid_empty_question():
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400


def test_unsupported_unrelated_question():
    response = client.post("/api/query", json={"question": "Tell me a joke."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "UNRELATED_QUERY"


def test_unsafe_drop_collection_rejected():
    response = client.post(
        "/api/query",
        json={"question": "Drop the products collection", "source_ids": ["demo-source-id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "UNSAFE_SQL"
    assert "safety requirements" in data["error"]


def test_unsafe_delete_records_rejected():
    response = client.post(
        "/api/query",
        json={"question": "Delete all students from the collection", "source_ids": ["demo-source-id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "UNSAFE_SQL"
