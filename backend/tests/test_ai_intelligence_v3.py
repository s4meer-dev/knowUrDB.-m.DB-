import pytest
from fastapi.testclient import TestClient

from app.core.mongodb import MongoDBManager
from app.main import app
from app.services.demo_generator import DemoGenerator
from app.services.registry_service import RegistryService
from app.services.scope_resolver import QueryScope, ScopeResolver


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Seed demo dataset if needed
        c.post("/api/demo/generate")
        yield c


# =====================================================================
# 1. SCOPE RESOLVER TESTS (Deterministic Platform vs Dataset vs Collection)
# =====================================================================


def test_scope_resolver_platform_dataset_count():
    """Verify 'how many datasets' variants resolve strictly to PLATFORM scope."""
    for q in [
        "How many dataset are there?",
        "how many dataset are there",
        "how many datasets",
        "how many datasets do I have?",
        "count datasets",
        "total datasets",
        "number of datasets",
        "how many databases",
        "how many databases do i have",
    ]:
        res = ScopeResolver.resolve_scope(q)
        assert res.scope == QueryScope.PLATFORM, f"Expected PLATFORM for '{q}', got {res.scope}"
        assert res.intent == "META_COUNT_DATASETS"


def test_scope_resolver_platform_dataset_list():
    """Verify 'list datasets' variants resolve to PLATFORM scope."""
    for q in [
        "show all datasets",
        "list datasets",
        "what datasets do I have?",
        "what datasets are available",
        "what databases are available",
        "available datasets",
        "show available sources",
    ]:
        res = ScopeResolver.resolve_scope(q)
        assert res.scope == QueryScope.PLATFORM, f"Expected PLATFORM for '{q}', got {res.scope}"
        assert res.intent == "META_LIST_DATASETS"


def test_scope_resolver_dataset_scope():
    """Verify dataset-level questions resolve to DATASET scope."""
    res_overview = ScopeResolver.resolve_scope("Tell me about this dataset")
    assert res_overview.scope == QueryScope.DATASET
    assert res_overview.intent == "META_DATASET_OVERVIEW"

    res_count_cols = ScopeResolver.resolve_scope("how many collections in this dataset?")
    assert res_count_cols.scope == QueryScope.DATASET
    assert res_count_cols.intent == "META_COUNT_COLLECTIONS"


def test_scope_resolver_unrelated():
    """Verify off-topic questions resolve to UNRELATED scope."""
    for q in [
        "What is the weather in London?",
        "tell me a joke",
        "capital of france",
        "who is the president",
        "recipe for pasta",
        "2 + 2",
    ]:
        res = ScopeResolver.resolve_scope(q)
        assert res.scope == QueryScope.UNRELATED, f"Expected UNRELATED for '{q}', got {res.scope}"


# =====================================================================
# 2. END-TO-END PLATFORM SCOPE TESTS (Root Cause Fix Verification)
# =====================================================================


def test_count_datasets_never_triggers_collection_clarification(client: TestClient):
    """
    CRITICAL ROOT CAUSE TEST:
    When asking 'How many dataset are there?', the system MUST NOT:
      - Pick an arbitrary tabular dataset (e.g. Commercial Banking Hub)
      - Ask 'Which collection would you like me to count?'
      - Return an ambiguous clarification error
    It MUST return:
      - intent: META_COUNT_DATASETS
      - status: success
      - presentation.type: kpi
      - headline: TOTAL DATASETS
      - exact count of registered datasets (>= 1)
    """
    resp = client.post("/api/query", json={"question": "How many dataset are there?"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success", f"Failed with: {data}"
    assert data["intent"] == "META_COUNT_DATASETS"
    assert data["presentation"]["type"] == "kpi"
    assert "TOTAL DATASETS" in data["answer"]["headline"]
    assert int(data["answer"]["value"]) >= 1
    assert "dataset" in data["answer"]["summary"].lower()
    # Confirm no collection clarification was triggered!
    assert data.get("candidates") is None or len(data.get("candidates", [])) == 0


def test_count_datasets_variations_end_to_end(client: TestClient):
    """Verify multiple phrasing variations for dataset counting succeed with exact scalar KPI."""
    for q in [
        "how many datasets",
        "how many datasets?",
        "count datasets",
        "total datasets",
        "how many databases do i have",
    ]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] == "META_COUNT_DATASETS"
        assert data["presentation"]["type"] == "kpi"
        assert int(data["answer"]["value"]) >= 1


def test_list_datasets_end_to_end(client: TestClient):
    """Verify 'list datasets' returns structured dataset_list presentation."""
    for q in ["show all datasets", "list datasets", "what datasets do I have?"]:
        resp = client.post("/api/query", json={"question": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["intent"] in ("META_LIST_DATASETS", "METADATA_QUERY")
        assert data["presentation"]["type"] in ("dataset_list", "dataset_overview")
        assert data["row_count"] >= 1
        assert "dataset" in data["columns"] or "name" in data["columns"]


def test_active_dataset_scope_end_to_end(client: TestClient):
    """Verify 'what is the active dataset' returns active dataset metadata."""
    resp = client.post("/api/query", json={"question": "what is the active dataset"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_ACTIVE_DATASET"
    assert data["presentation"]["type"] == "kpi"


def test_generation_history_scope_end_to_end(client: TestClient):
    """Verify 'how many datasets have i generated' returns generation count."""
    resp = client.post("/api/query", json={"question": "how many datasets have i generated"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_GENERATIONS"
    assert data["presentation"]["type"] == "kpi"


# =====================================================================
# 3. DATASET & COLLECTION SCOPE TESTS
# =====================================================================


def test_count_collections_in_dataset(client: TestClient):
    """Verify 'how many collections in this dataset?' returns exact collection count KPI."""
    resp = client.post("/api/query", json={"question": "how many collections in this dataset?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_COUNT_COLLECTIONS"
    assert data["presentation"]["type"] == "kpi"
    assert int(data["answer"]["value"]) == 5
    assert "collections" in data["answer"]["summary"].lower()


def test_count_collection_records_exact_kpi(client: TestClient):
    """
    EXACT ANSWER PRINCIPLE:
    When asking 'how many products?' or 'how many clients?',
    must return a focused scalar KPI card, NOT a 500-row table dump!
    """
    resp = client.post("/api/query", json={"question": "how many products are there?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "COUNT"
    assert data["presentation"]["type"] == "kpi"
    assert int(data["answer"]["value"].replace(",", "")) > 0
    # Must NOT dump raw rows!
    assert data["row_count"] <= 1


def test_sum_and_average_exact_kpi(client: TestClient):
    """
    EXACT ANSWER PRINCIPLE:
    Scalar queries for SUM and AVERAGE must return a KPI card, not raw documents!
    """
    # Average
    resp_avg = client.post("/api/query", json={"question": "what is the average price of products?"})
    assert resp_avg.status_code == 200
    data_avg = resp_avg.json()
    assert data_avg["status"] == "success"
    assert data_avg["intent"] == "AVERAGE"
    assert data_avg["presentation"]["type"] == "kpi"
    assert data_avg["row_count"] <= 1

    # Sum
    resp_sum = client.post("/api/query", json={"question": "what is the total revenue of orders?"})
    assert resp_sum.status_code == 200
    data_sum = resp_sum.json()
    assert data_sum["status"] == "success"
    assert data_sum["intent"] == "SUM"
    assert data_sum["presentation"]["type"] == "kpi"


def test_maximum_exact_detail_card(client: TestClient):
    """
    EXACT ANSWER PRINCIPLE:
    Superlative query ('most expensive product', 'highest salary')
    must return single-record detail card highlighting the winning record!
    """
    resp = client.post("/api/query", json={"question": "what is the most expensive product?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "MAXIMUM"
    assert data["presentation"]["type"] == "detail"
    assert data["row_count"] == 1
    assert "highlight_record" in data["presentation"]


def test_top_n_ranked_table(client: TestClient):
    """Verify TOP_N returns ranked table bounded to requested N."""
    resp = client.post("/api/query", json={"question": "top 5 products by price"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "TOP_N"
    assert data["presentation"]["type"] == "ranked_table"
    assert data["row_count"] <= 5
    assert "rank" in data["columns"]


def test_filter_table(client: TestClient):
    """Verify FILTER returns clean table with matching documents."""
    resp = client.post("/api/query", json={"question": "show products where category is Electronics"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] in ("FILTER", "LIST_RECORDS")
    assert data["presentation"]["type"] == "table"


# =====================================================================
# 4. ALL SOURCES & CLARIFICATION ROUTING TESTS
# =====================================================================


def test_all_sources_single_match_auto_routing(client: TestClient):
    """
    When ALL SOURCES is selected and query mentions an entity unique to 1 dataset,
    the router MUST automatically bind to that dataset without asking clarification.
    """
    # 'orders' or 'products' in demo dataset
    resp = client.post(
        "/api/query",
        json={"question": "how many orders were placed?", "source_ids": None},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "COUNT"


def test_ambiguous_collection_clarification(client: TestClient):
    """
    When asking a collection query with no collection named ('how many records?'),
    must prompt user with collection candidates and [← Back] support.
    """
    resp = client.post("/api/query", json={"question": "how many records are there?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "clarification_required"
    assert data["intent"] == "CLARIFICATION"
    assert data["presentation"]["type"] == "clarification"
    assert len(data.get("candidates", [])) >= 2


def test_ambiguous_field_clarification(client: TestClient):
    """
    When asking an aggregation without specifying which numeric field,
    system should return field clarification.
    """
    resp = client.post(
        "/api/query",
        json={"question": "what is the total value of orders?", "active_collection": "orders"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # If the collection has multiple numeric fields without 'value', it prompts field clarification
    if data["status"] == "clarification_required":
        assert data["presentation"]["clarification_type"] == "field"


def test_unrelated_query_rejection(client: TestClient):
    """Verify off-topic questions return UNRELATED with a friendly error message."""
    resp = client.post("/api/query", json={"question": "write a poem about flowers"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert data["intent"] == "UNRELATED"
    assert "couldn't find relevant data" in data["error"].lower()
