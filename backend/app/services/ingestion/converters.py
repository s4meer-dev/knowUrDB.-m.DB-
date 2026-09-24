import datetime
import json
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pymongo

from app.core.mongodb import MongoDBManager
from app.services.ingestion.detectors import FileFormat


class ConversionError(Exception):
    pass


def _sanitize_collection_name(raw_name: str, unique_prefix: str = "") -> str:
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", raw_name.strip().lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    if not clean or clean[0].isdigit():
        clean = f"col_{clean}"
    if unique_prefix:
        return f"{unique_prefix}_{clean}"[:60]
    return clean[:60]


def _sanitize_field_name(key: str) -> str:
    clean = str(key).strip().replace("\x00", "")
    if clean.startswith("$"):
        clean = clean.lstrip("$")
    return clean or "field"


def _normalize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date)):
        return val.isoformat()
    if isinstance(val, str):
        s = val.strip()
        # Try parsing JSON array or object strings into native MongoDB structures
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, (list, dict)):
                    return parsed
            except Exception:
                pass
        return s
    if hasattr(val, "item"):
        return val.item()
    return val


def _structure_mongo_document(flat_row: dict[str, Any]) -> dict[str, Any]:
    """
    Applies MongoDB document modeling to a flat dictionary record:
    1. Normalizes BSON-compatible values and strips NaN/null noise.
    2. Groups semantic prefixes (e.g., contact_email/contact_phone, address_city/address_state)
       or dot-separated keys into nested embedded documents while keeping top-level queryability.
    """
    doc: dict[str, Any] = {}
    nested_groups: dict[str, dict[str, Any]] = {}

    for raw_k, raw_v in flat_row.items():
        k = _sanitize_field_name(raw_k)
        v = _normalize_value(raw_v)
        if v is None:
            continue

        # Support explicit dot-notation in headers (e.g. "address.city")
        if "." in k:
            parts = k.split(".", 1)
            parent, child = parts[0], parts[1]
            nested_groups.setdefault(parent, {})[child] = v
            doc[k.replace(".", "_")] = v
            continue

        # Detect natural domain sub-documents (contact_*, address_*, shipping_*, billing_*, metrics_*)
        for prefix in ("contact_", "address_", "location_", "shipping_", "billing_", "profile_"):
            if k.startswith(prefix) and len(k) > len(prefix):
                group_name = prefix[:-1]
                sub_key = k[len(prefix) :]
                nested_groups.setdefault(group_name, {})[sub_key] = v
                break

        doc[k] = v

    for group_name, sub_doc in nested_groups.items():
        if sub_doc and group_name not in doc:
            doc[group_name] = sub_doc

    return doc


def _create_intelligent_indexes(collection, sample_docs: list[dict[str, Any]]) -> int:
    """
    Inspects uploaded documents and creates safe, high-value MongoDB indexes
    on identifier, status, category, and timestamp fields.
    """
    if not sample_docs:
        return 1
    keys_seen: set[str] = set()
    for d in sample_docs[:10]:
        keys_seen.update(d.keys())

    created = 1  # _id_ index exists by default
    for k in sorted(keys_seen):
        if k == "_id":
            continue
        kl = k.lower()
        if (
            kl == "id"
            or kl.endswith("_id")
            or kl in {"email", "status", "category", "department", "month", "date", "created_at", "tier", "name"}
        ):
            try:
                collection.create_index([(k, pymongo.ASCENDING)])
                created += 1
            except Exception:
                pass
        if created >= 8:
            break
    return created


class FormatConverter:
    """
    Converts structured tabular and database files into native MongoDB collections.
    """

    @staticmethod
    def convert_to_mongodb(
        file_path: str, format_type: str, source_id: str, original_filename: str
    ) -> dict[str, Any]:
        db = MongoDBManager.get_db()
        base_stem = os.path.splitext(original_filename)[0]
        prefix = source_id.replace("-", "_")[:8]
        collections_created: list[str] = []
        total_records = 0
        total_indexes = 0

        def _ingest_dataframe(df: pd.DataFrame, table_name: str) -> None:
            nonlocal total_records, total_indexes
            if df.empty and len(df.columns) == 0:
                raise ConversionError(f"Dataset '{table_name}' contains no columns or valid structure.")

            # Clean column names
            df.columns = [
                _sanitize_field_name(str(c)) if str(c).strip() else f"col_{i}"
                for i, c in enumerate(df.columns)
            ]

            col_name = _sanitize_collection_name(table_name, prefix)
            coll = db[col_name]
            coll.drop()

            raw_records = df.to_dict(orient="records")
            mongo_docs = [_structure_mongo_document(r) for r in raw_records if any(pd.notna(v) for v in r.values())]

            if mongo_docs:
                # Batch insert in chunks of 2000 for memory & wire efficiency
                batch_size = 2000
                for i in range(0, len(mongo_docs), batch_size):
                    coll.insert_many(mongo_docs[i : i + batch_size])

            idx_count = _create_intelligent_indexes(coll, mongo_docs[:20])
            doc_count = len(mongo_docs)
            total_records += doc_count
            total_indexes += idx_count
            collections_created.append(col_name)

            db[MongoDBManager.SYS_COLLECTIONS_METADATA].update_one(
                {"source_id": source_id, "collection_name": col_name},
                {
                    "$set": {
                        "source_id": source_id,
                        "collection_name": col_name,
                        "original_name": table_name,
                        "document_count": doc_count,
                        "index_count": idx_count,
                        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
                    }
                },
                upsert=True,
            )

        try:
            if format_type == FileFormat.CSV:
                df = pd.read_csv(file_path)
                _ingest_dataframe(df, base_stem)

            elif format_type == FileFormat.TSV:
                df = pd.read_csv(file_path, sep="\t")
                _ingest_dataframe(df, base_stem)

            elif format_type == FileFormat.EXCEL:
                sheets = pd.read_excel(file_path, sheet_name=None)
                for sheet_name, df in sheets.items():
                    tname = f"{base_stem}_{sheet_name}" if len(sheets) > 1 else base_stem
                    _ingest_dataframe(df, tname)

            elif format_type == FileFormat.PARQUET:
                df = pd.read_parquet(file_path)
                _ingest_dataframe(df, base_stem)

            elif format_type == FileFormat.JSON:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # Check if dict of collection_name -> list of docs
                    if all(isinstance(v, list) for v in data.values()) and len(data) > 0:
                        for key_name, items in data.items():
                            df = pd.DataFrame(items)
                            _ingest_dataframe(df, key_name)
                    else:
                        df = pd.DataFrame([data])
                        _ingest_dataframe(df, base_stem)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                    _ingest_dataframe(df, base_stem)
                else:
                    raise ConversionError("JSON root must be an object or array of objects.")

            elif format_type == FileFormat.JSONL:
                df = pd.read_json(file_path, lines=True)
                _ingest_dataframe(df, base_stem)

            elif format_type in (
                FileFormat.SQLITE,
                FileFormat.GENERIC_SQL,
                FileFormat.MYSQL_DUMP,
                FileFormat.POSTGRES_DUMP,
            ):
                # Isolated migration importer for legacy SQL/SQLite files into MongoDB collections
                from app.services.ingestion.sql_migration_importer import import_sql_source_to_mongodb

                migrated = import_sql_source_to_mongodb(file_path, format_type, base_stem)
                for table_name, df in migrated.items():
                    _ingest_dataframe(df, table_name)

            else:
                raise ConversionError(f"Unsupported format for MongoDB ingestion: {format_type}")

            if not collections_created:
                raise ConversionError("No collections could be extracted from the uploaded file.")

            return {
                "collections": collections_created,
                "table_count": len(collections_created),
                "record_count": total_records,
                "index_count": total_indexes,
            }

        except ConversionError:
            raise
        except Exception as exc:
            raise ConversionError(f"Failed to ingest '{original_filename}' into MongoDB: {exc}") from exc
