from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_query_count_students():
    response = client.post(
        "/api/query", json={"question": "How many students are in the database?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["generated_sql"] == "SELECT COUNT(*) FROM students;"
    assert "COUNT(*)" in data["columns"]
    assert len(data["rows"]) == 1
    assert data["rows"][0]["COUNT(*)"] == 4000


def test_query_count_departments():
    response = client.post(
        "/api/query", json={"question": "How many departments exist?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["generated_sql"] == "SELECT COUNT(*) FROM departments;"
    assert data["rows"][0]["COUNT(*)"] == 12


def test_query_filtered_student():
    response = client.post(
        "/api/query", json={"question": "Find the student with student_id 1."}
    )
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


def test_nlp_student_counting_variations():
    questions = [
        "How many students are in the database?",
        "How many students are there?",
        "Total number of students",
    ]
    for q in questions:
        response = client.post("/api/query", json={"question": q})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success", f"Failed for question: {q}"
        assert data["generated_sql"] == "SELECT COUNT(*) FROM students;"


def test_nlp_department_student_counts():
    questions = [
        "Show student count by department",
        "How many students are in each department?",
        "List departments with student counts",
    ]
    for q in questions:
        response = client.post("/api/query", json={"question": q})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success", f"Failed for question: {q}"
        assert "GROUP BY department_id" in data["generated_sql"]


def test_nlp_department_with_most_students():
    questions = [
        "Which department has the most students?",
        "Which department has highest number of students?",
        "What department has the most students?",
        "Show me the department with the highest student count.",
        "Which department has the maximum number of students?",
    ]
    for q in questions:
        response = client.post("/api/query", json={"question": q})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success", f"Failed for question: {q}"
        assert "ORDER BY student_count DESC" in data["generated_sql"]
        assert "LIMIT 1" in data["generated_sql"]
        # Ensure it returns exactly one row
        assert len(data["rows"]) == 1
        assert "student_count" in data["columns"]


def test_nlp_average_attendance_by_department():
    questions = [
        "Show average attendance by department",
        "Average attendance for each department",
        "Which department has the highest average attendance?",
    ]
    for q in questions:
        response = client.post("/api/query", json={"question": q})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success", f"Failed for question: {q}"
        assert "AVG(a.attendance_percentage)" in data["generated_sql"]


def test_nlp_top_students_by_average_marks():
    questions = [
        "Show the top 10 students by average marks.",
        "Top students by average score",
        "List top 10 students based on marks",
        "Highest average scoring students",
    ]
    for q in questions:
        response = client.post("/api/query", json={"question": q})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success", f"Failed for question: {q}"
        assert "ORDER BY average_score DESC" in data["generated_sql"]
        assert "LIMIT 10" in data["generated_sql"]


def test_read_only_protection():
    import sqlite3

    from app.core.database import demo_db_provider

    conn = demo_db_provider.get_connection()
    try:
        conn.execute("CREATE TABLE security_test (id INTEGER);")
        assert False, "Should have raised exception for writing to read-only DB"
    except sqlite3.OperationalError as e:
        assert "readonly database" in str(e)
    finally:
        conn.close()
