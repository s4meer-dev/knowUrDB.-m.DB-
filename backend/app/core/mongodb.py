import datetime
import logging
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import mongomock
import pymongo
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger("knowurdb.mongodb")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class MongoIsolationSafetyError(RuntimeError):
    """Raised when knowUrDB detects an unsafe connection to a shared MongoDB instance (e.g. port 27017)."""


class _SysCollectionProxy:
    """
    Virtualizes internal control-plane collections (`_sys_collections_metadata`,
    `_sys_query_history`, `_sys_document_chunks`, `_sys_settings`, `_sys_workspaces`)
    into the physical `_system` collection inside `knowurdb`.
    Meanwhile, `datasets`, `sources`, and `generations` exist as dedicated first-class
    collections inside `knowurdb` (`knowurdb.datasets`, `knowurdb.sources`, `knowurdb.generations`).
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
    - `datasets`, `sources` (or `_sys_sources`), and `generations` ALWAYS route to the physical
      `knowurdb.datasets`, `knowurdb.sources`, and `knowurdb.generations` collections inside `knowurdb`.
    - Internal `_sys_*` keys route to `_SysCollectionProxy(sys_raw_db['_system'], key)`.
    - User dataset collections (`patients`, `students`, `subscribers`, etc.) route directly to `raw_db[name]`.
    """

    def __init__(self, raw_db: Database, sys_raw_db: Database | None = None):
        self._raw_db = raw_db
        self._sys_raw_db = sys_raw_db if sys_raw_db is not None else raw_db

    def __getitem__(self, name: str) -> Any:
        if name in ("sources", "_sys_sources"):
            return self._sys_raw_db["sources"]
        if name in ("datasets", "_sys_datasets"):
            return self._sys_raw_db["datasets"]
        if name in ("generations", "_sys_generations"):
            return self._sys_raw_db["generations"]
        if name in MongoDBManager.VIRTUAL_SYSTEM_COLLECTIONS:
            return _SysCollectionProxy(self._sys_raw_db[MongoDBManager.PHYSICAL_SYSTEM_COLLECTION], name)
        return self._raw_db[name]

    def __getattr__(self, item: str) -> Any:
        return getattr(self._raw_db, item)


class MongoDBManager:
    """
    Centralized MongoDB connection & multi-database isolation manager for KnowUrDB.
    - Connects exclusively to the dedicated KnowUrDB MongoDB instance (`mongodb://127.0.0.1:27018` by default).
    - Enforces a Connection Safety Guard preventing accidental writes to shared `localhost:27017`.
    - Control database `knowurdb` contains ONLY registry/control collections:
      `datasets`, `sources`, `generations`, and `_system`.
    - Every generated demo dataset (`demo_healthcare_xxxx`, `demo_education_xxxx`, etc.) lives in its
      own independent MongoDB database on the dedicated instance.
    """

    _client: pymongo.MongoClient | mongomock.MongoClient | None = None
    _db_name: str = settings.MONGODB_CONTROL_DB or settings.MONGODB_DATABASE or "knowurdb"
    _is_mock: bool = False
    _active_source_id: str | None = None

    PHYSICAL_SYSTEM_COLLECTION = "_system"
    SYS_DATASETS = "datasets"
    SYS_SOURCES = "sources"
    SYS_GENERATIONS = "generations"

    SYS_WORKSPACES = "_sys_workspaces"
    SYS_COLLECTIONS_METADATA = "_sys_collections_metadata"
    SYS_QUERY_HISTORY = "_sys_query_history"
    SYS_DOCUMENT_CHUNKS = "_sys_document_chunks"
    SYS_SETTINGS = "_sys_settings"

    VIRTUAL_SYSTEM_COLLECTIONS = {
        SYS_WORKSPACES,
        SYS_COLLECTIONS_METADATA,
        SYS_QUERY_HISTORY,
        SYS_DOCUMENT_CHUNKS,
        SYS_SETTINGS,
    }

    SYSTEM_COLLECTIONS = {
        PHYSICAL_SYSTEM_COLLECTION,
        SYS_DATASETS,
        SYS_SOURCES,
        "_sys_sources",
        SYS_GENERATIONS,
        *VIRTUAL_SYSTEM_COLLECTIONS,
    }

    @classmethod
    def get_uri_summary(cls) -> str:
        return settings.MONGODB_URI.rstrip("/")

    @classmethod
    def parse_configured_endpoint(cls, uri: str | None = None) -> tuple[str, int, str]:
        parsed = urlparse(uri or settings.MONGODB_URI)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 27018
        return host, port, cls._db_name

    @classmethod
    def validate_connection_isolation(cls, uri: str | None = None) -> dict[str, Any]:
        """
        Connection Safety Guard (Sections 8 & 9):
        Verifies MongoDB host, port, and control database before performing write/destructive operations.
        Refuses to operate on shared port 27017 unless ALLOW_SHARED_MONGODB_27017 is explicitly True.
        """
        host, port, control_db = cls.parse_configured_endpoint(uri)
        if port == 27017 and not settings.ALLOW_SHARED_MONGODB_27017:
            raise MongoIsolationSafetyError(
                f"Unsafe MongoDB configuration — Connection Safety Guard: KnowUrDB cannot connect to {host}:{port}, "
                "which is reserved for other local projects. Please use the dedicated KnowUrDB "
                "MongoDB instance on localhost:27018 (MONGODB_URI=mongodb://localhost:27018)."
            )
        return {
            "host": host,
            "port": port,
            "uri": uri or settings.MONGODB_URI,
            "control_database": control_db,
            "isolated": port != 27017,
        }

    @classmethod
    def _ensure_dedicated_mongod_running(cls, host: str, port: int) -> None:
        """
        If KnowUrDB is configured for its dedicated local port (e.g. 27018) and nothing is
        listening yet (e.g. Docker is not running), automatically launches a dedicated local
        `mongod` process bound to `127.0.0.1:27018` with persistent storage in `.mongodb_27018/data`.
        """
        if host not in ("127.0.0.1", "localhost") or port == 27017:
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return

        # Locate local mongod binary
        candidates: list[Path] = []
        prog_files = Path("C:/Program Files/MongoDB/Server")
        if prog_files.exists():
            candidates.extend(sorted(prog_files.glob("*/bin/mongod.exe"), reverse=True))
        for p in ("/usr/bin/mongod", "/usr/local/bin/mongod", "/opt/homebrew/bin/mongod"):
            if Path(p).exists():
                candidates.append(Path(p))

        if not candidates:
            return

        mongod_bin = str(candidates[0])
        data_dir = PROJECT_ROOT / f".mongodb_{port}" / "data"
        log_dir = PROJECT_ROOT / f".mongodb_{port}" / "logs"
        data_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "mongod.log"

        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(
                [
                    mongod_bin,
                    "--port",
                    str(port),
                    "--bind_ip",
                    "127.0.0.1",
                    "--dbpath",
                    str(data_dir),
                    "--logpath",
                    str(log_file),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            for _ in range(15):
                time.sleep(0.2)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.3)
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        logger.info("Started dedicated KnowUrDB mongod instance on 127.0.0.1:%d", port)
                        break
        except Exception as exc:
            logger.warning("Failed auto-starting dedicated mongod on port %d: %s", port, exc)

    @classmethod
    def get_client(cls) -> pymongo.MongoClient | mongomock.MongoClient:
        cls.validate_connection_isolation()
        if cls._client is None:
            host, port, _ = cls.parse_configured_endpoint()
            cls._ensure_dedicated_mongod_running(host, port)
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
                    "Connected to dedicated KnowUrDB MongoDB server at %s (control_db=%s)",
                    settings.MONGODB_URI,
                    cls._db_name,
                )
            except Exception as exc:
                logger.warning(
                    "Dedicated MongoDB server at %s unreachable (%s); activating embedded mongomock fallback.",
                    settings.MONGODB_URI,
                    exc,
                )
                cls._client = mongomock.MongoClient()
                cls._is_mock = True
        return cls._client

    _initialized: bool = False
    _initializing: bool = False

    @classmethod
    def get_db(cls, db_name: str | None = None) -> Any:
        """Returns the requested MongoDB database wrapped with the central `knowurdb` registry facade."""
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
        - For any generated or demo dataset (`demo_healthcare_34cf`, `demo_database`, etc.),
          returns that dataset's independent physical MongoDB database name.
        - Never queries `knowurdb` for dataset records unless the source is an uploaded CSV/JSON file
          explicitly stored inside `knowurdb`.
        """
        sid = source_id or cls.get_active_source_id()
        if not sid:
            return cls._db_name

        if sid == "demo-source-id":
            return "demo_database"
        if sid.startswith("mongodb_demo_"):
            return sid.replace("mongodb_", "", 1)

        sys_db = cls.get_db()
        src = sys_db[cls.SYS_SOURCES].find_one({"source_id": sid})
        if src:
            phys_db = src.get("physical_database")
            if phys_db and isinstance(phys_db, str) and not phys_db.startswith("knowurdb"):
                return phys_db
            db_name = src.get("database_name")
            if db_name and isinstance(db_name, str) and "/" not in db_name and db_name != cls._db_name:
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
        Determines how a logical collection (`patients`, `products`, `customers`, etc.)
        is stored in its target MongoDB database.
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

            phys_db_name = cls.resolve_physical_database_name(sid)
            if phys_db_name != cls._db_name:
                raw_target_db = cls.get_client()[phys_db_name]
                if table_name in raw_target_db.list_collection_names():
                    return table_name, False

        meta_any = sys_db[cls.SYS_COLLECTIONS_METADATA].find_one({"collection_name": table_name})
        if meta_any and meta_any.get("container_collection"):
            return meta_any["container_collection"], bool(meta_any.get("is_grouped", False))

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
        host, port, control_db = cls.parse_configured_endpoint()
        try:
            cls.validate_connection_isolation()
            client = cls.get_client()
            res = client.admin.command("ping")
            version = "mongomock" if cls._is_mock else client.server_info().get("version", "unknown")
            return {
                "connected": bool(res.get("ok") == 1.0),
                "engine": "mongomock" if cls._is_mock else "mongodb",
                "version": version,
                "database": control_db,
                "host": host,
                "port": port,
                "uri": settings.MONGODB_URI,
            }
        except Exception as exc:
            logger.error("MongoDB ping failed: %s", exc)
            return {
                "connected": False,
                "engine": "mongodb",
                "database": control_db,
                "host": host,
                "port": port,
                "uri": settings.MONGODB_URI,
                "error": (
                    f"KnowUrDB could not connect to its dedicated MongoDB instance on {host}:{port}. ({exc})"
                ),
            }

    @classmethod
    def init_db(cls) -> None:
        """
        Initializes ONLY the control-plane registry collections inside `knowurdb`:
          - `knowurdb.datasets`
          - `knowurdb.sources`
          - `knowurdb.generations`
          - `knowurdb._system`
        NEVER automatically generates a demo dataset on startup (Sections 22, 23, 57, 58).
        """
        cls.validate_connection_isolation()
        db = cls.get_db()
        raw_db = cls.get_client()[cls._db_name]

        # Ensure control-plane collections exist and have unique indexes
        existing_cols = set(raw_db.list_collection_names())
        for control_col in (cls.SYS_DATASETS, cls.SYS_SOURCES, cls.SYS_GENERATIONS, cls.PHYSICAL_SYSTEM_COLLECTION):
            if control_col not in existing_cols:
                try:
                    raw_db.create_collection(control_col)
                except Exception:
                    pass

        try:
            raw_db[cls.PHYSICAL_SYSTEM_COLLECTION].create_index("_sys_type")
            raw_db[cls.SYS_DATASETS].create_index("dataset_id", unique=True)
            raw_db[cls.SYS_DATASETS].create_index("database_name", unique=True)
            raw_db[cls.SYS_SOURCES].create_index("source_id", unique=True)
            raw_db[cls.SYS_GENERATIONS].create_index("generation_id", unique=True)
        except Exception:
            pass

        # Clean up any legacy duplicate `demo_database` collection inside `knowurdb`
        if "demo_database" in existing_cols:
            try:
                raw_db["demo_database"].drop()
            except Exception:
                pass

        if db[cls.SYS_WORKSPACES].count_documents({"workspace_id": "default"}) == 0:
            db[cls.SYS_WORKSPACES].insert_one(
                {
                    "workspace_id": "default",
                    "name": "Default Intelligence Workspace",
                    "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )

        # Read-only reconciliation of existing managed `demo_*` databases in this MongoDB instance
        # (NEVER generates new demo data on startup!)
        try:
            from app.services.demo_generator import DemoGenerator

            DemoGenerator().reconcile_managed_databases()
        except Exception as exc:
            logger.warning("Startup dataset registry reconciliation warning: %s", exc)

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
            # Verify active_source_id still exists in knowurdb.sources
            exists = cls.get_db()[cls.SYS_SOURCES].find_one({"source_id": cls._active_source_id})
            if exists:
                return cls._active_source_id
            cls._active_source_id = None
        saved = cls.get_setting("active_source_id")
        if saved:
            exists = cls.get_db()[cls.SYS_SOURCES].find_one({"source_id": saved})
            if exists:
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
