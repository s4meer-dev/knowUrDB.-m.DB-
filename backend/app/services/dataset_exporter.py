import datetime
import hashlib
import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from bson import ObjectId, json_util

from app.core.config import settings
from app.core.mongodb import MongoDBManager

logger = logging.getLogger("knowurdb.dataset_exporter")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def resolve_dataset_root(custom_root: Path | None = None) -> tuple[Path, str]:
    """
    Resolves the absolute filesystem path and portable project-relative name
    for the unified `demo_datasets/` directory.
    """
    if custom_root is not None:
        try:
            rel = custom_root.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError:
            rel = custom_root.name
        return custom_root, rel

    configured = settings.DEMO_DATASET_ROOT.strip()
    candidate = Path(configured)
    if not candidate.is_absolute():
        abs_root = (PROJECT_ROOT / candidate).resolve()
        rel_root = candidate.as_posix().strip("/")
    else:
        abs_root = candidate.resolve()
        try:
            rel_root = abs_root.relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError:
            rel_root = abs_root.name

    abs_root.mkdir(parents=True, exist_ok=True)
    return abs_root, rel_root


def _detect_bson_type(val: Any) -> str:
    if isinstance(val, ObjectId):
        return "ObjectId"
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, int):
        return "int"
    if isinstance(val, float):
        return "double"
    if isinstance(val, datetime.datetime | datetime.date):
        return "date"
    if isinstance(val, list):
        return "array"
    if isinstance(val, dict):
        return "object"
    if val is None:
        return "null"
    return "string"


def _safe_sample_value(val: Any) -> Any:
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, datetime.datetime | datetime.date):
        return val.isoformat()
    if isinstance(val, list):
        return [_safe_sample_value(x) for x in val[:2]]
    if isinstance(val, dict):
        return {str(k): _safe_sample_value(v) for k, v in list(val.items())[:4]}
    return val


class DatasetManifestService:
    """
    Manages dataset manifests, schema definitions, metadata descriptors,
    and the global `demo_datasets/index.json` catalog.
    """

    def __init__(self, dataset_root: Path | None = None):
        self.abs_root, self.rel_root = resolve_dataset_root(dataset_root)

    def get_relative_dataset_path(self, database_name: str) -> str:
        return f"{self.rel_root}/{database_name}"

    def get_dataset_dir(self, database_name: str) -> Path:
        return self.abs_root / database_name

    def verify_dataset_snapshot(
        self,
        database_name: str,
        expected_counts: dict[str, int] | None = None,
    ) -> tuple[bool, str, list[str]]:
        """
        Verifies that `demo_datasets/<database_name>/` exists and contains valid:
        - `manifest.json`
        - `metadata.json`
        - `schema.json`
        - `README.md`
        - `collections/<col>.jsonl` with line counts matching `expected_counts`.
        Returns `(is_valid, status_reason, relative_artifacts)`.
        """
        ds_dir = self.get_dataset_dir(database_name)
        if not ds_dir.exists() or not ds_dir.is_dir():
            return False, "MISSING_FILES", []

        manifest_file = ds_dir / "manifest.json"
        metadata_file = ds_dir / "metadata.json"
        schema_file = ds_dir / "schema.json"
        readme_file = ds_dir / "README.md"
        cols_dir = ds_dir / "collections"

        for required in (manifest_file, metadata_file, schema_file, readme_file, cols_dir):
            if not required.exists():
                return False, "MISSING_FILES", []

        try:
            with open(manifest_file, encoding="utf-8") as mf:
                manifest_data = json.load(mf)
            with open(metadata_file, encoding="utf-8") as mdf:
                json.load(mdf)
            with open(schema_file, encoding="utf-8") as sf:
                json.load(sf)
        except Exception:
            return False, "CORRUPT_JSON", []

        collections_meta = manifest_data.get("collections", [])
        if not collections_meta:
            return False, "EMPTY_MANIFEST", []

        artifacts = [
            "manifest.json",
            "metadata.json",
            "schema.json",
            "README.md",
        ]

        for col_entry in collections_meta:
            col_name = col_entry.get("name")
            expected_cnt = (
                expected_counts.get(col_name, col_entry.get("document_count", 0))
                if expected_counts is not None
                else col_entry.get("document_count", 0)
            )
            rel_file = col_entry.get("file") or f"collections/{col_name}.jsonl"
            col_file = ds_dir / rel_file
            if not col_file.exists():
                return False, f"MISSING_COLLECTION_{col_name}", []

            # Count non-empty lines in the JSONL file
            line_count = 0
            with open(col_file, encoding="utf-8") as cf:
                for line in cf:
                    if line.strip():
                        line_count += 1
            if line_count != expected_cnt or line_count == 0:
                return False, f"COUNT_MISMATCH_{col_name}", []
            artifacts.append(rel_file)

        if expected_counts:
            manifest_col_names = {c.get("name") for c in collections_meta}
            for col_name in expected_counts:
                if col_name not in manifest_col_names:
                    return False, f"UNTRACKED_COLLECTION_{col_name}", []

        return True, "SYNCED", artifacts

    def rebuild_global_index(self) -> dict[str, Any]:
        """
        Scans `demo_datasets/*/manifest.json` and writes `demo_datasets/index.json`
        with an authoritative catalog of all synchronized datasets.
        """
        self.abs_root.mkdir(parents=True, exist_ok=True)
        datasets_entries: list[dict[str, Any]] = []

        for child in sorted(self.abs_root.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            manifest_path = child / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                with open(manifest_path, encoding="utf-8") as mf:
                    manifest = json.load(mf)
                datasets_entries.append(
                    {
                        "dataset_id": manifest.get("dataset_id", child.name),
                        "database_name": manifest.get("database_name", child.name),
                        "display_name": manifest.get("display_name", child.name),
                        "domain": manifest.get("domain", "enterprise"),
                        "status": manifest.get("status", "ready"),
                        "collection_count": manifest.get("collection_count", 0),
                        "document_count": manifest.get("document_count", 0),
                        "filesystem_path": f"{self.rel_root}/{child.name}",
                        "created_at": manifest.get("created_at"),
                        "content_hash": manifest.get("content_hash"),
                    }
                )
            except Exception as exc:
                logger.warning("Skipping invalid manifest in %s: %s", child, exc)

        index_payload = {
            "schema_version": "1.0",
            "generator_version": "2.0.0",
            "dataset_root": self.rel_root,
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "dataset_count": len(datasets_entries),
            "datasets": datasets_entries,
        }

        index_path = self.abs_root / "index.json"
        temp_index = self.abs_root / f".index_{uuid.uuid4().hex[:8]}.tmp"
        with open(temp_index, "w", encoding="utf-8") as idx_file:
            json.dump(index_payload, idx_file, indent=2)
        os.replace(temp_index, index_path)
        return index_payload

    def delete_dataset_snapshot(self, database_name: str) -> bool:
        """
        Deletes `demo_datasets/<database_name>/` and updates `demo_datasets/index.json`.
        """
        if not database_name:
            return False
        ds_dir = self.get_dataset_dir(database_name)
        removed = False
        if ds_dir.exists() and ds_dir.is_dir():
            shutil.rmtree(ds_dir, ignore_errors=True)
            removed = True
        self.rebuild_global_index()
        return removed


class MongoDatasetExporter:
    """
    Exports live MongoDB collections for a demo dataset into `demo_datasets/<database_name>/`
    with atomic temp-directory provisioning, BSON-aware JSONL streaming, schema extraction,
    and automatic startup reconciliation/backfill.
    """

    def __init__(self, dataset_root: Path | None = None):
        self.manifest_service = DatasetManifestService(dataset_root)
        self.abs_root = self.manifest_service.abs_root
        self.rel_root = self.manifest_service.rel_root

    def _inspect_collection_schema(
        self,
        sample_docs: list[dict[str, Any]],
        total_count: int,
        index_names: list[str],
    ) -> dict[str, Any]:
        fields_map: dict[str, dict[str, Any]] = {}
        for doc in sample_docs:
            for key, val in doc.items():
                btype = _detect_bson_type(val)
                if key not in fields_map:
                    field_info: dict[str, Any] = {
                        "bson_type": btype,
                        "nullable": val is None,
                        "sample_value": _safe_sample_value(val),
                    }
                    if isinstance(val, dict):
                        field_info["nested_fields"] = {
                            str(nk): _detect_bson_type(nv) for nk, nv in val.items()
                        }
                    elif isinstance(val, list) and val:
                        first_item = val[0]
                        field_info["items_bson_type"] = _detect_bson_type(first_item)
                        if isinstance(first_item, dict):
                            field_info["items_nested_fields"] = {
                                str(nk): _detect_bson_type(nv) for nk, nv in first_item.items()
                            }
                    fields_map[key] = field_info
                else:
                    if val is None:
                        fields_map[key]["nullable"] = True

        return {
            "document_count": total_count,
            "field_count": len(fields_map),
            "fields": fields_map,
            "indexes": index_names,
        }

    def export_database(
        self,
        database_name: str,
        display_name: str,
        domain: str,
        description: str,
        collections: list[str] | None = None,
        generation_id: str | None = None,
        seed: int | None = None,
        created_at: str | None = None,
        is_grouped_in_knowurdb: bool = False,
    ) -> dict[str, Any]:
        """
        Atomically exports a MongoDB demo database (`database_name`) into
        `demo_datasets/<database_name>/` containing:
          - `manifest.json`
          - `metadata.json`
          - `schema.json`
          - `README.md`
          - `collections/<collection>.jsonl`
        and updates `demo_datasets/index.json`.
        """
        client = MongoDBManager.get_client()
        sys_db = MongoDBManager.get_db()
        target_db = client[database_name]

        now_iso = created_at or datetime.datetime.now(datetime.UTC).isoformat()
        gen_id = generation_id or f"gen_{uuid.uuid4().hex[:12]}"
        seed_val = seed if seed is not None else 42

        # Determine collections to export
        if not collections:
            raw_cols = [
                c
                for c in target_db.list_collection_names()
                if not c.startswith("system.") and not c.startswith("_")
            ]
            collections = sorted(raw_cols)

        if not collections and database_name == "demo_database":
            collections = ["customers", "products", "orders", "employees", "students"]

        temp_dir_name = f".generating_{database_name}_{uuid.uuid4().hex[:8]}"
        temp_dir = self.abs_root / temp_dir_name
        temp_cols_dir = temp_dir / "collections"
        final_dir = self.abs_root / database_name
        rel_dataset_path = f"{self.rel_root}/{database_name}"

        try:
            temp_cols_dir.mkdir(parents=True, exist_ok=True)

            hasher = hashlib.sha256()
            hasher.update(f"{database_name}:{domain}:".encode("utf-8"))

            manifest_collections: list[dict[str, Any]] = []
            document_counts: dict[str, int] = {}
            schema_collections: dict[str, Any] = {}
            total_docs = 0
            total_indexes = 0

            for col_name in collections:
                rel_jsonl_path = f"collections/{col_name}.jsonl"
                abs_jsonl_path = temp_dir / rel_jsonl_path

                sample_docs: list[dict[str, Any]] = []
                written_lines = 0

                # Check whether documents live in standalone `target_db[col_name]`
                # or in grouped `sys_db["demo_database"]`
                standalone_count = 0
                try:
                    standalone_count = target_db[col_name].count_documents({})
                except Exception:
                    standalone_count = 0

                if standalone_count > 0 and not is_grouped_in_knowurdb:
                    expected_count = standalone_count
                    cursor = target_db[col_name].find({}).batch_size(250)
                    with open(abs_jsonl_path, "w", encoding="utf-8") as jf:
                        for doc in cursor:
                            if len(sample_docs) < 15:
                                sample_docs.append(doc)
                            line_str = json_util.dumps(doc)
                            jf.write(line_str + "\n")
                            if written_lines < 5:
                                hasher.update(line_str.encode("utf-8"))
                            written_lines += 1
                    try:
                        idx_info = target_db[col_name].index_information()
                        index_names = [
                            "_".join(f"{k}_{v}" for k, v in spec.get("key", []))
                            for spec in idx_info.values()
                        ]
                    except Exception:
                        index_names = ["_id_1"]
                else:
                    # Fallback to grouped container in `knowurdb.demo_database` if standalone is empty
                    folder_doc = sys_db["demo_database"].find_one({"_id": col_name})
                    records = (folder_doc or {}).get("records", [])
                    expected_count = len(records)
                    with open(abs_jsonl_path, "w", encoding="utf-8") as jf:
                        for idx_r, raw_rec in enumerate(records):
                            rec = dict(raw_rec)
                            if "_id" not in rec:
                                deterministic_hex = hashlib.md5(
                                    f"{database_name}:{col_name}:{idx_r}".encode("utf-8")
                                ).hexdigest()[:24]
                                rec["_id"] = ObjectId(deterministic_hex)
                            if len(sample_docs) < 15:
                                sample_docs.append(rec)
                            line_str = json_util.dumps(rec)
                            jf.write(line_str + "\n")
                            if written_lines < 5:
                                hasher.update(line_str.encode("utf-8"))
                            written_lines += 1
                    index_names = ["_id_1", f"{col_name}_id_1"]

                if written_lines != expected_count or written_lines == 0:
                    raise RuntimeError(
                        f"Export verification failed for {database_name}.{col_name}: "
                        f"expected {expected_count} lines, wrote {written_lines}"
                    )

                document_counts[col_name] = written_lines
                total_docs += written_lines
                total_indexes += max(1, len(index_names))

                manifest_collections.append(
                    {
                        "name": col_name,
                        "document_count": written_lines,
                        "file": rel_jsonl_path,
                    }
                )
                schema_collections[col_name] = self._inspect_collection_schema(
                    sample_docs=sample_docs,
                    total_count=written_lines,
                    index_names=index_names,
                )

            content_hash = f"sha256:{hasher.hexdigest()[:24]}"

            # 1. Write metadata.json
            metadata_payload = {
                "dataset_name": display_name,
                "database_name": database_name,
                "domain": domain,
                "description": description,
                "synthetic": True,
                "source_type": "MongoDB",
                "filesystem_path": rel_dataset_path,
                "collections": collections,
                "document_counts": document_counts,
                "total_documents": total_docs,
                "generated_at": now_iso,
                "generator_version": "2.0.0",
            }
            with open(temp_dir / "metadata.json", "w", encoding="utf-8") as mdf:
                json.dump(metadata_payload, mdf, indent=2)

            # 2. Write schema.json
            schema_payload = {
                "database": database_name,
                "domain": domain,
                "schema_version": "1.0",
                "inspected_at": now_iso,
                "collection_count": len(collections),
                "total_documents": total_docs,
                "collections": schema_collections,
            }
            with open(temp_dir / "schema.json", "w", encoding="utf-8") as sf:
                json.dump(schema_payload, sf, indent=2)

            # 3. Write manifest.json
            manifest_payload = {
                "dataset_id": database_name,
                "database_name": database_name,
                "display_name": display_name,
                "source_type": "mongodb",
                "domain": domain,
                "description": description,
                "status": "ready",
                "generator_version": "2.0.0",
                "template_version": "1.0",
                "schema_version": "1.0",
                "generation_id": gen_id,
                "seed": seed_val,
                "created_at": now_iso,
                "collection_count": len(collections),
                "document_count": total_docs,
                "index_count": total_indexes,
                "content_hash": content_hash,
                "filesystem_path": rel_dataset_path,
                "collections": manifest_collections,
            }
            with open(temp_dir / "manifest.json", "w", encoding="utf-8") as mf:
                json.dump(manifest_payload, mf, indent=2)

            # 4. Write README.md
            readme_lines = [
                f"# {display_name} (`{database_name}`)",
                "",
                f"> **Domain**: `{domain}` | **Source Type**: `MongoDB` | **Total Documents**: `{total_docs}` | **Collections**: `{len(collections)}`",
                "",
                description,
                "",
                "## MongoDB Runtime & Filesystem Snapshot",
                "",
                f"- **MongoDB Database**: `{database_name}` (`mongodb://127.0.0.1:27017/{database_name}`)",
                f"- **Filesystem Snapshot Path**: `{rel_dataset_path}`",
                f"- **Content Hash**: `{content_hash}`",
                f"- **Generated At**: `{now_iso}`",
                "",
                "## Collections & JSONL Snapshots",
                "",
                "| Collection | Documents | Snapshot File | Key Indexed Fields |",
                "| :--- | ---: | :--- | :--- |",
            ]
            for col_name in collections:
                cnt = document_counts[col_name]
                col_schema = schema_collections.get(col_name, {})
                field_names = list((col_schema.get("fields") or {}).keys())[:6]
                fields_str = ", ".join(f"`{fn}`" for fn in field_names)
                readme_lines.append(
                    f"| `{col_name}` | {cnt} | `collections/{col_name}.jsonl` | {fields_str} |"
                )

            readme_lines.extend(
                [
                    "",
                    "## Directory Structure",
                    "",
                    "```text",
                    f"{database_name}/",
                    "├── manifest.json",
                    "├── metadata.json",
                    "├── schema.json",
                    "├── README.md",
                    "└── collections/",
                ]
                + [f"    ├── {c}.jsonl" for c in collections[:-1]]
                + ([f"    └── {collections[-1]}.jsonl"] if collections else [])
                + [
                    "```",
                    "",
                ]
            )
            with open(temp_dir / "README.md", "w", encoding="utf-8") as rf:
                rf.write("\n".join(readme_lines))

            # 5. Atomic swap from `.generating_<database_name>_<uuid>` -> `demo_datasets/<database_name>`
            if final_dir.exists():
                backup_dir = self.abs_root / f".backup_{database_name}_{uuid.uuid4().hex[:6]}"
                os.replace(final_dir, backup_dir)
                try:
                    os.replace(temp_dir, final_dir)
                finally:
                    shutil.rmtree(backup_dir, ignore_errors=True)
            else:
                os.replace(temp_dir, final_dir)

            # 6. Verify final snapshot & rebuild `demo_datasets/index.json`
            valid, reason, artifacts = self.manifest_service.verify_dataset_snapshot(
                database_name, expected_counts=document_counts
            )
            if not valid:
                raise RuntimeError(
                    f"Post-export snapshot verification failed for {database_name}: {reason}"
                )

            self.manifest_service.rebuild_global_index()

            # Also mirror manifest into MongoDB `target_db["_dataset_manifest"]`
            try:
                if database_name != "demo_database":
                    target_db["_dataset_manifest"].delete_many({})
                    target_db["_dataset_manifest"].insert_one(dict(manifest_payload))
            except Exception:
                pass

            manifest_payload["dataset_artifacts"] = artifacts
            manifest_payload["sync_status"] = "SYNCED"
            return manifest_payload

        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error("Failed exporting MongoDB dataset %s to filesystem: %s", database_name, exc)
            raise

    def restore_database_from_snapshot(self, database_name: str) -> dict[str, Any] | None:
        """
        If `demo_datasets/<database_name>/` exists on disk with valid `manifest.json` and
        `collections/*.jsonl`, but the MongoDB database is missing, restores the collections
        into MongoDB so the dataset is immediately queryable again.
        """
        valid, _reason, _artifacts = self.manifest_service.verify_dataset_snapshot(database_name)
        if not valid:
            return None

        ds_dir = self.manifest_service.get_dataset_dir(database_name)
        manifest_path = ds_dir / "manifest.json"
        with open(manifest_path, encoding="utf-8") as mf:
            manifest = json.load(mf)

        client = MongoDBManager.get_client()
        target_db = client[database_name]

        for col_entry in manifest.get("collections", []):
            col_name = col_entry["name"]
            rel_file = col_entry.get("file") or f"collections/{col_name}.jsonl"
            col_file = ds_dir / rel_file
            docs: list[dict[str, Any]] = []
            with open(col_file, encoding="utf-8") as cf:
                for line in cf:
                    stripped = line.strip()
                    if stripped:
                        docs.append(json_util.loads(stripped))
            if docs:
                target_db[col_name].drop()
                target_db[col_name].insert_many(docs)

        if database_name != "demo_database":
            target_db["_dataset_manifest"].delete_many({})
            target_db["_dataset_manifest"].insert_one(dict(manifest))

        return manifest

    def reconcile_and_backfill_all(self) -> dict[str, Any]:
        """
        Idempotent startup & on-demand reconciliation across:
        1. `demo_database` (preserved baseline dataset)
        2. All `demo_*` databases in MongoDB (`demo_ecommerce_8578`, `demo_energy_c46f`, `demo_telecom_7aee`, etc.)
        3. All `demo_datasets/*` folders on disk.
        """
        client = MongoDBManager.get_client()
        sys_db = MongoDBManager.get_db()
        self.abs_root.mkdir(parents=True, exist_ok=True)

        # Clean up any interrupted `.generating_*` directories
        for child in list(self.abs_root.iterdir()):
            if child.is_dir() and child.name.startswith(".generating_"):
                shutil.rmtree(child, ignore_errors=True)

        # Remove legacy `database/sources/mongodb` folder if present so only `demo_datasets/` is used
        legacy_dir = PROJECT_ROOT / "database"
        if legacy_dir.exists() and legacy_dir.is_dir():
            shutil.rmtree(legacy_dir, ignore_errors=True)

        summary: dict[str, list[str]] = {
            "synchronized": [],
            "backfilled": [],
            "restored_to_mongodb": [],
        }

        try:
            mongo_db_names = set(client.list_database_names())
        except Exception as exc:
            logger.warning("Could not list MongoDB databases during reconciliation: %s", exc)
            return summary

        # Ensure `demo_database` is included if registered in `sys_sources` or MongoDB
        candidate_dbs: set[str] = set()
        for db_name in mongo_db_names:
            if db_name == "demo_database" or db_name.startswith("demo_"):
                candidate_dbs.add(db_name)

        demo_source_doc = sys_db[MongoDBManager.SYS_SOURCES].find_one({"source_id": "demo-source-id"})
        if demo_source_doc:
            candidate_dbs.add("demo_database")

        for src_doc in sys_db[MongoDBManager.SYS_SOURCES].find({"source_category": "mongodb"}):
            db_name = src_doc.get("database_name")
            if db_name and (db_name == "demo_database" or db_name.startswith("demo_")):
                candidate_dbs.add(db_name)

        for db_name in sorted(candidate_dbs):
            try:
                source_id = "demo-source-id" if db_name == "demo_database" else f"mongodb_{db_name}"
                src_doc = sys_db[MongoDBManager.SYS_SOURCES].find_one({"source_id": source_id})

                target_db = client[db_name]
                existing_manifest = None
                try:
                    existing_manifest = target_db["_dataset_manifest"].find_one({}, {"_id": 0})
                except Exception:
                    existing_manifest = None

                if not existing_manifest and src_doc and isinstance(src_doc.get("manifest"), dict):
                    existing_manifest = src_doc["manifest"]

                # Determine collection counts in MongoDB
                expected_counts: dict[str, int] = {}
                raw_cols = [
                    c
                    for c in target_db.list_collection_names()
                    if not c.startswith("system.") and not c.startswith("_")
                ]
                for c_name in sorted(raw_cols):
                    cnt = target_db[c_name].count_documents({})
                    if cnt > 0:
                        expected_counts[c_name] = cnt

                if not expected_counts and db_name == "demo_database":
                    for folder_doc in sys_db["demo_database"].find({}):
                        t_name = folder_doc.get("table_name") or folder_doc.get("_id")
                        recs = folder_doc.get("records", [])
                        if t_name and recs:
                            expected_counts[str(t_name)] = len(recs)

                if not expected_counts:
                    continue

                is_valid, _reason, artifacts = self.manifest_service.verify_dataset_snapshot(
                    db_name, expected_counts=expected_counts
                )

                if is_valid:
                    summary["synchronized"].append(db_name)
                    manifest_path = self.manifest_service.get_dataset_dir(db_name) / "manifest.json"
                    with open(manifest_path, encoding="utf-8") as mf:
                        manifest_data = json.load(mf)
                else:
                    # Backfill from existing MongoDB documents without regenerating
                    domain = (
                        (existing_manifest or {}).get("domain")
                        or (src_doc or {}).get("domain")
                        or (db_name.split("_")[1] if "_" in db_name and db_name != "demo_database" else "enterprise")
                    )
                    display_name = (
                        (existing_manifest or {}).get("display_name")
                        or (src_doc or {}).get("display_name")
                        or ("Enterprise & Campus Intelligence" if db_name == "demo_database" else db_name.replace("_", " ").title())
                    )
                    description = (
                        (existing_manifest or {}).get("description")
                        or (src_doc or {}).get("description")
                        or f"Synthetic {domain} MongoDB dataset ({db_name})."
                    )
                    created_at = (
                        (existing_manifest or {}).get("created_at")
                        or (src_doc or {}).get("uploaded_at")
                        or datetime.datetime.now(datetime.UTC).isoformat()
                    )
                    manifest_data = self.export_database(
                        database_name=db_name,
                        display_name=display_name,
                        domain=domain,
                        description=description,
                        collections=list(expected_counts.keys()),
                        generation_id=(existing_manifest or {}).get("generation_id"),
                        seed=(existing_manifest or {}).get("seed"),
                        created_at=created_at,
                    )
                    artifacts = manifest_data.get("dataset_artifacts", [])
                    summary["backfilled"].append(db_name)

                rel_path = self.manifest_service.get_relative_dataset_path(db_name)
                sys_db[MongoDBManager.SYS_SOURCES].update_one(
                    {"source_id": source_id},
                    {
                        "$set": {
                            "filesystem_path": rel_path,
                            "sync_status": "SYNCED",
                            "dataset_artifacts": artifacts,
                            "manifest": manifest_data,
                        }
                    },
                )
            except Exception as exc:
                logger.warning("Failed reconciling dataset %s: %s", db_name, exc)

        # Check for any filesystem-only datasets in `demo_datasets/*` and restore them if valid
        for child in sorted(self.abs_root.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            db_name = child.name
            if db_name in candidate_dbs:
                continue
            restored_manifest = self.restore_database_from_snapshot(db_name)
            if restored_manifest:
                summary["restored_to_mongodb"].append(db_name)

        self.manifest_service.rebuild_global_index()
        return summary
