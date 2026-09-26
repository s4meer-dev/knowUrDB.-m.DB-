import pytest
from fastapi.testclient import TestClient

from app.core.mongodb import MongoDBManager
from app.main import app
from app.models.scope import QueryScopeModel, ScopeType
from app.services.intent_classifier import QuestionNormalizer
from app.services.registry_service import RegistryService
from app.services.result_validator import ResultValidator
from app.services.scope_resolver import QueryScope, ScopeResolver
from app.services.semantic_field_registry import (
    SemanticConcept,
    SemanticFieldRegistry,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Seed demo dataset if needed
        c.post("/api/demo/generate")
        yield c


# =====================================================================
# 1. BUG #1: NEVER AUTOSELECT ON FRESH LOAD (DEFAULT TO ALL_SOURCES)
# =====================================================================


def test_scope_model_all_sources():
    """Verify QueryScopeModel correctly identifies ALL_SOURCES."""
    scope = QueryScopeModel.all_sources()
    assert scope.is_all_sources() is True
    assert scope.scope_type == ScopeType.ALL_SOURCES
    assert scope.dataset_id is None
    assert scope.collection_name is None


def test_scope_model_dataset():
    """Verify QueryScopeModel correctly handles DATASET scope."""
    scope = QueryScopeModel.for_dataset("demo-source-id")
    assert scope.is_all_sources() is False
    assert scope.scope_type == ScopeType.DATASET
    assert scope.dataset_id == "demo-source-id"
    assert scope.collection_name is None


def test_scope_model_collection():
    """Verify QueryScopeModel correctly handles COLLECTION scope."""
    scope = QueryScopeModel.for_collection("demo-source-id", "customers")
    assert scope.is_all_sources() is False
    assert scope.scope_type == ScopeType.COLLECTION
    assert scope.dataset_id == "demo-source-id"
    assert scope.collection_name == "customers"


def test_api_fresh_load_defaults_to_all_sources(client: TestClient):
    """When no scope is passed or ALL_SOURCES is passed, querying platform count returns all datasets."""
    resp = client.post(
        "/api/query",
        json={
            "question": "How many datasets are there?",
            "scope": {"scope_type": "ALL_SOURCES"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_COUNT_DATASETS"
    assert int(data["answer"]["value"]) >= 1


# =====================================================================
# 2. BUG #2: SCOPE OVERRIDES GENERIC INTENT
# =====================================================================


def test_dataset_scope_context_on_generic_dataset_count():
    """
    When the user is viewing Dataset A and asks 'How many datasets are there?',
    the system must NOT return global platform count (e.g. 4).
    It must return a context response explaining 1 dataset is selected with its collections.
    """
    res = ScopeResolver.resolve_scope(
        "How many datasets are there?",
        active_source_id="demo-source-id",
        is_all_sources=False,
    )
    assert res.scope == QueryScope.DATASET
    assert res.intent == "META_DATASET_SCOPE_CONTEXT"


def test_dataset_scope_context_api_execution(client: TestClient):
    """Verify API endpoint returns DATASET_SCOPE_CONTEXT when scoped to a single dataset."""
    # Find an active dataset source_id
    reg = RegistryService()
    datasets = reg.list_datasets()
    assert len(datasets) > 0
    active_sid = datasets[0]["source_id"]

    resp = client.post(
        "/api/query",
        json={
            "question": "How many datasets are there?",
            "source_ids": [active_sid],
            "scope": {
                "scope_type": "DATASET",
                "dataset_id": active_sid,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_DATASET_SCOPE_CONTEXT"
    assert data["answer"]["value"] == "1"
    assert "You currently have 1 dataset selected" in data["answer"]["summary"]


def test_global_override_phrasing_returns_platform_count(client: TestClient):
    """
    When explicit global phrasing is used ('in total', 'across all sources'),
    the system correctly returns platform-level count even if a dataset was active.
    """
    for global_q in [
        "How many datasets are there in total?",
        "How many datasets across all sources?",
        "How many total datasets exist?",
        "how many datasets globally?",
        "count datasets across the entire platform",
    ]:
        res = ScopeResolver.resolve_scope(
            global_q,
            active_source_id="demo-source-id",
            is_all_sources=False,
        )
        assert res.scope == QueryScope.PLATFORM, f"Expected PLATFORM for '{global_q}', got {res.scope}"
        assert res.intent == "META_COUNT_DATASETS"


def test_collection_scope_context_on_generic_dataset_count(client: TestClient):
    """
    When the user is viewing a collection (e.g. 'orders') and asks 'How many datasets are there?',
    the system explains that a dataset-level count is not available in a single collection.
    """
    resp = client.post(
        "/api/query",
        json={
            "question": "How many datasets are there?",
            "source_ids": ["demo-source-id"],
            "active_collection": "orders",
            "scope": {
                "scope_type": "COLLECTION",
                "dataset_id": "demo-source-id",
                "collection_name": "orders",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "META_COLLECTION_SCOPE_CONTEXT"
    assert "orders" in data["answer"]["summary"]


# =====================================================================
# 3. BUG #3: NEVER SUBSTITUTE UNRELATED METRIC
# =====================================================================


def test_semantic_field_registry_concept_classification():
    """Verify SemanticFieldRegistry correctly classifies distinct metrics."""
    prof_revenue = SemanticFieldRegistry.classify_field("total_amount", "orders")
    assert prof_revenue.concept == SemanticConcept.REVENUE

    prof_spent = SemanticFieldRegistry.classify_field("total_spent", "customers")
    assert prof_spent.concept == SemanticConcept.CUSTOMER_SPENDING

    prof_gpa = SemanticFieldRegistry.classify_field("gpa", "students")
    assert prof_gpa.concept == SemanticConcept.ACADEMIC

    prof_salary = SemanticFieldRegistry.classify_field("salary", "employees")
    assert prof_salary.concept == SemanticConcept.COMPENSATION


def test_revenue_in_students_collection_rejected():
    """In 'students' collection, asking 'show total revenue' must return METRIC_UNAVAILABLE, never GPA."""
    student_columns = [
        {"name": "name", "data_type": "String"},
        {"name": "gpa", "data_type": "Double"},
        {"name": "Attendance_Percentage", "data_type": "Double"},
    ]
    match_res = SemanticFieldRegistry.match_requested_metric("REVENUE", "students", student_columns)
    assert match_res.status == "INCOMPATIBLE"
    assert "revenue is not available in the `students` collection" in match_res.explanation.lower()


def test_revenue_in_customers_collection_offers_alternative():
    """In 'customers' collection, asking 'show total revenue' must offer total_spent as an alternative, not substitute."""
    customer_columns = [
        {"name": "name", "data_type": "String"},
        {"name": "total_spent", "data_type": "Double"},
        {"name": "city", "data_type": "String"},
    ]
    match_res = SemanticFieldRegistry.match_requested_metric("REVENUE", "customers", customer_columns)
    assert match_res.status == "RELATED_ALTERNATIVE"
    assert match_res.field_name == "total_spent"
    assert "customer spending" in match_res.explanation.lower()


def test_result_validator_rejects_gpa_for_revenue():
    """ResultValidator must block any query result where GPA was used for revenue."""
    outcome = ResultValidator.validate_result(
        question="show total revenue",
        requested_concept="REVENUE",
        target_collection="students",
        target_field="gpa",
        query_result=[{"total_gpa": 3.8}],
        generated_answer_headline="TOTAL REVENUE",
    )
    assert outcome.is_valid is False
    assert outcome.rejection_code == "METRIC_SEMANTIC_MISMATCH"
    assert "cannot be safely interpreted as revenue" in outcome.user_explanation


def test_result_validator_rejects_salary_for_revenue():
    """ResultValidator must block salary being represented as business revenue."""
    outcome = ResultValidator.validate_result(
        question="show total revenue",
        requested_concept="REVENUE",
        target_collection="employees",
        target_field="salary",
        query_result=[{"total_salary": 2500000}],
        generated_answer_headline="TOTAL REVENUE",
    )
    assert outcome.is_valid is False
    assert outcome.rejection_code == "METRIC_SEMANTIC_MISMATCH"
    assert "compensation, not business revenue" in outcome.user_explanation


# =====================================================================
# 4. BUG #4: EXPLICIT SOURCE ATTRIBUTION
# =====================================================================


def test_revenue_in_orders_has_explicit_source_attribution(client: TestClient):
    """
    When total revenue is calculated on orders, the summary must explicitly state:
    'Total revenue is ₹..., calculated from orders.total_amount across ... records.'
    """
    resp = client.post(
        "/api/query",
        json={
            "question": "show total revenue",
            "active_collection": "orders",
            "scope": {
                "scope_type": "COLLECTION",
                "collection_name": "orders",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] in ("SUM", "AGGREGATION")
    summary = data["answer"]["summary"]
    assert "calculated from orders." in summary
    assert "records" in summary


# =====================================================================
# 5. TYPO NORMALIZATION AND TOLERANCE
# =====================================================================


def test_typo_normalization():
    """Verify common typos are normalized properly."""
    assert QuestionNormalizer.normalize("show total revene") == "show total revenue"
    assert QuestionNormalizer.normalize("how many datsets") == "how many datasets"
    assert QuestionNormalizer.normalize("show all custmers") == "show all customers"
    assert QuestionNormalizer.normalize("list prodcuts") == "list products"
    assert QuestionNormalizer.normalize("what colletion is this") == "what collection is this"
    assert QuestionNormalizer.normalize("customer spnding") == "customer spending"
