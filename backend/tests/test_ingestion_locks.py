import os
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.services.source_manager import STORAGE_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: ensure temp dirs exist
    test_storage = Path(STORAGE_DIR)
    test_storage.mkdir(parents=True, exist_ok=True)
    yield
    # Teardown: we don't necessarily clear it all out because we want to see if files are locked
    # If they are locked, shutil.rmtree will fail on Windows, causing the test to fail.
    # We will attempt to remove the test sources created during these tests.
    pass

def create_dummy_csv(path, rows=50):
    with open(path, "w", encoding="utf-8") as f:
        f.write("id,name,value\n")
        for i in range(rows):
            f.write(f"{i},Item {i},{i * 1.5}\n")

def test_sequential_upload_no_locks(tmp_path):
    """
    Test uploading multiple CSV files sequentially.
    If the SQLite connection is leaked, shutil.move or subsequent processing will fail with WinError 32.
    """
    csv1 = tmp_path / "batch_1.csv"
    csv2 = tmp_path / "batch_2.csv"
    csv3 = tmp_path / "dup.csv"
    
    create_dummy_csv(csv1, 100)
    create_dummy_csv(csv2, 100)
    create_dummy_csv(csv3, 100)
    
    source_ids = []
    
    # Upload 1
    with open(csv1, "rb") as f:
        res1 = client.post("/api/sources/upload", files={"file": ("batch_1.csv", f, "text/csv")})
    assert res1.status_code == 200, res1.text
    assert res1.json()["status"] == "ready"
    assert res1.json()["table_count"] > 0
    source_ids.append(res1.json()["source_id"])
    
    # Upload 2
    with open(csv2, "rb") as f:
        res2 = client.post("/api/sources/upload", files={"file": ("batch_2.csv", f, "text/csv")})
    assert res2.status_code == 200, res2.text
    assert res2.json()["status"] == "ready"
    assert res2.json()["table_count"] > 0
    source_ids.append(res2.json()["source_id"])

    # Upload 3 (Duplicate filename)
    with open(csv3, "rb") as f:
        res3 = client.post("/api/sources/upload", files={"file": ("batch_1.csv", f, "text/csv")})
    assert res3.status_code == 200, res3.text
    assert res3.json()["status"] == "ready"
    assert res3.json()["table_count"] > 0
    source_ids.append(res3.json()["source_id"])
    
    # Attempt to delete sources
    for sid in source_ids:
        delete_res = client.delete(f"/api/sources/{sid}")
        assert delete_res.status_code == 200, delete_res.text

def test_concurrent_upload_batch(tmp_path):
    """
    Test uploading multiple files in a batch concurrently.
    """
    csv1 = tmp_path / "concurrent_1.csv"
    csv2 = tmp_path / "concurrent_2.csv"
    create_dummy_csv(csv1, 100)
    create_dummy_csv(csv2, 100)
    
    with open(csv1, "rb") as f1, open(csv2, "rb") as f2:
        res = client.post("/api/sources/upload/batch", files=[
            ("files", ("concurrent_1.csv", f1, "text/csv")),
            ("files", ("concurrent_2.csv", f2, "text/csv"))
        ])
    
    assert res.status_code == 200, res.text
    sources = res.json()
    assert len(sources) == 2
    for s in sources:
        assert s["status"] == "ready"
        assert s["table_count"] > 0
        client.delete(f"/api/sources/{s['source_id']}")

