import json
import logging
from typing import Any

from app.services.query_executor import QueryExecutor
from app.services.schema_service import SchemaService
from app.services.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

class MetaQueryRouter:
    """
    Handles meta-queries such as "Show all tables", "Describe database", or "How many total records".
    These queries can be answered deterministically without direct user SQL execution.
    """

    def __init__(self, schema_service: SchemaService, query_executor: QueryExecutor, ai_provider: GeminiProvider):
        self.schema_service = schema_service
        self.query_executor = query_executor
        self.ai = ai_provider

    def route_meta_query(self, question: str) -> dict[str, Any] | None:
        """
        Attempts to answer the question using AI-driven intent classification.
        Returns a dictionary representing the response data (columns, rows, execution_time_ms, explanation)
        if matched, otherwise returns None.
        """
        prompt = f"""
You are a classification system for database questions.
Analyze the user's question and determine if it is asking for high-level metadata about the database itself, or if it requires querying the actual data records.

Categories:
1. LIST_TABLES: User wants to know what tables exist, how many tables there are, or list the tables. Examples: "how many tables are there in the dataset", "what tables do we have", "list tables".
2. SCHEMA_SUMMARY: User wants to know the structure of the database, what columns exist, or a general description of the data schema. Examples: "describe the database", "what is the schema", "what columns are in users".
3. GLOBAL_COUNT: User wants to know the total number of records/rows across the entire database or asking for "total data" overall. Examples: "total data", "how many rows total", "record count".
4. DATA_QUERY: User is asking for specific data, aggregations, or conditional queries that require writing a SQL SELECT statement. Examples: "how many users are from USA", "what is the average price", "show me John's orders", "total revenue".

Question: "{question}"

Return EXACTLY a JSON object with this structure (no markdown, no backticks):
{{
  "category": "LIST_TABLES" | "SCHEMA_SUMMARY" | "GLOBAL_COUNT" | "DATA_QUERY"
}}
"""
        try:
            response_text = self.ai.generate_text(prompt)
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
                
            data = json.loads(response_text.strip())
            category = data.get("category", "DATA_QUERY")
            
            if category == "LIST_TABLES":
                return self._handle_list_tables()
            elif category == "SCHEMA_SUMMARY":
                return self._handle_schema_summary()
            elif category == "GLOBAL_COUNT":
                return self._handle_global_record_count()
            else:
                return None
        except Exception as e:
            logger.error(f"Error classifying meta query: {e}")
            return None

    def _handle_list_tables(self) -> dict[str, Any]:
        tables = self.schema_service.get_table_names()
        columns = ["table_name"]
        rows = [{"table_name": t} for t in tables]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": 0.0,
            "explanation": "Here is the list of all available tables in the database.",
            "generated_sql": "",
        }

    def _handle_schema_summary(self) -> dict[str, Any]:
        schema = self.schema_service.get_schema()
        columns = ["table_name", "columns", "primary_keys", "foreign_keys"]
        rows = []
        for table in schema.tables:
            rows.append(
                {
                    "table_name": table.name,
                    "columns": ", ".join(col.name for col in table.columns),
                    "primary_keys": ", ".join(table.primary_keys)
                    if table.primary_keys
                    else "None",
                    "foreign_keys": ", ".join(
                        f"{fk.source_column} -> {fk.referenced_table}.{fk.referenced_column}"
                        for fk in table.foreign_keys
                    )
                    if table.foreign_keys
                    else "None",
                }
            )
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": 0.0,
            "explanation": "This is a summary of the database structure, including tables, columns, and relationships.",
            "generated_sql": "",
        }

    def _handle_global_record_count(self) -> dict[str, Any]:
        tables = self.schema_service.get_table_names()
        columns = ["table_name", "record_count"]
        rows = []

        # Execute individual counts safely using the executor
        total_time = 0.0
        for table in tables:
            # Table names from schema_service are already validated
            sql = f"SELECT COUNT(*) FROM {table};"
            try:
                _, t_rows, exec_time = self.query_executor.execute(sql)
                count = t_rows[0]["COUNT(*)"]
                rows.append({"table_name": table, "record_count": count})
                total_time += exec_time
            except Exception:  # noqa: BLE001
                rows.append({"table_name": table, "record_count": 0})

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": round(total_time, 2),
            "explanation": "Here is the total number of records stored in each table across the database.",
            "generated_sql": "",
        }
