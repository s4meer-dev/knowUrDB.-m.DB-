import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.core.app_database import app_db_provider
from app.models.source import SourceMetadata, SourceStatus, SourceType
from app.services.ingestion.detectors import FileDetector, FileFormat
from app.services.ingestion.pipeline import IngestionPipeline

# For now we use the same upload dir logic, but properly tracked
STORAGE_DIR = Path(__file__).parent.parent.parent.parent / "database" / "storage"

class SourceManager:
    """
    Manages the lifecycle, storage, and registry of all uploaded sources.
    """

    def __init__(self, db_provider=app_db_provider):
        self.db = db_provider
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.ingestion_pipeline = IngestionPipeline(str(STORAGE_DIR / "temp"))

    def _determine_source_type(self, format_type: str) -> SourceType:
        if format_type in [FileFormat.PDF, FileFormat.TXT, FileFormat.MARKDOWN]:
            return SourceType.DOCUMENT
        return SourceType.RELATIONAL  # We can extend for tabular, etc.

    def register_source(self, original_filename: str, file_path: str, mime_type: str, size_bytes: int) -> SourceMetadata:
        """
        Register a new source. It moves the file to an isolated storage location and
        processes it based on its type.
        """
        source_id = f"src_{uuid.uuid4().hex}"
        source_dir = STORAGE_DIR / "sources" / source_id
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Move original file to source dir
        original_file_dest = source_dir / original_filename
        shutil.copy2(file_path, original_file_dest)

        format_type = FileDetector.detect_format(str(original_file_dest), original_filename)
        source_type = self._determine_source_type(format_type)

        now = datetime.utcnow().isoformat() + "Z"
        metadata = SourceMetadata(
            source_id=source_id,
            name=original_filename,
            original_filename=original_filename,
            file_type=os.path.splitext(original_filename)[1].lower(),
            mime_type=mime_type,
            detected_format=format_type,
            size_bytes=size_bytes,
            uploaded_at=now,
            status=SourceStatus.ANALYZING,
            storage_location=str(source_dir)
        )

        self._save_metadata(metadata)

        # Trigger processing (In a real system, this could be async/Celery)
        try:
            if source_type == SourceType.RELATIONAL:
                result = self.ingestion_pipeline.process_file(str(original_file_dest), original_filename)
                
                # Move the generated SQLite database to the source directory
                generated_db_path = result["path"]
                final_db_name = f"{source_id}_internal.db"
                final_db_dest = source_dir / final_db_name
                shutil.move(generated_db_path, final_db_dest)
                
                metadata.table_count = result["table_count"]
                metadata.record_count = result["record_count"]
                metadata.detected_dialect = result["dialect"]
                metadata.status = SourceStatus.READY
            elif source_type == SourceType.DOCUMENT:
                from app.services.document_processor import DocumentProcessor
                from app.services.gemini_provider import GeminiProvider
                ai = GeminiProvider()
                dp = DocumentProcessor(ai)
                dp.process_document(str(original_file_dest), source_id, original_filename)
                metadata.status = SourceStatus.READY
            
            self._save_metadata(metadata)
        except Exception as e:
            metadata.status = SourceStatus.FAILED
            metadata.error_message = str(e)
            self._save_metadata(metadata)

        return metadata

    def get_source(self, source_id: str) -> Optional[SourceMetadata]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,))
            row = cursor.fetchone()
            if row:
                return SourceMetadata(**dict(row))
            return None

    def list_sources(self) -> List[SourceMetadata]:
        sources = []
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM sources ORDER BY uploaded_at DESC")
            for row in cursor.fetchall():
                sources.append(SourceMetadata(**dict(row)))
        return sources

    def delete_source(self, source_id: str):
        metadata = self.get_source(source_id)
        if not metadata:
            return

        with self.db.get_connection() as conn:
            conn.execute("UPDATE sources SET status = ? WHERE source_id = ?", (SourceStatus.DELETING, source_id))
            conn.commit()

        # Delete from disk
        source_dir = Path(metadata.storage_location)
        if source_dir.exists():
            shutil.rmtree(source_dir)

        # Delete from DB
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
            conn.commit()

    def _save_metadata(self, metadata: SourceMetadata):
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sources (
                    source_id, name, original_filename, file_type, mime_type,
                    detected_format, detected_dialect, size_bytes, uploaded_at,
                    status, table_count, record_count, schema_summary, storage_location, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.source_id, metadata.name, metadata.original_filename,
                    metadata.file_type, metadata.mime_type, metadata.detected_format,
                    metadata.detected_dialect, metadata.size_bytes, metadata.uploaded_at,
                    metadata.status.value, metadata.table_count, metadata.record_count,
                    metadata.schema_summary, metadata.storage_location, metadata.error_message
                )
            )
            conn.commit()

    def get_internal_db_path(self, source_id: str) -> str:
        source = self.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        # If storage_location is already a file (e.g. demo db), use it
        storage_path = Path(source.storage_location)
        if storage_path.is_file():
            expected_path = storage_path
        else:
            expected_path = storage_path / f"{source_id}_internal.db"
            
        if not expected_path.exists():
            raise ValueError(f"Internal database for source {source_id} not found")
        return str(expected_path)
