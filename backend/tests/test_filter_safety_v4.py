"""
KNOWURDB - QUERY INTELLIGENCE ENGINE V4 REGRESSION SUITE
Schema-Aware, Filter-Safe, Intent-Aware, Zero Data Leakage
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_generator import DemoGenerator
from app.services.intent_classifier import QueryPlan, QueryPlannerEngine
from app.services.presentation_planner import PresentationPlanner
from app.services.result_validator import ResultValidator
from app.services.semantic_filter_extractor import SemanticFilterExtractor, StructuredFilter
from app.services.source_manager import SourceManager


def get_fooddelivery_source_id() -> str:
    sm = SourceManager()
    for s in sm.list_sources():
        if "restaurants" in (s.collections or []):
            return s.source_id
    meta = DemoGenerator().generate_new_independent_demo_dataset(preferred_domain="fooddelivery")
    return meta.source_id


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Ensure demo dataset is initialized
        c.post("/api/demo/generate")
        # Ensure food delivery dataset is available
        get_fooddelivery_source_id()
        try:
            yield c
        finally:
            try:
                sm = SourceManager()
                for s in sm.list_sources():
                    if "restaurants" in (s.collections or []) and s.source_id != "demo_database":
                        sm.delete_source(s.source_id)
            except Exception:
                pass


# =====================================================================
# 1. SEMANTIC FILTER EXTRACTOR TESTS
# =====================================================================


def test_extractor_extracts_status_equality():
    extractor = SemanticFilterExtractor()
    cases = [
        "give me details of all who's status is verified",
        "give me details of all whose status is verified",
        "show all records where status is verified",
        "show all records where status = verified",
        "find items with status = 'verified'",
        "show all verified items",
        "list verified records",
    ]
    for q in cases:
        filters = extractor.extract_filters(q)
        assert len(filters) >= 1, f"Failed to extract filter for: '{q}'"
        f = filters[0]
        assert f.raw_field == "status"
        assert f.operator == "eq"
        assert f.value.lower() == "verified"


def test_extractor_extracts_numeric_and_location():
    extractor = SemanticFilterExtractor()

    # Numeric threshold
    filters = extractor.extract_filters("show all items with price above 500")
    assert any(f.operator == "gt" and f.value == 500 for f in filters)

    # Location
    filters = extractor.extract_filters("show customers from Bangalore")
    assert any(f.raw_field == "city" and ("Bangalore" in f.value or f.value == "bangalore") for f in filters)


def test_extractor_schema_resolution_fail_closed():
    extractor = SemanticFilterExtractor()

    # Schema without status
    restaurant_columns = [
        {"name": "restaurant_id"},
        {"name": "name"},
        {"name": "city"},
        {"name": "cuisine"},
        {"name": "rating"},
    ]
    filter_req = StructuredFilter(
        raw_field="status",
        operator="eq",
        value="verified",
        source_phrase="status is verified",
    )
    col_field, mongo_expr, desc = extractor.resolve_filter_to_collection(
        filter_req, restaurant_columns
    )
    assert col_field is None
    assert mongo_expr is None
    assert desc == "status"  # Missing field returned for fail-closed detection


def test_extractor_schema_resolution_success():
    extractor = SemanticFilterExtractor()

    menu_columns = [
        {"name": "item_id"},
        {"name": "name"},
        {"name": "price"},
        {"name": "status"},
    ]
    filter_req = StructuredFilter(
        raw_field="status",
        operator="eq",
        value="verified",
        source_phrase="status is verified",
    )
    col_field, mongo_expr, desc = extractor.resolve_filter_to_collection(
        filter_req, menu_columns
    )
    assert col_field == "status"
    assert mongo_expr is not None
    assert "verified" in str(mongo_expr)


# =====================================================================
# 2. FAIL-CLOSED QUERY PLANNER INTEGRITY
# =====================================================================


def test_query_planner_returns_field_unavailable_when_field_missing():
    """
    When user asks for status = 'verified' on 'restaurants' (which has NO status field),
    QueryPlannerEngine must immediately return a FIELD_NOT_AVAILABLE plan without executing find({}).
    """
    sid = get_fooddelivery_source_id()
    from app.services.schema_service import MongoSchemaService
    qp = QueryPlannerEngine(MongoSchemaService())
    plan = qp.build_plan(
        question="give me details of all who's status is verified",
        source_id=sid,
        active_collection="restaurants",
    )

    assert plan.intent == "FIELD_NOT_AVAILABLE"
    assert plan.presentation_type == "field_unavailable"
    assert plan.missing_filter_field == "status"
    assert "restaurant_id" in plan.available_fields


def test_query_planner_preserves_filter_when_field_exists():
    """
    When user asks for status = 'verified' on 'menu_items' (which HAS status field),
    QueryPlannerEngine compiles the $match stage.
    """
    sid = get_fooddelivery_source_id()
    from app.services.schema_service import MongoSchemaService
    qp = QueryPlannerEngine(MongoSchemaService())
    plan = qp.build_plan(
        question="give me details of all who's status is verified",
        source_id=sid,
        active_collection="menu_items",
    )

    assert plan.intent != "FIELD_NOT_AVAILABLE"
    assert "status" in plan.filters
    assert len(plan.requested_filters) >= 1

    query = qp.compile_to_mongo_query(plan)
    # Must have a $match stage
    has_match = any("$match" in stage for stage in query.get("pipeline", []))
    assert has_match is True
    assert "verified" in str(query)


# =====================================================================
# 3. PRE-EXECUTION & POST-EXECUTION FILTER VALIDATION
# =====================================================================


def test_pre_execution_guard_blocks_unfiltered_query_when_filters_requested():
    """
    ResultValidator.validate_pre_execution_filter must reject if a query
    is compiled without a $match stage when the plan requested filters.
    """
    plan = QueryPlan(
        intent="FILTER",
        collection="menu_items",
        filters={"status": {"$regex": "^verified$", "$options": "i"}},
        requested_filters=[
            {"field": "status", "operator": "eq", "value": "verified", "description": "status = 'verified'"}
        ],
    )

    bad_structured_query = {"pipeline": [{"$limit": 50}]}
    outcome = ResultValidator.validate_pre_execution_filter(plan, bad_structured_query)
    assert outcome.is_valid is False
    assert outcome.rejection_code == "FILTER_PRESERVATION_VIOLATION"

    good_structured_query = {
        "pipeline": [
            {"$match": {"status": {"$regex": "^verified$", "$options": "i"}}},
            {"$limit": 50},
        ]
    }
    good_outcome = ResultValidator.validate_pre_execution_filter(plan, good_structured_query)
    assert good_outcome.is_valid is True


def test_post_execution_guard_blocks_leaked_unfiltered_data():
    """
    ResultValidator.validate_post_execution_filter must reject any rows that do not
    satisfy the requested filter criteria.
    """
    plan = QueryPlan(
        intent="FILTER",
        collection="menu_items",
        filters={"status": {"$regex": "^verified$", "$options": "i"}},
        requested_filters=[
            {"field": "status", "operator": "eq", "value": "verified", "description": "status = 'verified'"}
        ],
    )

    dirty_rows = [
        {"name": "Burger", "status": "verified"},
        {"name": "Pizza", "status": "pending"},
    ]
    bad_outcome = ResultValidator.validate_post_execution_filter(plan, dirty_rows)
    assert bad_outcome.is_valid is False
    assert bad_outcome.rejection_code == "RESULT_FILTER_INTEGRITY_ERROR"

    clean_rows = [{"name": "Burger", "status": "verified"}]
    good_outcome = ResultValidator.validate_post_execution_filter(plan, clean_rows)
    assert good_outcome.is_valid is True


# =====================================================================
# 4. END-TO-END API SUITE FOR USER SCENARIO
# =====================================================================


def test_e2e_verified_filter_on_restaurants_returns_field_unavailable(client: TestClient):
    """
    SCENARIO C: User asks 'give me details of all who's status is verified' on 'restaurants'.
    Must return FIELD_NOT_AVAILABLE with 0 rows, available fields list, and candidate collections.
    MUST NOT return 50 unfiltered restaurants!
    """
    sid = get_fooddelivery_source_id()
    resp = client.post(
        "/api/query",
        json={
            "question": "give me details of all who's status is verified",
            "source_ids": [sid],
            "active_collection": "restaurants",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": sid,
                "collection_name": "restaurants",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "clarification_required"
    assert data["error_code"] == "FIELD_NOT_AVAILABLE"
    assert data["row_count"] == 0
    assert len(data["rows"]) == 0
    assert data["presentation"]["type"] == "field_unavailable"
    assert data["presentation"]["missing_field"] == "status"
    assert "available_fields" in data["presentation"]
    assert len(data["presentation"]["available_fields"]) > 0

    # Ensure other collections that have status (e.g. menu_items, ratings) are suggested
    cand_names = [c["name"].lower() for c in data.get("candidates", [])]
    assert "menu_items" in cand_names or "ratings" in cand_names


def test_e2e_verified_filter_on_menu_items_returns_only_matching(client: TestClient):
    """
    SCENARIO A: User asks 'give me details of all who's status is verified' on 'menu_items'.
    Must return only documents with status == 'verified' (32 matching records).
    Zero non-verified records may be returned.
    """
    sid = get_fooddelivery_source_id()
    resp = client.post(
        "/api/query",
        json={
            "question": "give me details of all who's status is verified",
            "source_ids": [sid],
            "active_collection": "menu_items",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": sid,
                "collection_name": "menu_items",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["row_count"] > 0
    assert len(data["rows"]) == data["row_count"]

    # Verify zero data leakage: every single returned row MUST have status == 'verified'
    for r in data["rows"]:
        assert str(r.get("status", "")).lower() == "verified", f"Data leakage found: {r}"


def test_e2e_verified_filter_on_ratings_returns_only_matching(client: TestClient):
    """
    SCENARIO A: User asks 'give me details of all who's status is verified' on 'ratings'.
    Must return only documents with status == 'verified' (18 matching records).
    """
    sid = get_fooddelivery_source_id()
    resp = client.post(
        "/api/query",
        json={
            "question": "give me details of all who's status is verified",
            "source_ids": [sid],
            "active_collection": "ratings",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": sid,
                "collection_name": "ratings",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["row_count"] > 0
    for r in data["rows"]:
        assert str(r.get("status", "")).lower() == "verified"


def test_e2e_nonexistent_filter_value_returns_no_matches_with_enums(client: TestClient):
    """
    SCENARIO B: User filters by a value that yields 0 matches (e.g. status is 'nonexistent_val').
    Must return NO_MATCHING_RECORDS with available distinct values.
    MUST NOT return 50 unfiltered records!
    """
    sid = get_fooddelivery_source_id()
    resp = client.post(
        "/api/query",
        json={
            "question": "show menu items where status is nonexistent_status_val",
            "source_ids": [sid],
            "active_collection": "menu_items",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": sid,
                "collection_name": "menu_items",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["intent"] == "NO_MATCHING_RECORDS"
    assert data["row_count"] == 0
    assert len(data["rows"]) == 0
    assert data["presentation"]["type"] == "no_matches"
    assert len(data["presentation"].get("available_values", [])) > 0
    assert "verified" in [str(v).lower() for v in data["presentation"]["available_values"]]


def test_e2e_count_with_filter_returns_exact_kpi(client: TestClient):
    """
    User asks 'how many verified menu items are there?'.
    Must count only where status == 'verified' (e.g. 32), returning KPI presentation.
    """
    sid = get_fooddelivery_source_id()
    resp = client.post(
        "/api/query",
        json={
            "question": "how many verified menu items are there?",
            "source_ids": [sid],
            "active_collection": "menu_items",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": sid,
                "collection_name": "menu_items",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["intent"] in ("COUNT", "AGGREGATION")
    assert data["presentation"]["type"] == "kpi"
    count_val = int(data["answer"]["value"])
    assert count_val > 0
    assert count_val < 180
