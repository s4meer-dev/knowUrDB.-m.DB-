import os
from pathlib import Path
import json

class FileFormat:
    SQLITE = "sqlite"
    MYSQL_DUMP = "mysql_dump"
    POSTGRES_DUMP = "postgres_dump"
    GENERIC_SQL = "generic_sql"
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    JSONL = "jsonl"
    EXCEL = "excel"
    PARQUET = "parquet"
    DUCKDB = "duckdb"
    UNSUPPORTED = "unsupported"

class FileDetector:
    @staticmethod
    def detect_format(file_path: str, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        
        # 1. Extension-based checks
        if ext in [".db", ".sqlite", ".sqlite3"]:
            # Need to verify if it's sqlite or duckdb
            return FileDetector._inspect_binary(file_path)
        elif ext == ".duckdb":
            return FileFormat.DUCKDB
        elif ext == ".csv":
            return FileFormat.CSV
        elif ext == ".tsv":
            return FileFormat.TSV
        elif ext == ".json":
            return FileFormat.JSON
        elif ext in [".jsonl", ".ndjson"]:
            return FileFormat.JSONL
        elif ext in [".xlsx", ".xls"]:
            return FileFormat.EXCEL
        elif ext == ".parquet":
            return FileFormat.PARQUET
        elif ext == ".sql":
            return FileDetector._inspect_sql(file_path)
        
        # Fallback to binary inspection if extension is unknown
        return FileDetector._inspect_binary(file_path)

    @staticmethod
    def _inspect_binary(file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                header = f.read(16)
                if header.startswith(b"SQLite format 3\x00"):
                    return FileFormat.SQLITE
                if header.startswith(b"DUCK"):
                    return FileFormat.DUCKDB
                if header.startswith(b"PAR1"):
                    return FileFormat.PARQUET
        except Exception:
            pass
        return FileFormat.UNSUPPORTED

    @staticmethod
    def _inspect_sql(file_path: str) -> str:
        # Read the first few lines to guess dialect
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(8192).lower()
                
                # Check for MySQL specifics
                if "engine=" in content or "auto_increment" in content or "mysql" in content or "lock tables" in content or "create database" in content:
                    return FileFormat.MYSQL_DUMP
                
                # Check for Postgres specifics
                if "pg_catalog" in content or "postgresql" in content or "set search_path" in content or "bigserial" in content:
                    return FileFormat.POSTGRES_DUMP
                
                # Otherwise, generic SQL
                return FileFormat.GENERIC_SQL
        except Exception:
            return FileFormat.GENERIC_SQL
