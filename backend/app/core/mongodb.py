import datetime
import logging
import re
from typing import Any

import mongomock
import pymongo
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger("knowurdb.mongodb")


class _SysCollectionProxy:
    """
    Virtualizes the 6 internal system collections (`_sys_sources`, `_sys_collections_metadata`,
    `_sys_query_history`, `_sys_document_chunks`, `_sys_settings`, `_sys_workspaces`)
    into a SINGLE physical MongoDB collection (`_system`) inside `knowurdb`.
    This keeps MongoDB Compass completely clean with only one `_system` item under `knowurdb`.
    """

    def __init__(self, raw_collection: Any, sys_type: str):
        self._col = raw_collection
        self._sys_type = sys_type

    def _scoped_filter(self, flt: dict[str, Any] | None) -> dict[str, Any]:
        if not flt:
            return {"_sys_type": self._sys_type}
        if "_sys_type" in flt:
            return flt
        return {"$and": [{"_sys_type": self._sys_type}, flt]}

    def create_index(self, keys: Any, **kwargs: Any) -> Any:
        # Avoid global unique collisions across virtual types by making indexes non-unique on shared collection
        kwargs.pop("unique", None)
        return self._col.create_index(keys, **kwargs)

    def count_documents(self, flt: dict[str, Any] | None = None) -> int:
        return self._col.count_documents(self._scoped_filter(flt))

    def find_one(
        self, flt: dict[str, Any] | None = None, projection: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any] | None:
        doc = self._col.find_one(self._scoped_filter(flt), projection, **kwargs)
        if doc and isinstance(doc, dict):
            doc = dict(doc)
            doc.pop("_sys_type", None)
        return doc

    def find(
        self, flt: dict[str, Any] | None = None, projection: dict[str, Any] | None = None, **kwargs: Any
    ) -> "_SysCursorProxy":
        cursor = self._col.find(self._scoped_filter(flt), projection, **kwargs)
        return _SysCursorProxy(cursor)

    def insert_one(self, doc: dict[str, Any]) -> Any:
        payload = dict(doc)
        payload["_sys_type"] = self._sys_type
        return self._col.insert_one(payload)

    def insert_many(self, docs: list[dict[str, Any]]) -> Any:
        payloads = []
        for d in docs:
            p = dict(d)
            p["_sys_type"] = self._sys_type
            payloads.append(p)
        return self._col.insert_many(payloads)

    def update_one(self, flt: dict[str, Any], update: dict[str, Any], upsert: bool = False) -> Any:
        upd = dict(update)
        if "$set" in upd:
            upd["$set"] = dict(upd["$set"])
            upd["$set"]["_sys_type"] = self._sys_type
        else:
            upd["$set"] = {"_sys_type": self._sys_type}
        return self._col.update_one(self._scoped_filter(flt), upd, upsert=upsert)

    def delete_one(self, flt: dict[str, Any]) -> Any:
        return self._col.delete_one(self._scoped_filter(flt))

    def delete_many(self, flt: dict[str, Any]) -> Any:
        return self._col.delete_many(self._scoped_filter(flt))

    def drop(self) -> None:
        self._col.delete_many({"_sys_type": self._sys_type})


class _SysCursorProxy:
    def __init__(self, cursor: Any):
        self._cursor = cursor

    def sort(self, *args: Any, **kwargs: Any) -> "_SysCursorProxy":
        self._cursor = self._cursor.sort(*args, **kwargs)
        return self

    def limit(self, n: int) -> "_SysCursorProxy":
        self._cursor = self._cursor.limit(n)
        return self

    def __iter__(self):
        for doc in self._cursor:
            if isinstance(doc, dict):
                d = dict(doc)
                d.pop("_sys_type", None)
                yield d
            else:
                yield doc


class _KnowUrDBDatabaseFacade:
    """
    Wraps a MongoDB Database (`knowurdb` or an independent `demo_<domain>_<id>` database) so that:
    - Accessing any `_sys_*` key ALWAYS routes to the central `_SysCollectionProxy(sys_raw_db['_system'], key)`
      inside `knowurdb`.
    - Accessing any user dataset collection (`patients`, `accounts`, `demo_database`, etc.) routes directly
      to `raw_db[collection_name]`.
    """

    def __init__(self, raw_db: Database, sys_raw_db: Database | None = None):
        self._raw_db = raw_db
        self._sys_raw_db = sys_raw_db if sys_raw_db is not None else raw_db

    def __getitem__(self, name: str) -> Any:
        if name in MongoDBManager.SYSTEM_COLLECTIONS and name != MongoDBManager.PHYSICAL_SYSTEM_COLLECTION:
            return _SysCollectionProxy(self._sys_raw_db[MongoDBManager.PHYSICAL_SYSTEM_COLLECTION], name)
        return self._raw_db[name]

    def __getattr__(self, item: str) -> Any:
        return getattr(self._raw_db, item)


class MongoDBManager:
    """
    Centralized MongoDB connection & multi-database isolation manager.
    - Central metadata (`_system`) and the preserved initial `demo_database` live in `knowurdb`.
    - Every generated random demo dataset (`demo_healthcare_a81f`, `demo_finance_39bc`, etc.)
      is provisioned as a REAL, independent MongoDB database visible at the top level of
      MongoDB Compass while registered in `knowurdb._system`.
    """

    _client: pymongo.MongoClient | mongomock.MongoClient | None = None
    _db_name: str = "knowurdb"
    _is_mock: bool = False
    _active_source_id: str | None = None

    PHYSICAL_SYSTEM_COLLECTION = "_system"

    SYS_WORKSPACES = "_sys_workspaces"
    SYS_SOURCES = "_sys_sources"
    SYS_COLLECTIONS_METADATA = "_sys_collections_metadata"
    SYS_QUERY_HISTORY = "_sys_query_history"
    SYS_DOCUMENT_CHUNKS = "_sys_document_chunks"
    SYS_SETTINGS = "_sys_settings"

    SYSTEM_COLLECTIONS = {
        PHYSICAL_SYSTEM_COLLECTION,
        SYS_WORKSPACES,
        SYS_SOURCES,
        SYS_COLLECTIONS_METADATA,
        SYS_QUERY_HISTORY,
        SYS_DOCUMENT_CHUNKS,
        SYS_SETTINGS,
    }

    @classmethod
    def get_client(cls) -> pymongo.MongoClient | mongomock.MongoClient:
        if cls._client is None:
            try:
                client = pymongo.MongoClient(
                    settings.MONGODB_URI,
                    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                    serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
                )
                client.admin.command("ping")
                cls._client = client
                cls._is_mock = False
                logger.info(
                    "Connected to live MongoDB server at %s (main_db=%s)",
                    settings.MONGODB_URI,
                    cls._db_name,
                )
            except Exception as exc:
                logger.warning(
                    "Live MongoDB server unreachable (%s); activating embedded mongomock fallback.",
                    exc,
                )
                cls._client = mongomock.MongoClient()
                cls._is_mock = True
        return cls._client

    _initialized: bool = False
    _initializing: bool = False

    @classmethod
    def get_db(cls, db_name: str | None = None) -> Any:
        """Returns the requested MongoDB database wrapped with the central `_system` collection proxy."""
        client = cls.get_client()
        sys_raw_db = client[cls._db_name]
        raw_db = client[db_name or cls._db_name]
        wrapped_db = _KnowUrDBDatabaseFacade(raw_db, sys_raw_db=sys_raw_db)
        if not cls._initialized and not cls._initializing and db_name is None:
            cls._initializing = True
            try:
                cls.init_db()
                cls._initialized = True
            finally:
                cls._initializing = False
        return wrapped_db

    @classmethod
    def resolve_physical_database_name(cls, source_id: str | None = None) -> str:
        """
        Resolves the physical MongoDB database name for a given `source_id` (or the active source).
        - For independent generated demo databases (`demo_healthcare_a81f`, `demo_finance_39bc`, etc.),
          returns that exact physical MongoDB database name.
        - For `demo-source-id` or uploaded files inside `knowurdb`, returns `cls._db_name` (`knowurdb`).
        """
        sid = source_id or cls.get_active_source_id()
        if not sid:
            return cls._db_name

        sys_db = cls.get_db()
        src = sys_db[cls.SYS_SOURCES].find_one({"source_id": sid})
        if src:
            phys_db = src.get("physical_database")
            if phys_db and isinstance(phys_db, str) and not phys_db.startswith("knowurdb"):
                return phys_db
            db_name = src.get("database_name")
            if (
                db_name
                and isinstance(db_name, str)
                and "/" not in db_name
                and db_name != cls._db_name
                and db_name != "demo_database"
            ):
                return db_name
        return cls._db_name

    @classmethod
    def get_source_db(cls, source_id: str | None = None) -> Any:
        """
        Returns the MongoDB database corresponding to `source_id` (or the active source).
        Ensures strict database isolation between independent `demo_<domain>_<id>` databases
        and `knowurdb`.
        """
        target_db_name = cls.resolve_physical_database_name(source_id)
        return cls.get_db(target_db_name)

    @classmethod
    def allocate_collection_folder_name(cls, base_label: str, is_demo: bool = False) -> str:
        """
        Allocates a single clean collection/folder name inside `knowurdb`:
        - Uploaded file `brands.csv` -> `brands` (or `brands_2` if `brands` already exists)
        """
        raw_db = cls.get_client()[cls._db_name]
        existing_cols = set(raw_db.list_collection_names())

        if is_demo:
            base = "demo_database"
        else:
            clean = re.sub(r"[^a-zA-Z0-9_]", "_", base_label.strip().lower())
            clean = re.sub(r"_+", "_", clean).strip("_")[:40]
            if not clean or clean[0].isdigit() or clean.startswith("_"):
                clean = f"dataset_{clean}".strip("_")
            base = clean

        if base not in existing_cols:
            return base

        idx = 2
        while f"{base}_{idx}" in existing_cols:
            idx += 1
        return f"{base}_{idx}"

    @classmethod
    def resolve_container_for_table(
        cls, table_name: str, source_id: str | None = None
    ) -> tuple[str, bool]:
        """
        Determines how a logical table/collection (`patients`, `products`, `customers`, etc.)
        is stored in its target MongoDB database:
        Returns `(physical_collection_name, is_grouped_container)`.
        """
        sys_db = cls.get_db()
        sid = source_id or cls.get_active_source_id()

        if sid:
            meta = sys_db[cls.SYS_COLLECTIONS_METADATA].find_one(
                {"source_id": sid, "collection_name": table_name}
            )
            if meta:
                is_grouped = bool(meta.get("is_grouped", False))
                container = meta.get("container_collection") or table_name
                return container, is_grouped

            # Check if `sid` is an independent MongoDB database containing `table_name` directly
            phys_db_name = cls.resolve_physical_database_name(sid)
            if phys_db_name != cls._db_name:
                raw_target_db = cls.get_client()[phys_db_name]
                if table_name in raw_target_db.list_collection_names():
                    return table_name, False

            # If `sid` is `demo-source-id` (`demo_database`), check grouped container
            if sid == "demo-source-id":
                raw_main_db = cls.get_client()[cls._db_name]
                if "demo_database" in raw_main_db.list_collection_names():
                    if raw_main_db["demo_database"].count_documents({"_id": table_name}) > 0:
                        return "demo_database", True

        # Fallback only if source_id was not set
        meta_any = sys_db[cls.SYS_COLLECTIONS_METADATA].find_one({"collection_name": table_name})
        if meta_any and meta_any.get("container_collection"):
            return meta_any["container_collection"], bool(meta_any.get("is_grouped", False))

        raw_db = cls.get_client()[cls._db_name]
        if "demo_database" in raw_db.list_collection_names():
            if raw_db["demo_database"].count_documents({"_id": table_name}) > 0:
                return "demo_database", True

        return table_name, False

    @classmethod
    def set_database_name(cls, db_name: str) -> None:
        cls._db_name = db_name
        cls._initialized = False

    @classmethod
    def reset_client(cls, use_mock: bool = False, db_name: str | None = None) -> None:
        if cls._client is not None:
            try:
                cls._client.close()
            except Exception:
                pass
        cls._client = None
        if db_name:
            cls._db_name = db_name
        if use_mock:
            cls._client = mongomock.MongoClient()
            cls._is_mock = True
        cls._initialized = False

    @classmethod
    def ping(cls) -> dict[str, Any]:
        try:
            client = cls.get_client()
            res = client.admin.command("ping")
            version = "mongomock" if cls._is_mock else client.server_info().get("version", "unknown")
            return {
                "connected": bool(res.get("ok") == 1.0),
                "engine": "mongomock" if cls._is_mock else "mongodb",
                "version": version,
                "database": cls._db_name,
            }
        except PyMongoError as exc:
            logger.error("MongoDB ping failed: %s", exc)
            return {
                "connected": False,
                "engine": "mongodb",
                "database": cls._db_name,
                "error": str(exc),
            }

    @classmethod
    def init_db(cls) -> None:
        """
        Initializes the single `_system` collection inside `knowurdb` and seeds the initial
        `demo_database` collection if no sources exist.
        """
        db = cls.get_db()
        raw_db = cls.get_client()[cls._db_name]
        raw_db[cls.PHYSICAL_SYSTEM_COLLECTION].create_index("_sys_type")

        if db[cls.SYS_WORKSPACES].count_documents({"workspace_id": "default"}) == 0:
            db[cls.SYS_WORKSPACES].insert_one(
                {
                    "workspace_id": "default",
                    "name": "Default Intelligence Workspace",
                    "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )

        try:
            from app.services.demo_generator import DemoGenerator

            gen = DemoGenerator()
            if db[cls.SYS_SOURCES].count_documents({}) == 0:
                gen.seed_initial_demo_if_empty()
            gen.reconcile_managed_databases()
        except Exception as exc:
            logger.warning("Could not auto-seed or reconcile demo sources: %s", exc)

    @classmethod
    def get_setting(cls, key: str, default: str | None = None) -> str | None:
        doc = cls.get_db()[cls.SYS_SETTINGS].find_one({"key": key})
        return doc["value"] if doc and "value" in doc else default

    @classmethod
    def set_setting(cls, key: str, value: str) -> None:
        cls.get_db()[cls.SYS_SETTINGS].update_one(
            {"key": key},
            {"$set": {"key": key, "value": value, "updated_at": datetime.datetime.now(datetime.UTC).isoformat()}},
            upsert=True,
        )

    @classmethod
    def set_active_source(cls, source_id: str) -> None:
        cls._active_source_id = source_id
        cls.set_setting("active_source_id", source_id)
        try:
            from app.services.dataset_intelligence import DatasetIntelligenceService

            DatasetIntelligenceService._catalog_cache.clear()
        except Exception:
            pass

    @classmethod
    def get_active_source_id(cls) -> str | None:
        if cls._active_source_id:
            return cls._active_source_id
        saved = cls.get_setting("active_source_id")
        if saved:
            cls._active_source_id = saved
            return saved
        first_src = cls.get_db()[cls.SYS_SOURCES].find_one(
            {"status": "ready", "detected_format": {"$nin": ["pdf", "txt", "markdown"]}},
            sort=[("uploaded_at", pymongo.DESCENDING)],
        )
        if first_src:
            return first_src["source_id"]
        return None

    @classmethod
    def list_user_collections(cls, source_id: str | None = None) -> list[str]:
        db = cls.get_db()
        sid = source_id or cls.get_active_source_id()
        if sid:
            src = db[cls.SYS_SOURCES].find_one({"source_id": sid})
            if src and src.get("collections"):
                return [c for c in src["collections"] if not c.startswith("_")]
            metas = list(
                db[cls.SYS_COLLECTIONS_METADATA].find(
                    {"source_id": sid}, {"collection_name": 1}
                )
            )
            if metas:
                return [m["collection_name"] for m in metas if not m["collection_name"].startswith("_")]
            phys_db_name = cls.resolve_physical_database_name(sid)
            if phys_db_name != cls._db_name:
                raw_target_db = cls.get_client()[phys_db_name]
                return [
                    c
                    for c in raw_target_db.list_collection_names()
                    if not c.startswith("_") and not c.startswith("system.")
                ]

        all_metas = list(db[cls.SYS_COLLECTIONS_METADATA].find({}, {"collection_name": 1}))
        if all_metas:
            seen = []
            for m in all_metas:
                c = m["collection_name"]
                if c not in seen and not c.startswith("_"):
                    seen.append(c)
            return seen

        raw_db = cls.get_client()[cls._db_name]
        return [
            c
            for c in raw_db.list_collection_names()
            if c not in cls.SYSTEM_COLLECTIONS and not c.startswith("system.")
        ]

