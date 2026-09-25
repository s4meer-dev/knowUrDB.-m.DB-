from fastapi.testclient import TestClient

from app.core.mongodb import MongoDBManager
from app.main import app
from app.services.demo_generator import DemoGenerator

client = TestClient(app)


def test_existing_demo_database_preserved_and_repeated_5_generations():
    # 1. Ensure initial demo_database (demo-source-id) exists
    gen = DemoGenerator()
    initial = gen.seed_initial_demo_if_empty()
    assert initial.source_id == "demo-source-id"
    assert initial.record_count == 342
    assert set(initial.collections) == {"customers", "products", "orders", "employees", "students"}

    # 2. Generate 5 independent demo databases via POST /api/sources/generate-demo
    created_sources = []
    for _ in range(5):
        resp = client.post("/api/sources/generate-demo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["source_id"] != "demo-source-id"
        assert data["source_id"].startswith("mongodb_demo_")
        assert data["database_name"].startswith("demo_")
        assert data["database_name"] != "demo_database"
        assert data["table_count"] == 5
        assert data["record_count"] > 100
        assert data.get("manifest") is not None
        assert data["manifest"]["seed"]
        created_sources.append(data)

    # Verify all 5 have unique source_ids, database_names, and seeds
    db_names = {s["database_name"] for s in created_sources}
    source_ids = {s["source_id"] for s in created_sources}
    seeds = {s["manifest"]["seed"] for s in created_sources}
    assert len(db_names) == 5
    assert len(source_ids) == 5
    assert len(seeds) == 5

    # Verify all 5 physically exist in MongoDB alongside untouched demo-source-id
    mongo_client = MongoDBManager.get_client()
    physical_dbs = set(mongo_client.list_database_names())
    for s in created_sources:
        assert s["database_name"] in physical_dbs
        phys_db = mongo_client[s["database_name"]]
        phys_cols = set(phys_db.list_collection_names())
        for c_name in s["collections"]:
            assert c_name in phys_cols
            assert phys_db[c_name].count_documents({}) == s["collection_counts"][c_name]

    # Verify original demo-source-id is still untouched in Source Library
    all_sources_resp = client.get("/api/sources")
    assert all_sources_resp.status_code == 200
    all_ids = {s["source_id"] for s in all_sources_resp.json()}
    assert "demo-source-id" in all_ids
    for sid in source_ids:
        assert sid in all_ids

    # Clean up the 5 generated test databases
    for sid in source_ids:
        del_resp = client.delete(f"/api/sources/{sid}")
        assert del_resp.status_code == 200


def test_same_domain_variation_and_cross_database_isolation():
    # 1. Generate two Healthcare datasets and one Finance dataset
    r_hc1 = client.post("/api/sources/generate-demo", json={"domain": "healthcare"})
    r_hc2 = client.post("/api/sources/generate-demo", json={"domain": "healthcare"})
    r_fin = client.post("/api/sources/generate-demo", json={"domain": "finance"})
    assert r_hc1.status_code == 200
    assert r_hc2.status_code == 200
    assert r_fin.status_code == 200

    hc1 = r_hc1.json()
    hc2 = r_hc2.json()
    fin = r_fin.json()

    # Same-domain test: database names, display names, and seeds must differ
    assert hc1["database_name"] != hc2["database_name"]
    assert hc1["manifest"]["seed"] != hc2["manifest"]["seed"]
    assert hc1["display_name"] != hc2["display_name"]

    # BSON Schema Explorer test on Healthcare dataset
    schema_resp = client.get(f"/api/sources/{hc1['source_id']}/schema")
    assert schema_resp.status_code == 200
    table_names = {t["name"] for t in schema_resp.json()["tables"]}
    assert table_names == {"patients", "doctors", "appointments", "prescriptions", "lab_results"}

    # Cross-Database Isolation Test:
    # While Finance (fin['source_id']) is selected, ask "How many patients are there?"
    q_leak = client.post(
        "/api/query",
        json={
            "question": "How many patients are there?",
            "source_ids": [fin["source_id"]],
        },
    )
    assert q_leak.status_code == 200
    leak_body = q_leak.json()
    # Must NOT execute against Healthcare! Must return clarification_required on Finance collections
    assert leak_body["status"] == "clarification_required"
    candidate_names = {(c.get("collection") or c["name"]).lower() for c in leak_body["candidates"]}
    assert candidate_names == {"customers", "accounts", "transactions", "investments", "branches"}

    # Now switch to Healthcare (hc1['source_id']) and ask "How many patients are there?"
    q_hc = client.post(
        "/api/query",
        json={
            "question": "How many patients are there?",
            "source_ids": [hc1["source_id"]],
        },
    )
    assert q_hc.status_code == 200
    hc_body = q_hc.json()
    assert hc_body["status"] == "success"
    assert hc_body["collection"] == "patients"
    expected_patients = hc1["collection_counts"]["patients"]
    assert int(hc_body["answer"]["value"].replace(",", "")) == expected_patients
    assert list(hc_body["rows"][0].values())[0] == expected_patients

    # Delete Healthcare #2 and verify Healthcare #1 and Finance remain intact
    del_hc2 = client.delete(f"/api/sources/{hc2['source_id']}")
    assert del_hc2.status_code == 200
    remaining_ids = {s["source_id"] for s in client.get("/api/sources").json()}
    assert hc2["source_id"] not in remaining_ids
    assert hc1["source_id"] in remaining_ids
    assert fin["source_id"] in remaining_ids

    # Clean up remaining test sources
    client.delete(f"/api/sources/{hc1['source_id']}")
    client.delete(f"/api/sources/{fin['source_id']}")
