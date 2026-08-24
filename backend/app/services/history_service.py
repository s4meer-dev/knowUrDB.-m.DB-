import uuid

from app.core.app_database import app_db_provider
from app.models.query import QueryHistoryItem


class HistoryService:
    """
    Handles saving and retrieving query history from the application database.
    """

    def __init__(self):
        self.db_provider = app_db_provider

    def log_query(
        self,
        question: str,
        query_source: str,
        status: str,
        generated_sql: str | None = None,
        row_count: int | None = None,
        execution_time_ms: float | None = None,
        error_message: str | None = None,
    ) -> str:
        """
        Logs a query execution attempt to history.
        Returns the generated query ID.
        """
        query_id = str(uuid.uuid4())

        with self.db_provider.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO query_history (
                    id, question, generated_sql, query_source, status,
                    row_count, execution_time_ms, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query_id,
                    question,
                    generated_sql,
                    query_source,
                    status,
                    row_count,
                    execution_time_ms,
                    error_message,
                ),
            )
        return query_id

    def get_history(self, limit: int = 50) -> list[QueryHistoryItem]:
        """
        Retrieves recent query history, newest first.
        """
        with self.db_provider.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM query_history ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()

        return [
            QueryHistoryItem(
                id=row["id"],
                question=row["question"],
                generated_sql=row["generated_sql"],
                query_source=row["query_source"],
                status=row["status"],
                row_count=row["row_count"],
                execution_time_ms=row["execution_time_ms"],
                error_message=row["error_message"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_history_item(self, query_id: str) -> QueryHistoryItem | None:
        """
        Retrieves a single history item by ID.
        """
        with self.db_provider.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM query_history WHERE id = ?", (query_id,)
            )
            row = cursor.fetchone()

        if not row:
            return None

        return QueryHistoryItem(
            id=row["id"],
            question=row["question"],
            generated_sql=row["generated_sql"],
            query_source=row["query_source"],
            status=row["status"],
            row_count=row["row_count"],
            execution_time_ms=row["execution_time_ms"],
            error_message=row["error_message"],
            created_at=row["created_at"],
        )

    def delete_history_item(self, query_id: str) -> bool:
        """
        Deletes a single history item. Returns True if deleted, False if not found.
        """
        with self.db_provider.get_connection() as conn:
            cursor = conn.execute("DELETE FROM query_history WHERE id = ?", (query_id,))
            return cursor.rowcount > 0

    def clear_history(self):
        """
        Clears all query history.
        """
        with self.db_provider.get_connection() as conn:
            conn.execute("DELETE FROM query_history")
