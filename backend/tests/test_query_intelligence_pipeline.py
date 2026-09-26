import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.post("/api/demo/generate")
        yield c


def test_dataset_overview(client: TestClient):
    for q in [
        "give me info about dataset",
        "tell me about this dataset",
        "what collections are available?",
        "what data do I have?",
        "how many collections are there?",
    ]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] in ("DATASET_OVERVIEW", "COLLECTION_OVERVIEW", "META_COUNT_COLLECTIONS")
        assert data["presentation"]["type"] in ("dataset_overview", "kpi")
        assert data["row_count"] == 5
        assert "collections" in data["answer"]["summary"].lower()


def test_ambiguous_questions_never_guess_products(client: TestClient):
    """
    Regression test for Section 8, 28, 80, 106:
    When no collection is specified and no conversation context exists,
    'how many data are there', 'show me the records', 'give me information', 'show me data'
    MUST return clarification_required and MUST NEVER silently resolve to 'products'.
    """
    for q in [
        "how many data are there",
        "how many data are there?",
        "how many records are there?",
        "show me the records",
        "give me information",
        "show me data",
    ]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "clarification_required", f"Expected clarification for '{q}', got {data}"
        assert data["intent"] == "CLARIFICATION"
        assert data["collection"] is None
        cand_cols = {c["collection"] for c in data["candidates"]}
        assert {"customers", "products", "orders", "employees", "students"}.issubset(cand_cols)
        # Ensure each candidate card includes document_count and fields_preview
        for c in data["candidates"]:
            assert c.get("document_count", 0) > 0
            assert isinstance(c.get("fields_preview"), list)


def test_collection_count_explicit_and_selected(client: TestClient):
    # Explicit collection mention in question
    for q in [
        "how many products are there?",
        "count products",
        "number of products?",
        "total products?",
    ]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] == "COUNT"
        assert data["collection"] == "products"
        assert data["presentation"]["type"] == "kpi"
        assert data["answer"]["value"] == "12"

    # Ambiguous question after user selects a collection from Clarification UI
    resp_sel = client.post(
        "/api/query",
        json={"question": "how many data are there", "active_collection": "customers"},
    )
    assert resp_sel.status_code == 200
    data_sel = resp_sel.json()
    assert data_sel["status"] == "success"
    assert data_sel["intent"] == "COUNT"
    assert data_sel["collection"] == "customers"
    assert data_sel["answer"]["value"] == "50"


def test_list_products(client: TestClient):
    for q in [
        "show me data related to product",
        "show me products",
        "list products",
        "give me product data",
    ]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] == "LIST_RECORDS"
        assert data["collection"] == "products"
        assert data["presentation"]["type"] == "table"
        assert data["row_count"] == 12
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


def test_multi_collection_query(client: TestClient):
    resp = client.post(
        "/api/query", json={"question": "which customers placed the most orders?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "MULTI_COLLECTION"
    assert data["row_count"] > 0
    assert "orders_placed" in data["columns"]
    assert "customer_name" in data["columns"]


def test_non_existent_collection_detection(client: TestClient):
    resp = client.post("/api/query", json={"question": "show teachers"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "clarification_required"
    assert "teachers" in (data["error"] or "").lower()
    assert len(data["candidates"]) == 5


def test_conversational_followup_and_correction(client: TestClient):
    # Step 1: User asks "show products"
    r1 = client.post("/api/query", json={"question": "show products"}).json()
    assert r1["collection"] == "products"
    assert r1["intent"] == "LIST_RECORDS"

    # Step 2: User asks follow-up "how many?" with conversation context
    r2 = client.post(
        "/api/query",
        json={
            "question": "how many?",
            "conversation_context": {
                "collection": "products",
                "last_question": "show products",
                "intent": "LIST_RECORDS",
            },
        },
    ).json()
    assert r2["status"] == "success"
    assert r2["intent"] == "COUNT"
    assert r2["collection"] == "products"
    assert r2["answer"]["value"] == "12"

    # Step 3: User corrects "actually customers"
    r3 = client.post(
        "/api/query",
        json={
            "question": "actually customers",
            "conversation_context": {
                "collection": "products",
                "last_question": "show products",
                "intent": "LIST_RECORDS",
            },
        },
    ).json()
    assert r3["status"] == "success"
    assert r3["collection"] == "customers"
    assert r3["row_count"] == 50


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
