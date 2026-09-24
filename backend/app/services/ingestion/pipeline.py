import uuid
from pathlib import Path

from app.services.ingestion.converters import ConversionError, FormatConverter
from app.services.ingestion.detectors import FileDetector, FileFormat


class IngestionPipeline:
    """
    MongoDB-native data ingestion pipeline.
    Detects file format, normalizes records, models embedded documents/arrays,
    inserts documents into MongoDB collections, and creates intelligent indexes.
    """

    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir) if upload_dir else Path("database/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def process_file(
        self, file_path: str, original_filename: str, source_id: str | None = None
    ) -> dict:
        format_type = FileDetector.detect_format(file_path, original_filename)

        if format_type == FileFormat.UNSUPPORTED:
            raise ValueError(
                f"File format is not currently supported or is corrupted: {original_filename}"
            )

        sid = source_id or f"src-{uuid.uuid4().hex[:8]}"

        try:
            conversion_result = FormatConverter.convert_to_mongodb(
                file_path=file_path,
                format_type=format_type,
                source_id=sid,
                original_filename=original_filename,
            )
        except ConversionError as exc:
            raise ValueError(str(exc)) from exc

        return {
            "status": "success",
            "format": format_type,
            "dialect": "mongodb",
            "database_name": conversion_result["database_name"],
            "collections": conversion_result["collections"],
            "table_count": conversion_result["table_count"],
            "record_count": conversion_result["record_count"],
            "index_count": conversion_result.get("index_count", 1),
            "path": f"mongodb://localhost:27017/{conversion_result['database_name']}",
            "name": original_filename,
        }
