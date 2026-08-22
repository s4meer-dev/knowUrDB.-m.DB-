from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_query_count_students():
    response = client.post("/api/query", json={"question": "How many students are in the database?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["generated_sql"] == "SELECT COUNT(*) FROM students;"
    assert "COUNT(*)" in data["columns"]
    assert len(data["rows"]) == 1
    assert data["rows"][0]["COUNT(*)"] == 4000

def test_query_count_departments():
    response = client.post("/api/query", json={"question": "How many departments exist?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["generated_sql"] == "SELECT COUNT(*) FROM departments;"
    assert data["rows"][0]["COUNT(*)"] == 12

def test_query_filtered_student():
    response = client.post("/api/query", json={"question": "Find the student with student_id 1."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "first_name" in data["columns"]
    assert data["rows"][0]["first_name"] == "Kelly"

def test_invalid_empty_question():
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400

def test_unsupported_question():
    response = client.post("/api/query", json={"question": "Tell me a joke."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Unsupported question" in data["error"]

def test_unsafe_generated_sql_rejection(monkeypatch):
    from app.services.text_to_sql_service import TextToSQLService
    
    # Mock translator to return unsafe SQL
    def mock_translate(*args, **kwargs):
        return "DROP TABLE students;"
        
    monkeypatch.setattr(TextToSQLService, "translate", mock_translate)
    
    response = client.post("/api/query", json={"question": "Drop the database."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Only SELECT or WITH queries are allowed" in data["error"]

def test_multiple_statement_rejection(monkeypatch):
    from app.services.text_to_sql_service import TextToSQLService
    
    # Mock translator to return unsafe SQL
    def mock_translate(*args, **kwargs):
        return "SELECT * FROM students; SELECT * FROM courses;"
        
    monkeypatch.setattr(TextToSQLService, "translate", mock_translate)
    
    response = client.post("/api/query", json={"question": "Get students and courses."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Multiple SQL statements are not allowed" in data["error"]
