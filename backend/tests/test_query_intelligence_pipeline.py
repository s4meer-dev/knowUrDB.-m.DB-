import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Ensure demo dataset is generated
        c.post("/api/demo/generate")
        yield c


def test_dataset_overview(client: TestClient):
    for q in ["give me info about dataset", "what collections are available?", "tell me about this database"]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] in ("DATASET_OVERVIEW", "COLLECTION_OVERVIEW")
        assert data["presentation"]["type"] == "dataset_overview"
        assert data["row_count"] == 5
        assert "collections" in data["answer"]["summary"].lower()


def test_collection_count(client: TestClient):
    for q in [
        "how many data are there in the collection",
        "how many products are there?",
        "count products",
        "number of products?",
        "total products?",
    ]:
        resp = client.post("/api/query", json={"question": q, "active_collection": "products"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] == "COUNT"
        assert data["presentation"]["type"] == "kpi"
        assert data["answer"]["value"] == "12"
        assert "12" in data["answer"]["summary"]


def test_list_products(client: TestClient):
    for q in ["show me data related to product", "show me products", "list products", "give me product data"]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] == "LIST_RECORDS"
        assert data["presentation"]["type"] == "table"
        assert data["row_count"] == 12
        # Must NEVER invent 'TOP RESULT BY PRICE' for a list query
        assert "TOP RESULT" not in (data["answer"]["headline"] or "").upper()
        assert "leads with" not in (data["answer"]["summary"] or "")


def test_filter_products(client: TestClient):
    resp = client.post("/api/query", json={"question": "show me products above 50000"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "FILTER"
    assert data["presentation"]["type"] == "table"
    assert 0 < data["row_count"] < 12
    for row in data["rows"]:
        assert row["price"] > 50000


def test_top_products(client: TestClient):
    resp = client.post("/api/query", json={"question": "give me the top 5 products by price"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "TOP_N"
    assert data["presentation"]["type"] == "ranked_table"
    assert data["row_count"] == 5
    assert "rank" in data["columns"]
    assert data["rows"][0]["rank"] == 1
    assert data["rows"][0]["price"] >= data["rows"][1]["price"]


def test_average_price(client: TestClient):
    resp = client.post("/api/query", json={"question": "what is the average product price?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "AVERAGE"
    assert data["presentation"]["type"] == "kpi"
    assert "₹" in data["answer"]["value"]
    assert data["answer"]["value"] != "₹12"


def test_max_price(client: TestClient):
    resp = client.post("/api/query", json={"question": "what is the most expensive product?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "MAXIMUM"
    assert data["presentation"]["type"] == "detail"
    assert data["row_count"] == 1
    assert "1,45,000" in data["answer"]["value"]
    assert "PROD-002" in data["answer"]["summary"]


def test_collection_resolution(client: TestClient):
    cases = [
        ("show me prodcut", "products"),
        ("tell me about the customers", "customers"),
        ("how many orders are there?", "orders"),
        ("show customers from Bangalore", "customers"),
    ]
    for q, expected_col in cases:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["collection"] == expected_col


def test_active_source_resolution(client: TestClient):
    resp = client.post(
        "/api/query",
        json={"question": "how many records are there?", "active_collection": "employees"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["collection"] == "employees"
    assert data["answer"]["value"] == "60"


def test_semantic_field_resolution(client: TestClient):
    resp = client.post("/api/query", json={"question": "show products with low stock"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["collection"] == "products"
    assert data["intent"] == "FILTER"
    for row in data["rows"]:
        assert row["stock"] < 25


def test_unrelated_detection(client: TestClient):
    resp = client.post("/api/query", json={"question": "what is the weather in Tokyo today?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert data["error_code"] == "UNRELATED_QUERY"


def test_clarification(client: TestClient):
    # Ambiguous query without active_collection or recognizable collection/field token
    resp = client.post("/api/query", json={"question": "filter above 10"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("clarification_required", "success")


def test_result_presentation_type(client: TestClient):
    mapping = [
        ("show me products", "table"),
        ("how many products are there?", "kpi"),
        ("give me info about dataset", "dataset_overview"),
        ("what is the most expensive product?", "detail"),
        ("give me the top 5 products by price", "ranked_table"),
        ("compare products by price and units sold", "comparison"),
        ("what fields are in products?", "schema"),
    ]
    for q, expected_ui in mapping:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["presentation"]["type"] == expected_ui


def test_followup_generation(client: TestClient):
    resp = client.post("/api/query", json={"question": "show me products"})
    assert resp.status_code == 200
    data = resp.json()
    follow_ups = data.get("follow_up_suggestions", [])
    assert len(follow_ups) >= 2
    assert all("product" in f.lower() for f in follow_ups)
