import datetime
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import pymongo

from app.core.mongodb import MongoDBManager
from app.models.source import SourceMetadata, SourceStatus, SourceType
from app.services.document_processor import DocumentProcessor
from app.services.ingestion.detectors import FileDetector, FileFormat
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.schema_service import MongoSchemaService


class SourceManager:
    """
    Manages the lifecycle of all uploaded datasets, MongoDB collections, and RAG documents.
    Backed by MongoDB system collection `_sys_sources`.
    """

    def __init__(self, storage_dir: str | None = None):
        base = Path(__file__).resolve().parent.parent.parent.parent
        self.storage_dir = Path(storage_dir) if storage_dir else (base / "database" / "sources")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = IngestionPipeline(str(self.storage_dir))
        self.schema_service = MongoSchemaService()
        self.doc_processor = DocumentProcessor()

    def _determine_source_type(self, detected_format: str) -> SourceType:
        if detected_format in (FileFormat.PDF, FileFormat.TXT, FileFormat.MARKDOWN, "pdf", "txt", "markdown"):
            return SourceType.DOCUMENT
        return SourceType.RELATIONAL

    def list_sources(self) -> list[SourceMetadata]:
        db = MongoDBManager.get_db()
        docs = list(
            db[MongoDBManager.SYS_SOURCES].find(
                {"status": {"$ne": SourceStatus.DELETED.value}},
                sort=[("uploaded_at", pymongo.DESCENDING)],
            )
        )
        return [
            SourceMetadata(**{k: v for k, v in d.items() if k != "_id"})
            for d in docs
        ]

    def get_source(self, source_id: str) -> SourceMetadata | None:
        db = MongoDBManager.get_db()
        doc = db[MongoDBManager.SYS_SOURCES].find_one({"source_id": source_id})
        if not doc:
            return None
        return SourceMetadata(**{k: v for k, v in doc.items() if k != "_id"})

    def get_internal_db_path(self, source_id: str) -> str:
        """
        Returns the source_id or storage identifier for setting the active MongoDB context.
        """
        src = self.get_source(source_id)
        if not src:
            raise ValueError(f"Source '{source_id}' not found.")
        return src.source_id

    def register_source(
        self,
        original_filename: str,
        file_path: str,
        mime_type: str,
        size_bytes: int,
    ) -> SourceMetadata:
        db = MongoDBManager.get_db()
        source_id = f"src-{uuid.uuid4().hex[:8]}"
        ext = os.path.splitext(original_filename)[1].lower() or ".dat"
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()

        detected_format = FileDetector.detect_format(file_path, original_filename)
        if detected_format == FileFormat.UNSUPPORTED:
            raise ValueError(f"Unsupported or corrupted file format: {original_filename}")

        source_type = self._determine_source_type(detected_format)

        if source_type == SourceType.DOCUMENT:
            # Store document file & ingest RAG chunks + embeddings into MongoDB
            dest_dir = self.storage_dir / source_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / original_filename
            shutil.copy2(file_path, dest_file)

            doc_stats = self.doc_processor.ingest_document(
                source_id=source_id,
                file_path=str(dest_file),
                filename=original_filename,
            )

            source_doc: dict[str, Any] = {
                "source_id": source_id,
                "name": original_filename,
                "original_filename": original_filename,
                "file_type": ext,
                "mime_type": mime_type,
                "detected_format": detected_format,
                "detected_dialect": "rag-vector",
                "size_bytes": size_bytes,
                "uploaded_at": now_iso,
                "status": SourceStatus.READY.value,
                "collections": [MongoDBManager.SYS_DOCUMENT_CHUNKS],
                "table_count": 1,
                "record_count": doc_stats["chunk_count"],
                "index_count": 2,
                "schema_summary": (
                    f"RAG Document '{original_filename}': {doc_stats['page_count']} pages/sections, {doc_stats['chunk_count']} vector-indexed chunks in MongoDB."
                ),
                "storage_location": str(dest_file),
            }
        else:
            # Structured / Tabular / Database migration into native MongoDB collections
            ingestion_info = self.pipeline.process_file(
                file_path=file_path,
                original_filename=original_filename,
                source_id=source_id,
            )
            MongoDBManager.set_active_source(source_id)
            schema_summary = self.schema_service.get_schema_summary(source_id).summary

            db_name = ingestion_info["database_name"]
            source_doc = {
                "source_id": source_id,
                "name": original_filename,
                "original_filename": original_filename,
                "file_type": ext,
                "mime_type": mime_type,
                "detected_format": detected_format,
                "detected_dialect": "mongodb",
                "size_bytes": size_bytes,
                "uploaded_at": now_iso,
                "status": SourceStatus.READY.value,
                "database_name": db_name,
                "collections": ingestion_info["collections"],
                "table_count": ingestion_info["table_count"],
                "record_count": ingestion_info["record_count"],
                "index_count": ingestion_info.get("index_count", 1),
                "schema_summary": schema_summary,
                "storage_location": f"mongodb://localhost:27017/{db_name}",
            }

        db[MongoDBManager.SYS_SOURCES].update_one(
            {"source_id": source_id},
            {"$set": source_doc},
            upsert=True,
        )
        return SourceMetadata(**source_doc)

    def delete_source(self, source_id: str) -> None:
        db = MongoDBManager.get_db()
        src = db[MongoDBManager.SYS_SOURCES].find_one({"source_id": source_id})
        if not src:
            return

        metas = list(db[MongoDBManager.SYS_COLLECTIONS_METADATA].find({"source_id": source_id}))
        for m in metas:
            ccol = m.get("container_collection")
            if ccol and ccol not in MongoDBManager.SYSTEM_COLLECTIONS:
                try:
                    db[ccol].drop()
                except Exception:
                    pass

        for col_name in src.get("collections", []):
            if col_name not in MongoDBManager.SYSTEM_COLLECTIONS:
                try:
                    db[col_name].drop()
                except Exception:
                    pass

        db[MongoDBManager.SYS_COLLECTIONS_METADATA].delete_many({"source_id": source_id})
        db[MongoDBManager.SYS_DOCUMENT_CHUNKS].delete_many({"source_id": source_id})
        db[MongoDBManager.SYS_SOURCES].delete_one({"source_id": source_id})

        local_dir = self.storage_dir / source_id
        if local_dir.exists() and local_dir.is_dir():
            shutil.rmtree(local_dir, ignore_errors=True)
