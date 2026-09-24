import datetime
import uuid

import pymongo

from app.core.mongodb import MongoDBManager
from app.models.query import QueryHistoryItem


class HistoryService:
    """
    MongoDB-native Query History Service.
    Persists all executed queries, MongoDB aggregation pipelines, timings, and statuses
    in `_sys_query_history`.
    """

    def log_query(
        self,
        question: str,
        query_source: str,
        status: str,
        generated_sql: str | None = None,
        generated_mongo_query: str | None = None,
        source_id: str | None = None,
        row_count: int | None = None,
        execution_time_ms: float | None = None,
        error_message: str | None = None,
    ) -> str:
        query_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.UTC).isoformat()
        pipeline_str = generated_mongo_query or generated_sql

        doc = {
            "id": query_id,
            "question": question,
            "generated_mongo_query": pipeline_str,
            "generated_sql": pipeline_str,
            "query_source": query_source,
            "source_id": source_id,
            "status": status,
            "row_count": row_count if row_count is not None else 0,
            "execution_time_ms": round(execution_time_ms, 2) if execution_time_ms is not None else 0.0,
            "error_message": error_message,
            "created_at": created_at,
        }
        MongoDBManager.get_db()[MongoDBManager.SYS_QUERY_HISTORY].insert_one(doc)
        return query_id

    def get_history(self, limit: int = 50) -> list[QueryHistoryItem]:
        docs = list(
            MongoDBManager.get_db()[MongoDBManager.SYS_QUERY_HISTORY]
            .find({}, sort=[("created_at", pymongo.DESCENDING)])
            .limit(limit)
        )
        return [
            QueryHistoryItem(**{k: v for k, v in d.items() if k != "_id"})
            for d in docs
        ]

    def get_query_by_id(self, query_id: str) -> QueryHistoryItem | None:
        doc = MongoDBManager.get_db()[MongoDBManager.SYS_QUERY_HISTORY].find_one(
            {"id": query_id}
        )
        if not doc:
            return None
        return QueryHistoryItem(**{k: v for k, v in doc.items() if k != "_id"})

    def get_history_item(self, query_id: str) -> QueryHistoryItem | None:
        return self.get_query_by_id(query_id)

    def delete_query(self, query_id: str) -> bool:
        res = MongoDBManager.get_db()[MongoDBManager.SYS_QUERY_HISTORY].delete_one(
            {"id": query_id}
        )
        return res.deleted_count > 0

    def delete_history_item(self, query_id: str) -> bool:
        return self.delete_query(query_id)

    def clear_history(self) -> None:
        MongoDBManager.get_db()[MongoDBManager.SYS_QUERY_HISTORY].delete_many({})
