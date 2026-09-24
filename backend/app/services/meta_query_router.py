import re
import time
from typing import Any

from app.core.mongodb import MongoDBManager
from app.services.schema_service import MongoSchemaService


class MetaQueryRouter:
    """
    Deterministic MongoDB Meta-Query Router.
    Handles database/collection discovery, collection counts, schema overviews,
    and index inspections in sub-millisecond time without requiring an LLM call.
    """

    def __init__(
        self,
        schema_service: MongoSchemaService,
        query_executor: Any = None,
        ai_provider: Any = None,
    ):
        self.schema_service = schema_service
        self.query_executor = query_executor
        self.ai = ai_provider

    def route_meta_query(self, question: str) -> dict[str, Any] | None:
        start_time = time.perf_counter()
        q = question.strip().lower()
        q_clean = re.sub(r"[^\w\s]", "", q)

        schema = self.schema_service.get_schema()
        collections = schema.get("tables", [])
        if not collections:
            return None

        # 1. Questions asking about what collections/tables exist in the database
        if re.search(
            r"\b(what|which|list|show|describe)\b.*\b(collections|tables|datasets|schema|structure)\b",
            q_clean,
        ) or q_clean in {"schema", "show collections", "list collections", "show tables", "list tables", "describe database"}:
            rows = []
            for col in collections:
                rows.append(
                    {
                        "collection": col["name"],
                        "document_count": col.get("document_count", 0),
                        "field_count": len(col.get("columns", [])),
                        "indexes": len(col.get("indexes", [])),
                        "fields": ", ".join(c["name"] for c in col.get("columns", [])[:6]),
                    }
                )
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            col_names = ", ".join(c["name"] for c in collections)
            return {
                "generated_sql": "db.getCollectionInfos()",
                "columns": ["collection", "document_count", "field_count", "indexes", "fields"],
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": elapsed,
                "headline": "MONGODB COLLECTIONS",
                "value": str(len(rows)),
                "unit": "collections",
                "summary": f"The active MongoDB source contains {len(rows)} collections: {col_names}.",
            }

        # 2. Total record/document count across the active source
        if re.search(r"\b(how many total records|total documents in database|how many records in total)\b", q_clean):
            total_docs = sum(c.get("document_count", 0) for c in collections)
            rows = [{"collection": c["name"], "documents": c.get("document_count", 0)} for c in collections]
            elapsed = round((time.perf_counter() - start_time) * 1000.0, 2)
            return {
                "generated_sql": 'db.stats({ scale: 1 })',
                "columns": ["collection", "documents"],
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": elapsed,
                "headline": "TOTAL MONGODB DOCUMENTS",
                "value": f"{total_docs:,}",
                "unit": "documents",
                "summary": f"There are {total_docs:,} total BSON documents stored across {len(collections)} collections.",
            }

        return None
