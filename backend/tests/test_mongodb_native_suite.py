import io
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.mongodb import MongoDBManager
from app.main import app
from app.services.mongo_validator import MongoQuerySafetyError, MongoQueryValidator

client = TestClient(app)


def test_01_mongodb_connection_and_ping():
    status = MongoDBManager.ping()
    assert status["connected"] is True
    assert status["engine"] in ("mongodb", "mongomock")


def test_02_csv_ingestion_with_nested_document_modeling():
    csv_data = (
        b"customer_id,name,contact_email,contact_phone,address_city,address_state,total_spent\n"
        b"C101,Rohan Mehta,rohan@example.com,9876543210,Bengaluru,Karnataka,185000\n"
        b"C102,Ananya Iyer,ananya@example.com,9876543211,Chennai,Tamil Nadu,92000\n"
    )
    res = client.post(
        "/api/sources/upload",
        files={"file": ("enterprise_customers.csv", csv_data, "text/csv")},
    )
    assert res.status_code == 200
    src = res.json()
    col_name = src["collections"][0]

    # Verify nested subdocuments (`contact` and `address`) were modeled inside MongoDB
    doc = MongoDBManager.get_db()[col_name].find_one({"customer_id": "C101"})
    assert doc is not None
    assert doc["contact"]["email"] == "rohan@example.com"
    assert doc["address"]["city"] == "Bengaluru"
    client.delete(f"/api/sources/{src['source_id']}")


def test_03_json_ingestion():
    json_payload = json.dumps(
        [
            {"sku": "SKU-1", "title": "Router X", "price": 12500, "tags": ["networking", "wifi6"]},
            {"sku": "SKU-2", "title": "Switch Pro", "price": 24000, "tags": ["networking", "10gbe"]},
        ]
    ).encode("utf-8")
    res = client.post(
        "/api/sources/upload",
        files={"file": ("hardware_catalog.json", json_payload, "application/json")},
    )
    assert res.status_code == 200
    src = res.json()
    assert src["record_count"] == 2
    client.delete(f"/api/sources/{src['source_id']}")


def test_04_excel_ingestion():
    df = pd.DataFrame(
        [{"region": "North", "q1_sales": 450000}, {"region": "South", "q1_sales": 610000}]
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    res = client.post(
        "/api/sources/upload",
        files={
            "file": (
                "regional_sales.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert res.status_code == 200
    src = res.json()
    assert src["record_count"] == 2
    client.delete(f"/api/sources/{src['source_id']}")


def test_05_parquet_ingestion():
    df = pd.DataFrame(
        [{"sensor_id": "S1", "temperature": 24.5}, {"sensor_id": "S2", "temperature": 28.1}]
    )
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)
    res = client.post(
        "/api/sources/upload",
        files={"file": ("telemetry.parquet", buf.getvalue(), "application/octet-stream")},
    )
    assert res.status_code == 200
    src = res.json()
    assert src["record_count"] == 2
    client.delete(f"/api/sources/{src['source_id']}")


def test_06_pdf_and_markdown_rag_ingestion_and_retrieval():
    md_content = (
        b"# Refund & Return Policy\n\n"
        b"Customers are eligible for a full 100% refund within 30 calendar days of purchase "
        b"if the hardware seal is unbroken or if a manufacturing defect is verified by support.\n\n"
        b"# Enterprise SLA\n\n"
        b"Enterprise tier customers receive 99.99% uptime guarantee and 15-minute response times."
    )
    res = client.post(
        "/api/sources/upload",
        files={"file": ("refund_policy.md", md_content, "text/markdown")},
    )
    assert res.status_code == 200
    src = res.json()

    # Query via natural language router -> DOCUMENT_RAG
    q_res = client.post(
        "/api/query",
        json={"question": "Which document contains information about the refund policy?"},
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["status"] == "success"
    assert q_data["query_source"] == "rag"
    assert "30 calendar days" in q_data["answer"]["summary"]
    client.delete(f"/api/sources/{src['source_id']}")


def test_07_clarification_flow_for_ambiguous_sources():
    s2024 = b"order_id,sales\n1,50000\n2,75000"
    s2025 = b"order_id,sales\n3,90000\n4,110000"
    r1 = client.post("/api/sources/upload", files={"file": ("sales_2024.csv", s2024, "text/csv")}).json()
    r2 = client.post("/api/sources/upload", files={"file": ("sales_2025.csv", s2025, "text/csv")}).json()

    try:
        q_res = client.post("/api/query", json={"question": "What are the total sales?"}).json()
        assert q_res["status"] == "clarification_required"
        candidate_names = {c["name"] for c in q_res["candidates"]}
        assert "sales_2024.csv" in candidate_names
        assert "sales_2025.csv" in candidate_names
    finally:
        client.delete(f"/api/sources/{r1['source_id']}")
        client.delete(f"/api/sources/{r2['source_id']}")


def test_08_multi_source_comparison_flow():
    s2024 = b"order_id,sales\n1,50000"
    s2025 = b"order_id,sales\n2,90000"
    r1 = client.post("/api/sources/upload", files={"file": ("sales_2024.csv", s2024, "text/csv")}).json()
    r2 = client.post("/api/sources/upload", files={"file": ("sales_2025.csv", s2025, "text/csv")}).json()

    try:
        q_res = client.post(
            "/api/query", json={"question": "Compare sales from 2024 and 2025 datasets."}
        ).json()
        assert q_res["status"] == "success"
        assert q_res["query_source"] == "multi_source"
        assert len(q_res["rows"]) >= 2
    finally:
        client.delete(f"/api/sources/{r1['source_id']}")
        client.delete(f"/api/sources/{r2['source_id']}")


@pytest.mark.parametrize(
    "malicious_payload",
    [
        {"collection": "products", "operation": "insert", "document": {"name": "hack"}},
        {"collection": "products", "operation": "updateMany", "filter": {}, "update": {"$set": {"price": 0}}},
        {"collection": "products", "operation": "deleteMany", "filter": {}},
        {"collection": "products", "operation": "drop"},
        {"collection": "products", "operation": "aggregate", "pipeline": [{"$out": "pwned_collection"}]},
        {"collection": "products", "operation": "aggregate", "pipeline": [{"$merge": {"into": "users"}}]},
        {"collection": "products", "operation": "find", "filter": {"$where": "function() { return true; }"}},
        {"collection": "_sys_sources", "operation": "find", "filter": {}},
        {"collection": "products", "operation": "aggregate", "pipeline": [{"$match": {}}] * 20},
        {"collection": "products", "operation": "find", "limit": 9999999},
    ],
)
def test_09_comprehensive_mongodb_security_validator(malicious_payload):
    with pytest.raises(MongoQuerySafetyError):
        MongoQueryValidator.validate(malicious_payload)

    res = client.post("/api/query/validate", json={"query": malicious_payload})
    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "UNSAFE_QUERY"
