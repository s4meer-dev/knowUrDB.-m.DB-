import os
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.models.schema import SchemaSummary
from app.models.source import SourceMetadata


@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    # Make the AI service configured for tests
    patcher_is_configured = patch(
        "app.services.gemini_provider.GeminiProvider.is_configured",
        return_value=True
    )
    patcher_get_status = patch(
        "app.services.gemini_provider.GeminiProvider.get_status_info",
        return_value={"configured": True, "status": "ready"}
    )
    
        # Mock AI output for tests
    def mock_generate_text(self, prompt: str) -> str:
        # Mock expected test queries
        if "You are a classification system for database questions" in prompt:
            if "Explain the database schema" in prompt:
                return '{"category": "SCHEMA_SUMMARY"}'
            return '{"category": "DATA_QUERY"}'
        if "classify the user question into exactly one of these categories" in prompt:
            return "VALID"
        if "suggest exactly 3 brief follow-up questions" in prompt:
            return "- Follow up 1\n- Follow up 2\n- Follow up 3"
        if "Explain the database schema" in prompt:
            return "The database contains students, courses, and departments."
        if "Drop the database." in prompt:
            return "DROP TABLE students;"
        if "Get students and courses." in prompt:
            return "SELECT * FROM students; SELECT * FROM courses;"
        if "top 10 students" in prompt.lower() or "top students" in prompt.lower() or "highest average scoring" in prompt.lower():
            return "SELECT * FROM students ORDER BY average_score DESC LIMIT 10;"
        if "average attendance" in prompt.lower():
            return "SELECT a.name, AVG(a.attendance_percentage) FROM departments a GROUP BY a.name;"
        if "most students" in prompt.lower() or "highest number of students" in prompt.lower() or "highest student count" in prompt.lower() or "maximum number of students" in prompt.lower():
            return "SELECT name, student_count FROM departments ORDER BY student_count DESC LIMIT 1;"
        if "student count by department" in prompt.lower() or "each department" in prompt.lower() or "departments with student counts" in prompt.lower():
            return "SELECT department_id, COUNT(*) FROM departments GROUP BY department_id;"
        if "how many students" in prompt.lower() or "total number of students" in prompt.lower():
            return "SELECT COUNT(*) FROM students;"
        if "how many departments" in prompt.lower():
            return "SELECT COUNT(*) FROM departments;"
        # For analysis generation
        if "Analyze this SQL query" in prompt:
            return '{"answer": {"headline": "SUCCESS", "value": "1", "unit": "", "summary": "Success"}, "insights": ["Insight"]}'
        
        return "SELECT * FROM students;"
        
    patcher_generate = patch(
        "app.services.gemini_provider.GeminiProvider.generate_text",
        autospec=True,
        side_effect=mock_generate_text
    )

    # Globally mock query_router to default to SINGLE_SOURCE so tests pass
    patcher_router = patch(
        "app.api.query.query_router.route_query",
        return_value={
            "decision": "SINGLE_SOURCE",
            "sources": [{"source_id": "demo-source-id", "type": "sqlite3"}],
            "candidates": [],
            "confidence": 1.0
        }
    )
    
    # Mock SourceManager to ensure 'demo-source-id' is found
    # Create a real temporary database file with the required schema
    import sqlite3
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    mock_db_path = os.path.join(temp_dir, "mock.db")
    
    conn = sqlite3.connect(mock_db_path)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, first_name TEXT, average_score REAL, student_count INTEGER, department_id INTEGER, attendance_percentage REAL)")
    conn.execute("CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER, student_count INTEGER, attendance_percentage REAL)")
    conn.execute("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("CREATE TABLE security_test (id INTEGER)")
    # Insert required data to satisfy assertions
    for i in range(4000):
        if i == 0:
            conn.execute("INSERT INTO students (id, first_name, average_score) VALUES (?, ?, ?)", (1, "Kelly", 95.0))
        else:
            conn.execute("INSERT INTO students (id, first_name, average_score) VALUES (?, ?, ?)", (i+1, "Test", 80.0))
            
    for i in range(12):
        conn.execute("INSERT INTO departments (id, name, department_id) VALUES (?, ?, ?)", (i+1, f"Dept {i}", i+1))
    conn.commit()
    conn.close()
    
    mock_source = SourceMetadata(
        source_id="demo-source-id",
        name="Demo University Database",
        file_path=mock_db_path,
        file_type="db",
        size_bytes=1024,
        storage_location=mock_db_path,
        detected_format="database",
        original_filename="mock.db",
        mime_type="application/x-sqlite3",
        uploaded_at="2023-01-01T00:00:00Z",
        status="ready"
    )
    patcher_source = patch(
        "app.api.query.source_manager.get_source",
        return_value=mock_source
    )
    
    patcher_db_path = patch(
        "app.api.query.source_manager.get_internal_db_path",
        return_value=mock_db_path
    )

    # Mock SchemaService to return the University schema that test_query.py expects
    from app.models.schema import DatabaseSchema, TableInfo, ColumnInfo
    university_schema = DatabaseSchema(
        tables=[
            TableInfo(name="students", columns=[ColumnInfo(name="id", data_type="INTEGER", primary_key=True), ColumnInfo(name="name", data_type="TEXT", primary_key=False)], primary_keys=["id"], foreign_keys=[]),
            TableInfo(name="departments", columns=[ColumnInfo(name="id", data_type="INTEGER", primary_key=True), ColumnInfo(name="name", data_type="TEXT", primary_key=False)], primary_keys=["id"], foreign_keys=[]),
            TableInfo(name="courses", columns=[ColumnInfo(name="id", data_type="INTEGER", primary_key=True), ColumnInfo(name="title", data_type="TEXT", primary_key=False)], primary_keys=["id"], foreign_keys=[])
        ]
    )
    patcher_schema = patch(
        "app.api.query.schema_service.get_schema",
        return_value=university_schema
    )
    patcher_schema_summary = patch(
        "app.api.query.schema_service.get_schema_summary",
        return_value=SchemaSummary(summary="Database contains the following tables: - students with columns id, name. - departments with columns id, name.", tables=2, total_columns=4)
    )

    patcher_is_configured.start()
    patcher_get_status.start()
    patcher_generate.start()
    patcher_router.start()
    patcher_source.start()
    patcher_db_path.start()
    patcher_schema.start()
    patcher_schema_summary.start()
    
    yield
    
    patcher_is_configured.stop()
    patcher_get_status.stop()
    patcher_generate.stop()
    patcher_router.stop()
    patcher_source.stop()
    patcher_db_path.stop()
    patcher_schema.stop()
    patcher_schema_summary.stop()
