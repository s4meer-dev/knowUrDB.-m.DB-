import os
import sqlite3
import uuid
from pathlib import Path
from app.services.ingestion.detectors import FileDetector, FileFormat
from app.services.ingestion.converters import FormatConverter, ConversionError

class IngestionPipeline:
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def process_file(self, file_path: str, original_filename: str) -> dict:
        """
        Process the uploaded file and return the final SQLite database path and metadata.
        """
        # 1. Detect format
        format_type = FileDetector.detect_format(file_path, original_filename)
        
        if format_type == FileFormat.UNSUPPORTED:
            raise ValueError(f"File format is not currently supported or is corrupted: {original_filename}")

        # 2. Convert to internal queryable database (SQLite)
        unique_id = uuid.uuid4().hex[:8]
        dest_db_name = f"{unique_id}_internal.db"
        dest_db_path = str(self.upload_dir / dest_db_name)

        try:
            FormatConverter.convert_to_sqlite(file_path, format_type, dest_db_path)
        except ConversionError as e:
            if Path(dest_db_path).exists():
                Path(dest_db_path).unlink()
            raise ValueError(str(e))

        # 3. Validate final SQLite DB and get basic stats
        try:
            with sqlite3.connect(f"file:{Path(dest_db_path).absolute().as_posix()}?mode=ro", uri=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
                
                table_count = len(tables)
                record_count = 0
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                        record_count += cursor.fetchone()[0]
                    except Exception:
                        pass
        except Exception as e:
            if Path(dest_db_path).exists():
                Path(dest_db_path).unlink()
            raise ValueError(f"Invalid generated SQLite database: {e}")

        return {
            "status": "success",
            "format": format_type,
            "dialect": format_type, # simplify for now
            "table_count": table_count,
            "record_count": record_count,
            "path": dest_db_path,
            "name": original_filename
        }
