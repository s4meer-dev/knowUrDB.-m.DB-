import re
from typing import Any

from app.services.query_executor import QueryExecutor
from app.services.schema_service import SchemaService


class MetaQueryRouter:
    """
    Handles meta-queries such as "Show all tables", "Describe database", or "How many total records".
    These queries can be answered deterministically without AI or direct user SQL execution.
    """

    def __init__(self, schema_service: SchemaService, query_executor: QueryExecutor):
        self.schema_service = schema_service
        self.query_executor = query_executor

    def normalize_question(self, question: str) -> str:
        q = question.lower().strip()
        q = q.removesuffix("?")
        q = q.replace(".", "")
        return q.strip()

    def route_meta_query(self, question: str) -> dict[str, Any] | None:
        """
        Attempts to answer the question using deterministic schema rules.
        Returns a dictionary representing the response data (columns, rows, execution_time_ms, explanation)
        if matched, otherwise returns None.
        """
        q = self.normalize_question(question)

        # 1. Table Listing & Schema Summary
        if re.search(
            r"^(show|list)( me)?( all)?( available)? tables( in the database)?$|^what tables are in the database$|^which tables exist$|^show database tables$",
            q,
        ):
            return self._handle_list_tables()

        if re.search(
            r"^what information is stored in the database$|^describe the database$|^what data is available$|^what does this database contain$|^show me the database structure$|^explain the database schema$|^give me a summary of the database$",
            q,
        ):
            return self._handle_schema_summary()

        # 2. Global Record Counts
        if re.search(
            r"^give me the total number of records$|^how many records are (there|in the database)$|^what is the total row count$|^total number of records$",
            q,
        ):
            return self._handle_global_record_count()

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
