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


class MongoDBManager:
    """
    Centralized MongoDB connection, pooling, database-folder isolation, and system registry.
    - System metadata (_sys_*) is isolated in `knowurdb_system` (or settings.MONGODB_DATABASE).
    - Demo database collections (`products`, `customers`, `orders`, `employees`, `students`)
      are cleanly grouped inside their own `knowurdb_demo` database folder in MongoDB Compass.
    - Each uploaded dataset is organized into its own `knowurdb_<dataset>` database folder
      in MongoDB Compass with clean, unprefixed collection names.
    """

    _client: pymongo.MongoClient | mongomock.MongoClient | None = None
    _db_name: str = (
        "knowurdb_system"
        if settings.MONGODB_DATABASE == "knowurdb"
        else settings.MONGODB_DATABASE
    )
    _is_mock: bool = False
    _active_source_id: str | None = None
    _source_db_cache: dict[str, str] = {}

    DEMO_DB_NAME = "knowurdb_demo"

    # System Collection Names (stored inside _db_name / knowurdb_system)
    SYS_WORKSPACES = "_sys_workspaces"
    SYS_SOURCES = "_sys_sources"
    SYS_COLLECTIONS_METADATA = "_sys_collections_metadata"
    SYS_QUERY_HISTORY = "_sys_query_history"
    SYS_DOCUMENT_CHUNKS = "_sys_document_chunks"
    SYS_SETTINGS = "_sys_settings"

    SYSTEM_COLLECTIONS = {
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
                    "Connected to live MongoDB server at %s (system_db=%s)",
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
    def get_db(cls, db_name: str | None = None) -> Database:
        """Returns the system metadata database (`knowurdb_system`) or an explicit database."""
        client = cls.get_client()
        db = client[db_name or cls._db_name]
        if not cls._initialized and not cls._initializing and db_name is None:
            cls._initializing = True
            try:
                cls.init_db()
                cls._initialized = True
            finally:
                cls._initializing = False
        return db

    @classmethod
    def allocate_source_db_name(cls, raw_label: str, source_id: str) -> str:
        """
        Allocates a clean, human-readable MongoDB database folder name for MongoDB Compass.
        - Demo source -> `knowurdb_demo` (or `knowurdb_test_demo` in test mode)
        - Uploaded file `brands.csv` -> `knowurdb_brands` (or `knowurdb_brands_2` if collision)
        """
        is_test = "test" in cls._db_name.lower()
        prefix = "knowurdb_test" if is_test else "knowurdb"

        if source_id == "demo-source-id" or raw_label.lower().startswith("demo"):
            db_name = f"{prefix}_demo"
            cls._source_db_cache[source_id] = db_name
            return db_name

        clean = re.sub(r"[^a-zA-Z0-9_]", "_", raw_label.strip().lower())
        clean = re.sub(r"_+", "_", clean).strip("_")[:32] or "dataset"
        base_db_name = f"{prefix}_{clean}"

        sys_db = cls.get_db()
        existing = sys_db[cls.SYS_SOURCES].find_one(
            {"database_name": base_db_name, "source_id": {"$ne": source_id}}
        )
        if not existing:
            cls._source_db_cache[source_id] = base_db_name
            return base_db_name

        suffix = 2
        while True:
            candidate = f"{base_db_name}_{suffix}"
            clash = sys_db[cls.SYS_SOURCES].find_one(
                {"database_name": candidate, "source_id": {"$ne": source_id}}
            )
            if not clash:
                cls._source_db_cache[source_id] = candidate
                return candidate
            suffix += 1

    @classmethod
    def get_source_db_name(cls, source_id: str | None = None) -> str:
        sid = source_id or cls.get_active_source_id() or "demo-source-id"
        if sid in cls._source_db_cache:
            return cls._source_db_cache[sid]

        sys_db = cls.get_db()
        src = sys_db[cls.SYS_SOURCES].find_one({"source_id": sid})
        if src and src.get("database_name"):
            db_name = src["database_name"]
            cls._source_db_cache[sid] = db_name
            return db_name

        is_test = "test" in cls._db_name.lower()
        default_demo = "knowurdb_test_demo" if is_test else cls.DEMO_DB_NAME
        if sid == "demo-source-id" or sid.startswith("demo-"):
            return default_demo
        return cls._db_name

    @classmethod
    def get_source_db(cls, source_id: str | None = None) -> Database:
        """
        Returns the dedicated MongoDB Database folder for the specified (or active) data source.
        """
        db_name = cls.get_source_db_name(source_id)
        return cls.get_client()[db_name]

    @classmethod
    def drop_source_db(cls, source_id: str, db_name: str | None = None) -> None:
        """
        Drops the dedicated MongoDB Database folder when a source is deleted,
        keeping MongoDB Compass completely clean.
        """
        target_db = db_name or cls.get_source_db_name(source_id)
        cls._source_db_cache.pop(source_id, None)
        if target_db and target_db != cls._db_name:
            try:
                cls.get_client().drop_database(target_db)
            except Exception as exc:
                logger.warning("Failed to drop source database %s: %s", target_db, exc)

    @classmethod
    def set_database_name(cls, db_name: str) -> None:
        cls._db_name = db_name
        cls._source_db_cache.clear()
        cls._initialized = False

    @classmethod
    def reset_client(cls, use_mock: bool = False, db_name: str | None = None) -> None:
        if cls._client is not None:
            try:
                cls._client.close()
            except Exception:
                pass
        cls._client = None
        cls._source_db_cache.clear()
        if db_name:
            cls._db_name = db_name
        if use_mock:
            cls._client = mongomock.MongoClient()
            cls._is_mock = True

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
                "demo_database": cls.DEMO_DB_NAME,
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
        Idempotently initializes system collections in `knowurdb_system`, indexes, default workspace,
        and seeds the default MongoDB Demo Database inside `knowurdb_demo` if no sources exist.
        """
        db = cls.get_db()

        # 1. Create indexes on system collections
        db[cls.SYS_SOURCES].create_index("source_id", unique=True)
        db[cls.SYS_SOURCES].create_index("status")
        db[cls.SYS_SOURCES].create_index([("uploaded_at", pymongo.DESCENDING)])

        db[cls.SYS_COLLECTIONS_METADATA].create_index(
            [("source_id", pymongo.ASCENDING), ("collection_name", pymongo.ASCENDING)],
            unique=True,
        )
        db[cls.SYS_COLLECTIONS_METADATA].create_index("collection_name")

        db[cls.SYS_QUERY_HISTORY].create_index("id", unique=True)
        db[cls.SYS_QUERY_HISTORY].create_index([("created_at", pymongo.DESCENDING)])
        db[cls.SYS_QUERY_HISTORY].create_index("source_id")

        db[cls.SYS_DOCUMENT_CHUNKS].create_index("source_id")
        db[cls.SYS_DOCUMENT_CHUNKS].create_index("chunk_id", unique=True)

        db[cls.SYS_SETTINGS].create_index("key", unique=True)

        # 2. Ensure default workspace exists
        if db[cls.SYS_WORKSPACES].count_documents({"workspace_id": "default"}) == 0:
            db[cls.SYS_WORKSPACES].insert_one(
                {
                    "workspace_id": "default",
                    "name": "Default Intelligence Workspace",
                    "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )

        # 3. Ensure initial demo source is seeded if no sources exist
        if db[cls.SYS_SOURCES].count_documents({}) == 0:
            try:
                from app.services.demo_generator import DemoGenerator

                DemoGenerator().seed_initial_demo_if_empty()
            except Exception as exc:
                logger.warning("Could not auto-seed initial demo source: %s", exc)

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
        sys_db = cls.get_db()
        sid = source_id or cls.get_active_source_id()
        if sid:
            metas = list(
                sys_db[cls.SYS_COLLECTIONS_METADATA].find(
                    {"source_id": sid}, {"collection_name": 1}
                )
            )
            if metas:
                return [m["collection_name"] for m in metas]
            src = sys_db[cls.SYS_SOURCES].find_one({"source_id": sid})
            if src and src.get("collections"):
                return list(src["collections"])

        source_db = cls.get_source_db(sid)
        all_cols = source_db.list_collection_names()
        return [
            c
            for c in all_cols
            if not c.startswith("_sys_") and not c.startswith("system.")
        ]
