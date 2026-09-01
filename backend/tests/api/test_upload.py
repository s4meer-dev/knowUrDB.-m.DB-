import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_single_upload():
    file_content = b"name,age\nAlice,30\nBob,25"
    response = client.post(
        "/api/sources/upload",
        files={"file": ("test_single.csv", file_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_single.csv"
    assert "source_id" in data
    assert data["source_id"].startswith("src_")
    
    # Verify in registry
    sources = client.get("/api/sources").json()
    assert any(s["source_id"] == data["source_id"] for s in sources)
    
def test_batch_upload():
    file1 = b"id,val\n1,100"
    file2 = b"id,val\n2,200"
    
    response = client.post(
        "/api/sources/upload/batch",
        files=[
            ("files", ("batch_1.csv", file1, "text/csv")),
            ("files", ("batch_2.csv", file2, "text/csv"))
        ]
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "batch_1.csv"
    assert data[1]["name"] == "batch_2.csv"
    assert data[0]["source_id"] != data[1]["source_id"]

def test_duplicate_filename_isolation():
    # If same filename uploaded twice, they must get different source IDs
    file_content = b"name,age\nAlice,30"
    
    res1 = client.post(
        "/api/sources/upload",
        files={"file": ("dup.csv", file_content, "text/csv")}
    )
    res2 = client.post(
        "/api/sources/upload",
        files={"file": ("dup.csv", file_content, "text/csv")}
    )
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    
    data1 = res1.json()
    data2 = res2.json()
    
    assert data1["source_id"] != data2["source_id"]
    assert data1["name"] == "dup.csv"
    assert data2["name"] == "dup.csv"
