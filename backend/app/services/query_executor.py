import time
from typing import Any

from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.mongodb import MongoDBManager
from app.services.mongo_validator import MongoQuerySafetyError, MongoQueryValidator
from app.services.schema_service import _flatten_for_table_row, _serialize_bson_value


class QueryExecutionError(Exception):
    pass


class MongoQueryExecutor:
    """
    Executes validated read-only MongoDB queries (`aggregate`, `find`, `count`, `distinct`)
    against the active MongoDB database and returns normalized tabular columns, rows, and timing.
    """

    def execute(
        self, query: dict[str, Any] | str
    ) -> tuple[list[str], list[dict[str, Any]], float]:
        start_time = time.perf_counter()

        try:
            structured = MongoQueryValidator.validate_against_db(query)
        except MongoQuerySafetyError:
            raise
        except ValueError as exc:
            raise QueryExecutionError(f"Database error: {exc}") from exc

        db = MongoDBManager.get_source_db()
        collection_name = structured["collection"]
        container_col, is_grouped = MongoDBManager.resolve_container_for_table(collection_name)
        coll = db[container_col]
        operation = structured["operation"]
        max_limit = structured.get("limit", settings.MAX_QUERY_LIMIT)

        unwrap_prefix = (
            [
                {"$match": {"_id": collection_name}},
                {"$unwind": "$records"},
                {"$replaceRoot": {"newRoot": "$records"}},
            ]
            if is_grouped
            else []
        )

        try:
            raw_docs: list[dict[str, Any]] = []

            if operation == "count":
                flt = structured.get("filter") or {}
                if is_grouped:
                    pipe = list(unwrap_prefix)
                    if flt:
                        pipe.append({"$match": flt})
                    pipe.append({"$count": "count"})
                    res = list(coll.aggregate(pipe))
                    cnt = res[0]["count"] if res else 0
                else:
                    cnt = coll.count_documents(flt)
                raw_docs = [{"count": cnt}]

            elif operation == "distinct":
                field = structured.get("distinct_field") or "_id"
                flt = structured.get("filter") or {}
                if is_grouped:
                    pipe = list(unwrap_prefix)
                    if flt:
                        pipe.append({"$match": flt})
                    pipe.append({"$group": {"_id": f"${field}"}})
                    pipe.append({"$limit": max_limit})
                    values = [r["_id"] for r in coll.aggregate(pipe) if r.get("_id") is not None]
                else:
                    values = coll.distinct(field, flt)
                raw_docs = [{field: _serialize_bson_value(v)} for v in values[:max_limit]]

            elif operation == "find":
                flt = structured.get("filter") or {}
                proj = structured.get("projection")
                sort_spec = structured.get("sort")
                if is_grouped:
                    pipe = list(unwrap_prefix)
                    if flt:
                        pipe.append({"$match": flt})
                    if sort_spec:
                        if isinstance(sort_spec, dict) and sort_spec:
                            pipe.append({"$sort": sort_spec})
                        elif isinstance(sort_spec, list) and sort_spec:
                            pipe.append({"$sort": dict(sort_spec)})
                    if proj and isinstance(proj, dict):
                        pipe.append({"$project": proj})
                    pipe.append({"$limit": max_limit})
                    raw_docs = list(coll.aggregate(pipe))
                else:
                    cursor = coll.find(flt, proj)
                    if sort_spec:
                        if isinstance(sort_spec, dict):
                            cursor = cursor.sort(list(sort_spec.items()))
                        elif isinstance(sort_spec, list):
                            cursor = cursor.sort(sort_spec)
                    cursor = cursor.limit(max_limit)
                    raw_docs = list(cursor)

            elif operation == "aggregate":
                rewritten_stages: list[dict[str, Any]] = []
                for stage in structured.get("pipeline") or []:
                    if isinstance(stage, dict) and "$lookup" in stage:
                        lk = stage["$lookup"]
                        from_tbl = lk.get("from", "")
                        local_f = lk.get("localField")
                        foreign_f = lk.get("foreignField")
                        as_f = lk.get("as", "joined")
                        target_cont, target_grouped = MongoDBManager.resolve_container_for_table(from_tbl)
                        if target_grouped and local_f and foreign_f:
                            rewritten_stages.append(
                                {
                                    "$lookup": {
                                        "from": target_cont,
                                        "let": {"join_val": f"${local_f}"},
                                        "pipeline": [
                                            {"$match": {"_id": from_tbl}},
                                            {"$unwind": "$records"},
                                            {"$replaceRoot": {"newRoot": "$records"}},
                                            {
                                                "$match": {
                                                    "$expr": {
                                                        "$eq": [f"${foreign_f}", "$$join_val"]
                                                    }
                                                }
                                            },
                                        ],
                                        "as": as_f,
                                    }
                                }
                            )
                            continue
                    rewritten_stages.append(stage)

                pipeline = list(unwrap_prefix) + rewritten_stages
                has_terminal_limit_or_count = any(
                    "$limit" in stage or "$count" in stage for stage in pipeline if isinstance(stage, dict)
                )
                if not has_terminal_limit_or_count:
                    pipeline.append({"$limit": max_limit})

                cursor = coll.aggregate(pipeline)
                raw_docs = list(cursor)

            rows: list[dict[str, Any]] = []
            columns: list[str] = []

            for doc in raw_docs:
                flat = _flatten_for_table_row(doc)
                # Omit internal _id column only when meaningful domain fields exist
                if "_id" in flat and len(flat) > 1 and isinstance(doc.get("_id"), object) and str(type(doc.get("_id"))).endswith("ObjectId'>"):
                    flat.pop("_id", None)
                rows.append(flat)
                for k in flat.keys():
                    if k not in columns:
                        columns.append(k)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return columns, rows, round(elapsed_ms, 2)

        except MongoQuerySafetyError:
            raise
        except PyMongoError as exc:
            raise QueryExecutionError(f"Database error: {exc}") from exc
        except Exception as exc:
            raise QueryExecutionError(f"Database error: {exc}") from exc


# Backwards-compatible alias
QueryExecutor = MongoQueryExecutor
