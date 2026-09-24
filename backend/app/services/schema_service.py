import json
from datetime import date, datetime
from typing import Any

from bson import ObjectId

from app.core.mongodb import MongoDBManager
from app.models.schema import SchemaSummary


def _infer_bson_type(val: Any) -> str:
    if isinstance(val, ObjectId):
        return "ObjectId"
    if isinstance(val, bool):
        return "Boolean"
    if isinstance(val, int):
        return "Int64"
    if isinstance(val, float):
        return "Double"
    if isinstance(val, (datetime, date)):
        return "Date"
    if isinstance(val, dict):
        return "Object"
    if isinstance(val, list):
        if len(val) > 0 and isinstance(val[0], dict):
            return "Array<Object>"
        return "Array"
    if isinstance(val, str):
        return "String"
    return "String"


def _serialize_bson_value(val: Any) -> Any:
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, dict):
        return {k: _serialize_bson_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_serialize_bson_value(v) for v in val]
    return val


def _flatten_for_table_row(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Serializes a MongoDB document for tabular display while preserving nested/array readability.
    Top-level nested objects are both accessible via dot-notation and JSON-serialized if needed.
    """
    row: dict[str, Any] = {}
    for k, v in doc.items():
        if k == "_id":
            row["_id"] = str(v)
        elif isinstance(v, dict):
            row[k] = json.dumps(_serialize_bson_value(v))
            for sub_k, sub_v in v.items():
                if not isinstance(sub_v, (dict, list)):
                    row[f"{k}.{sub_k}"] = _serialize_bson_value(sub_v)
        elif isinstance(v, list):
            row[k] = json.dumps(_serialize_bson_value(v))
        else:
            row[k] = _serialize_bson_value(v)
    return row


class MongoSchemaService:
    """
    Introspects MongoDB collections, BSON field types, embedded documents, arrays,
    indexes, and cross-collection $lookup relationships.
    """

    def _extract_fields_from_samples(
        self, samples: list[dict[str, Any]], pk_fields: set[str]
    ) -> list[dict[str, Any]]:
        field_map: dict[str, dict[str, Any]] = {}

        def _visit(obj: dict[str, Any], prefix: str = "", is_nested: bool = False, is_array: bool = False):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else k
                btype = _infer_bson_type(v)
                if path not in field_map:
                    field_map[path] = {
                        "name": path,
                        "data_type": btype,
                        "type": btype,
                        "primary_key": path in pk_fields or path == "_id",
                        "nullable": path != "_id",
                        "is_nested": is_nested,
                        "is_array": is_array or isinstance(v, list),
                        "sample_values": [],
                    }
                if v is not None and len(field_map[path]["sample_values"]) < 3:
                    serialized = _serialize_bson_value(v)
                    if not isinstance(serialized, (dict, list)) and serialized not in field_map[path]["sample_values"]:
                        field_map[path]["sample_values"].append(serialized)
                    elif field_map[path]["data_type"] == "String" and btype != "String":
                        field_map[path]["data_type"] = btype
                        field_map[path]["type"] = btype

                # Recurse into embedded objects (up to 2 levels)
                if isinstance(v, dict) and prefix.count(".") < 2:
                    _visit(v, prefix=path, is_nested=True, is_array=is_array)
                elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and prefix.count(".") < 2:
                    _visit(v[0], prefix=f"{path}[]", is_nested=True, is_array=True)

        for doc in samples:
            _visit(doc)

        return list(field_map.values())

    def get_schema(self, source_id: str | None = None) -> dict[str, Any]:
        db = MongoDBManager.get_db()
        active_source_id = source_id or MongoDBManager.get_active_source_id()
        collection_names = MongoDBManager.list_user_collections(active_source_id)

        if not collection_names and not source_id:
            collection_names = MongoDBManager.list_user_collections(None)

        tables: list[dict[str, Any]] = []
        collection_fields_lookup: dict[str, set[str]] = {}

        # First pass: collect fields and primary keys for each collection
        for coll_name in collection_names:
            coll = db[coll_name]
            doc_count = coll.count_documents({})
            samples = list(coll.find({}).limit(25))

            # Inspect indexes
            indexes_info = []
            pk_fields = {"_id"}
            try:
                raw_indexes = coll.index_information()
                for idx_name, idx_spec in raw_indexes.items():
                    keys = [k[0] for k in idx_spec.get("key", [])]
                    unique = bool(idx_spec.get("unique", False)) or idx_name == "_id_"
                    if unique or any(k.endswith("_id") and k == f"{coll_name.rstrip('s')}_id" for k in keys):
                        pk_fields.update(keys)
                    indexes_info.append(
                        {"name": idx_name, "keys": keys, "unique": unique}
                    )
            except Exception:
                indexes_info = [{"name": "_id_", "keys": ["_id"], "unique": True}]

            # Also recognize explicit entity IDs (e.g., customer_id on customers)
            singular = coll_name.lower().rstrip("s")
            for doc in samples[:3]:
                for k in doc.keys():
                    if k.lower() in {f"{singular}_id", "id"}:
                        pk_fields.add(k)

            columns = self._extract_fields_from_samples(samples, pk_fields)
            collection_fields_lookup[coll_name] = {c["name"] for c in columns}

            sample_doc = _serialize_bson_value(samples[0]) if samples else None

            tables.append(
                {
                    "name": coll_name,
                    "document_count": doc_count,
                    "columns": columns,
                    "primary_keys": sorted(pk_fields),
                    "foreign_keys": [],
                    "indexes": indexes_info,
                    "sample_document": sample_doc,
                }
            )

        # Second pass: infer cross-collection $lookup relationships
        for t in tables:
            coll_name = t["name"]
            fks = []
            for col in t["columns"]:
                col_name = col["name"].replace("[].", ".")
                leaf_name = col_name.split(".")[-1]
                if leaf_name.endswith("_id") and leaf_name not in t["primary_keys"]:
                    prefix = leaf_name[:-3].lower()  # e.g. 'customer' from 'customer_id'
                    for other_t in tables:
                        if other_t["name"] == coll_name:
                            continue
                        other_lower = other_t["name"].lower()
                        if other_lower in {prefix, f"{prefix}s", f"{prefix}es"} or other_lower.endswith(f"_{prefix}s"):
                            ref_col = leaf_name if leaf_name in collection_fields_lookup[other_t["name"]] else "_id"
                            fks.append(
                                {
                                    "source_column": col["name"],
                                    "referenced_table": other_t["name"],
                                    "referenced_column": ref_col,
                                }
                            )
            t["foreign_keys"] = fks

        return {"tables": tables, "collections": tables}

    def get_table_schema(self, table_name: str, source_id: str | None = None) -> dict[str, Any]:
        schema = self.get_schema(source_id)
        for t in schema["tables"]:
            if t["name"].lower() == table_name.lower():
                return t
        raise ValueError(f"Collection '{table_name}' not found in active database.")

    def get_schema_summary(self, source_id: str | None = None) -> SchemaSummary:
        schema = self.get_schema(source_id)
        if not schema["tables"]:
            return SchemaSummary(summary="No collections found in the active MongoDB source.")

        lines = ["MongoDB Database Schema (Collections & Document Fields):"]
        for t in schema["tables"]:
            col_strs = []
            for c in t["columns"]:
                pk_tag = " [PRIMARY KEY]" if c.get("primary_key") else ""
                nested_tag = " [NESTED]" if c.get("is_nested") else ""
                arr_tag = " [ARRAY]" if c.get("is_array") else ""
                samples = c.get("sample_values", [])
                sample_str = f" (e.g. {', '.join(repr(s) for s in samples[:2])})" if samples else ""
                col_strs.append(f"{c['name']}: {c['data_type']}{pk_tag}{nested_tag}{arr_tag}{sample_str}")
            lines.append(
                f"- Collection '{t['name']}' ({t.get('document_count', 0)} docs): "
                + ", ".join(col_strs)
            )
            for fk in t.get("foreign_keys", []):
                lines.append(
                    f"  $lookup relation: {t['name']}.{fk['source_column']} -> {fk['referenced_table']}.{fk['referenced_column']}"
                )

        return SchemaSummary(summary="\n".join(lines))

    def get_table_sample(
        self, table_name: str, limit: int = 50
    ) -> tuple[list[str], list[dict[str, Any]]]:
        db = MongoDBManager.get_db()
        all_cols = MongoDBManager.list_user_collections(None)
        matched_col = next((c for c in all_cols if c.lower() == table_name.lower()), None)
        if not matched_col:
            raise ValueError(f"Collection '{table_name}' not found.")

        docs = list(db[matched_col].find({}).limit(min(limit, 200)))
        if not docs:
            return [], []

        rows = [_flatten_for_table_row(d) for d in docs]
        columns: list[str] = []
        for r in rows:
            for k in r.keys():
                if k not in columns:
                    columns.append(k)
        return columns, rows


# Keep SchemaService alias for full compatibility across routers and tests
SchemaService = MongoSchemaService
