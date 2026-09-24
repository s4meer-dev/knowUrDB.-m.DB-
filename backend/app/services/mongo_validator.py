import json
import re
from typing import Any

from app.core.config import settings
from app.core.mongodb import MongoDBManager


class MongoQuerySafetyError(ValueError):
    """Raised when a MongoDB query or pipeline violates read-only or security policies."""



# Alias for compatibility with any caller catching SQLSafetyError
SQLSafetyError = MongoQuerySafetyError


class MongoQueryValidator:
    """
    Application-level security firewall for MongoDB queries and aggregation pipelines.
    Enforces strict read-only access and blocks operator/JavaScript injection, system collection
    access, and mutating aggregation stages ($out, $merge).
    """

    ALLOWED_OPERATIONS = {"find", "aggregate", "count", "distinct"}

    PROHIBITED_OPERATIONS = {
        "insert",
        "insertone",
        "insertmany",
        "update",
        "updateone",
        "updatemany",
        "replaceone",
        "delete",
        "deleteone",
        "deletemany",
        "remove",
        "drop",
        "dropdatabase",
        "dropindexes",
        "createindex",
        "createindexes",
        "renamecollection",
        "createuser",
        "dropuser",
        "grantrolestouser",
        "eval",
        "mapreduce",
        "bulkwrite",
        "findoneanddelete",
        "findoneandupdate",
        "findoneandreplace",
    }

    PROHIBITED_STAGES_AND_OPERATORS = {
        "$out",
        "$merge",
        "$where",
        "$function",
        "$accumulator",
        "$currentop",
        "$collstats",
        "$indexstats",
        "$listlocalsessions",
        "$listsessions",
        "$plancachestats",
    }

    DANGEROUS_PROMPT_PATTERNS = re.compile(
        r"(\b(drop|delete|truncate|remove|wipe|destroy|alter|modify)\b.*\b(table|tables|collection|collections|database|databases|document|documents|record|records|row|rows|all|from|products|customers|orders|employees|students)\b)"
        r"|(\b(insert\s+into|update\s+\w+\s+set|create\s+user|drop\s+user|rename\s+collection|grant\s+role)\b)"
        r"|(db\.\w*\.(drop|remove|delete|insert|update|replace|rename|createIndex|dropIndex|mapReduce|eval))",
        re.IGNORECASE,
    )

    MAX_PIPELINE_STAGES = 15

    @classmethod
    def validate_question_safety(cls, question: str) -> None:
        """
        Rejects explicitly destructive or malicious natural language commands immediately.
        """
        if not question:
            return
        if cls.DANGEROUS_PROMPT_PATTERNS.search(question):
            raise MongoQuerySafetyError(
                "Prohibited destructive or mutating operation detected in request."
            )
        lower_q = question.lower()
        if "$where" in lower_q or "$function" in lower_q or "$out" in lower_q or "$merge" in lower_q:
            raise MongoQuerySafetyError(
                "Prohibited MongoDB operator injection detected in request."
            )

    @classmethod
    def validate(cls, query_or_str: dict[str, Any] | str) -> dict[str, Any]:
        """
        Validates a structured MongoDB query dictionary or serialized query string.
        Returns the normalized structured query dictionary if valid, or raises MongoQuerySafetyError.
        """
        if not query_or_str:
            raise MongoQuerySafetyError("Query cannot be empty.")

        if isinstance(query_or_str, str):
            raw = query_or_str.strip()
            # Reject legacy destructive SQL or raw MongoDB shell mutations
            if cls.DANGEROUS_PROMPT_PATTERNS.search(raw):
                raise MongoQuerySafetyError(
                    "Mutating or administrative database command is strictly prohibited."
                )
            for bad_op in cls.PROHIBITED_STAGES_AND_OPERATORS:
                if bad_op in raw.lower():
                    raise MongoQuerySafetyError(
                        f"Prohibited MongoDB operator or stage '{bad_op}' is not allowed."
                    )
            for bad_cmd in cls.PROHIBITED_OPERATIONS:
                if re.search(rf"\.{bad_cmd}\s*\(", raw, re.IGNORECASE):
                    raise MongoQuerySafetyError(
                        f"Mutating MongoDB method '.{bad_cmd}()' is strictly prohibited."
                    )

            parsed = cls._parse_string_to_structured(raw)
        elif isinstance(query_or_str, dict):
            parsed = dict(query_or_str)
        else:
            raise MongoQuerySafetyError("Invalid query format; expected structured dict or JSON.")

        operation = str(parsed.get("operation", "aggregate")).lower().strip()
        if operation in cls.PROHIBITED_OPERATIONS or operation not in cls.ALLOWED_OPERATIONS:
            raise MongoQuerySafetyError(
                f"Operation '{operation}' is not permitted. Only read-only operations ({sorted(cls.ALLOWED_OPERATIONS)}) are allowed."
            )

        collection = str(parsed.get("collection") or parsed.get("source") or "").strip()
        if not collection:
            raise MongoQuerySafetyError("Target MongoDB collection must be specified.")

        if (
            collection.startswith("_sys_")
            or collection.startswith("system.")
            or collection.lower() in {"admin", "local", "config"}
        ):
            raise MongoQuerySafetyError(
                f"Access to internal or system collection '{collection}' is prohibited."
            )

        # Validate pipeline depth and stages
        pipeline = parsed.get("pipeline", [])
        if not isinstance(pipeline, list):
            raise MongoQuerySafetyError("Aggregation pipeline must be a list of stage objects.")
        if len(pipeline) > cls.MAX_PIPELINE_STAGES:
            raise MongoQuerySafetyError(
                f"Aggregation pipeline exceeds maximum allowed complexity ({cls.MAX_PIPELINE_STAGES} stages)."
            )

        cls._inspect_recursive(parsed)

        # Enforce maximum limit safeguard
        max_limit = settings.MAX_QUERY_LIMIT
        if parsed.get("limit") is not None:
            try:
                lim = int(parsed["limit"])
                if lim <= 0 or lim > max_limit * 10:
                    raise MongoQuerySafetyError(
                        f"Query limit ({lim}) exceeds maximum allowed threshold ({max_limit})."
                    )
                parsed["limit"] = min(lim, max_limit)
            except ValueError as exc:
                raise MongoQuerySafetyError("Query limit must be a valid integer.") from exc
        else:
            parsed["limit"] = min(100, max_limit)

        parsed["collection"] = collection
        parsed["operation"] = operation
        return parsed

    @classmethod
    def _inspect_recursive(cls, node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                k_lower = str(k).lower().strip()
                if k_lower in cls.PROHIBITED_STAGES_AND_OPERATORS:
                    raise MongoQuerySafetyError(
                        f"Prohibited MongoDB stage or operator '{k}' detected."
                    )
                if k_lower in cls.PROHIBITED_OPERATIONS:
                    raise MongoQuerySafetyError(
                        f"Prohibited MongoDB write operation '{k}' detected."
                    )
                if k_lower == "$lookup" and isinstance(v, dict):
                    from_col = str(v.get("from", "")).strip()
                    if from_col.startswith("_sys_") or from_col.startswith("system."):
                        raise MongoQuerySafetyError(
                            f"Prohibited $lookup target collection '{from_col}'."
                        )
                cls._inspect_recursive(v)
        elif isinstance(node, list):
            for item in node:
                cls._inspect_recursive(item)
        elif isinstance(node, str):
            n_lower = node.lower()
            if "function(" in n_lower or "db.eval" in n_lower or "process.env" in n_lower:
                raise MongoQuerySafetyError(
                    "Server-side JavaScript execution is strictly prohibited."
                )

    @classmethod
    def _parse_string_to_structured(cls, raw: str) -> dict[str, Any]:
        """
        Parses either a JSON object string or a shell-style `db.collection.aggregate([...])`
        representation into a normalized structured MongoDB query dictionary.
        """
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```javascript") or cleaned.startswith("```js"):
            cleaned = cleaned.split("\n", 1)[-1]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        cleaned = cleaned.removesuffix("```")
        cleaned = cleaned.strip()

        # 1. Try direct JSON object
        if cleaned.startswith("{"):
            try:
                data = json.loads(cleaned)
                if isinstance(data, dict):
                    return data
            except Exception as exc:
                raise MongoQuerySafetyError(f"Malformed JSON query representation: {exc}") from exc

        # 2. Try shell syntax: db.<collection>.<operation>(<args>)
        m = re.match(
            r"^db\.([a-zA-Z0-9_]+)\.(aggregate|find|countDocuments|count|distinct)\s*\((.*)\)\s*;?$",
            cleaned,
            re.DOTALL,
        )
        if m:
            col, op, inner = m.group(1), m.group(2), m.group(3).strip()
            norm_op = "count" if op in ("count", "countDocuments") else op
            try:
                parsed_arg = json.loads(inner) if inner else ([] if norm_op == "aggregate" else {})
            except Exception as exc:
                raise MongoQuerySafetyError(f"Malformed MongoDB arguments in {op}(): {exc}") from exc

            if norm_op == "aggregate":
                if not isinstance(parsed_arg, list):
                    raise MongoQuerySafetyError("aggregate() argument must be a pipeline array.")
                return {"collection": col, "operation": "aggregate", "pipeline": parsed_arg}
            elif norm_op == "find":
                return {
                    "collection": col,
                    "operation": "find",
                    "filter": parsed_arg if isinstance(parsed_arg, dict) else {},
                }
            elif norm_op == "count":
                return {
                    "collection": col,
                    "operation": "count",
                    "filter": parsed_arg if isinstance(parsed_arg, dict) else {},
                }

        raise MongoQuerySafetyError(
            "Unsupported or unsafe query syntax. Expected structured MongoDB query JSON or read-only db.<collection>.aggregate([...])."
        )

    @classmethod
    def validate_against_db(cls, query_or_str: dict[str, Any] | str, db_provider: Any = None) -> dict[str, Any]:
        structured = cls.validate(query_or_str)
        collection = structured["collection"]
        user_cols = MongoDBManager.list_user_collections(None)
        matched = next((c for c in user_cols if c.lower() == collection.lower()), None)
        if not matched:
            raise ValueError(
                f"Collection '{collection}' does not exist in MongoDB. Available collections: {user_cols}"
            )
        structured["collection"] = matched
        return structured

    @staticmethod
    def format_human_readable(structured: dict[str, Any]) -> str:
        """
        Formats a structured MongoDB query dictionary into clean, human-readable
        MongoDB shell / aggregation pipeline syntax for the Mongo Query Viewer panel.
        """
        col = structured.get("collection", "collection")
        op = structured.get("operation", "aggregate")
        if op == "aggregate":
            pipeline = structured.get("pipeline", [])
            return f"db.{col}.aggregate(\n{json.dumps(pipeline, indent=2)}\n)"
        elif op == "count":
            flt = structured.get("filter", {})
            return f"db.{col}.countDocuments({json.dumps(flt, indent=2)})"
        elif op == "distinct":
            field = structured.get("distinct_field", "_id")
            flt = structured.get("filter", {})
            return f'db.{col}.distinct("{field}", {json.dumps(flt, indent=2)})'
        else:
            flt = structured.get("filter", {})
            proj = structured.get("projection")
            sort_spec = structured.get("sort")
            limit_val = structured.get("limit", 100)
            base = f"db.{col}.find({json.dumps(flt, indent=2)}"
            if proj:
                base += f", {json.dumps(proj)}"
            base += ")"
            if sort_spec:
                base += f".sort({json.dumps(sort_spec)})"
            if limit_val:
                base += f".limit({limit_val})"
            return base
