from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_concurrent_mongodb_uploads():
    for i in range(3):
        csv_bytes = f"id,name,score\n1,Item_{i},9{i}.5\n2,ItemB_{i},8{i}.0".encode()
        res = client.post(
            "/api/sources/upload",
            files={"file": (f"upload_lock_{i}.csv", csv_bytes, "text/csv")},
        )
        assert res.status_code == 200
        sid = res.json()["source_id"]
        del_res = client.delete(f"/api/sources/{sid}")
        assert del_res.status_code == 200
