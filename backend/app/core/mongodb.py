import datetime
import logging
from typing import Any

import mongomock
import pymongo
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger("knowurdb.mongodb")


class MongoDBManager:
    """
    Centralized MongoDB connection, pooling, index management, and system collection registry.
    Connects to the live MongoDB server configured in settings.MONGODB_URI, with an automatic
    fallback to mongomock only if explicitly requested or if no server is reachable in offline CI.
    """

    _client: pymongo.MongoClient | mongomock.MongoClient | None = None
    _db_name: str = settings.MONGODB_DATABASE
    _is_mock: bool = False
    _active_source_id: str | None = None

    # System Collection Names (prefixed with _sys_ so they are never confused with user datasets)
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
                    "Connected to live MongoDB server at %s (db=%s)",
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
        Idempotently initializes system collections, indexes, default workspace,
        and seeds the default MongoDB Demo Database if no sources exist.
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
        # Fallback to first available relational/tabular source
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
        if source_id:
            metas = list(
                db[cls.SYS_COLLECTIONS_METADATA].find(
                    {"source_id": source_id}, {"collection_name": 1}
                )
            )
            if metas:
                return [m["collection_name"] for m in metas]
            src = db[cls.SYS_SOURCES].find_one({"source_id": source_id})
            if src and src.get("collections"):
                return list(src["collections"])

        all_cols = db.list_collection_names()
        return [
            c
            for c in all_cols
            if not c.startswith("_sys_") and not c.startswith("system.")
        ]
