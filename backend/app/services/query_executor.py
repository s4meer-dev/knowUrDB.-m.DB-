import sqlite3
import time
from typing import Any

from app.core.database import DatabaseProvider
from app.services.sql_validator import SQLSafetyError, SQLValidator


class QueryExecutionError(Exception):
    pass


class QueryExecutor:
    """
    Executes validated SQL safely and formats the result.
    """
    def __init__(self, db_provider: DatabaseProvider):
        self.db_provider = db_provider

    def execute(self, sql: str) -> tuple[list[str], list[dict[str, Any]], float]:
        """
        Executes a SQL string and returns (columns, rows, execution_time_ms).
        """
        # Double check safety
        try:
            SQLValidator.validate(sql)
        except SQLSafetyError as e:
            raise QueryExecutionError(f"Safety validation failed: {e!s}")

        start_time = time.perf_counter()
        
        conn = self.db_provider.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Fetch results
            rows_raw = cursor.fetchall()
            
            # Extract column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Convert rows to dictionaries mapping column name to value
            rows = []
            for row in rows_raw:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                rows.append(row_dict)
                
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            return columns, rows, execution_time_ms
            
        except sqlite3.Error as e:
            # Handle SQLite errors gracefully without exposing raw internals if possible,
            # but providing enough context for the user to understand what went wrong
            raise QueryExecutionError(f"Database error: {e!s}")
        finally:
            conn.close()
