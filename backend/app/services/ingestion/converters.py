import os
import sqlite3
import pandas as pd
import duckdb
import re
from pathlib import Path
from app.services.ingestion.detectors import FileFormat

class ConversionError(Exception):
    pass

class FormatConverter:
    @staticmethod
    def convert_to_sqlite(source_path: str, format_type: str, dest_db_path: str):
        if format_type == FileFormat.SQLITE:
            import shutil
            shutil.copy2(source_path, dest_db_path)
            return

        if format_type == FileFormat.CSV:
            TabularConverter.convert_csv(source_path, dest_db_path)
        elif format_type == FileFormat.TSV:
            TabularConverter.convert_csv(source_path, dest_db_path, sep="\t")
        elif format_type == FileFormat.JSON:
            TabularConverter.convert_json(source_path, dest_db_path, lines=False)
        elif format_type == FileFormat.JSONL:
            TabularConverter.convert_json(source_path, dest_db_path, lines=True)
        elif format_type == FileFormat.EXCEL:
            TabularConverter.convert_excel(source_path, dest_db_path)
        elif format_type == FileFormat.PARQUET:
            TabularConverter.convert_parquet(source_path, dest_db_path)
        elif format_type == FileFormat.DUCKDB:
            DuckDBConverter.convert(source_path, dest_db_path)
        elif format_type == FileFormat.MYSQL_DUMP:
            SQLDumpConverter.convert_mysql(source_path, dest_db_path)
        elif format_type == FileFormat.POSTGRES_DUMP:
            SQLDumpConverter.convert_postgres(source_path, dest_db_path)
        elif format_type == FileFormat.GENERIC_SQL:
            SQLDumpConverter.convert_generic(source_path, dest_db_path)
        else:
            raise ConversionError(f"Unsupported format: {format_type}")

class TabularConverter:
    @staticmethod
    def _sanitize_table_name(name: str) -> str:
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = name.strip('_').lower()
        if not name or name[0].isdigit():
            name = "table_" + name
        return name

    @staticmethod
    def convert_csv(source_path: str, dest_db_path: str, sep=","):
        try:
            df = pd.read_csv(source_path, sep=sep)
            table_name = TabularConverter._sanitize_table_name(Path(source_path).stem)
            with sqlite3.connect(dest_db_path) as conn:
                df.to_sql(table_name, conn, index=False, if_exists="replace")
        except Exception as e:
            raise ConversionError(f"Failed to convert CSV/TSV: {e}")

    @staticmethod
    def convert_json(source_path: str, dest_db_path: str, lines=False):
        try:
            df = pd.read_json(source_path, lines=lines)
            table_name = TabularConverter._sanitize_table_name(Path(source_path).stem)
            with sqlite3.connect(dest_db_path) as conn:
                # pandas handles nested structures sometimes as dicts, stringify them
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                        df[col] = df[col].astype(str)
                df.to_sql(table_name, conn, index=False, if_exists="replace")
        except Exception as e:
            raise ConversionError(f"Failed to convert JSON: {e}")

    @staticmethod
    def convert_excel(source_path: str, dest_db_path: str):
        try:
            xls = pd.ExcelFile(source_path)
            with sqlite3.connect(dest_db_path) as conn:
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    table_name = TabularConverter._sanitize_table_name(sheet_name)
                    df.to_sql(table_name, conn, index=False, if_exists="replace")
        except Exception as e:
            raise ConversionError(f"Failed to convert Excel: {e}")

    @staticmethod
    def convert_parquet(source_path: str, dest_db_path: str):
        try:
            df = pd.read_parquet(source_path)
            table_name = TabularConverter._sanitize_table_name(Path(source_path).stem)
            with sqlite3.connect(dest_db_path) as conn:
                df.to_sql(table_name, conn, index=False, if_exists="replace")
        except Exception as e:
            raise ConversionError(f"Failed to convert Parquet: {e}")

class DuckDBConverter:
    @staticmethod
    def convert(source_path: str, dest_db_path: str):
        try:
            con = duckdb.connect(source_path)
            tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
            with sqlite3.connect(dest_db_path) as sqlite_conn:
                for (table_name,) in tables:
                    df = con.execute(f"SELECT * FROM \"{table_name}\"").df()
                    df.to_sql(table_name, sqlite_conn, index=False, if_exists="replace")
            con.close()
        except Exception as e:
            raise ConversionError(f"Failed to convert DuckDB: {e}")

class SQLDumpConverter:
    @staticmethod
    def convert_mysql(source_path: str, dest_db_path: str):
        # We will use regex to sanitize MySQL dump and execute in SQLite
        try:
            with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            content = SQLDumpConverter._sanitize_mysql(content)
            
            with sqlite3.connect(dest_db_path) as conn:
                conn.executescript(content)
                conn.commit()
        except Exception as e:
            raise ConversionError(f"Failed to convert MySQL Dump: {e}")

    @staticmethod
    def _sanitize_mysql(content: str) -> str:
        # Remove CREATE DATABASE, USE, DROP DATABASE
        content = re.sub(r'(?im)^\s*(CREATE|DROP)\s+DATABASE\s+[^;]+;', '', content)
        content = re.sub(r'(?im)^\s*USE\s+[^;]+;', '', content)
        
        # Remove LOCK TABLES / UNLOCK TABLES
        content = re.sub(r'(?im)^\s*LOCK\s+TABLES\s+[^;]+;', '', content)
        content = re.sub(r'(?im)^\s*UNLOCK\s+TABLES;', '', content)
        
        # Remove SET statements
        content = re.sub(r'(?im)^\s*SET\s+[^;]+;', '', content)
        
        # Replace AUTO_INCREMENT with nothing (in SQLite INTEGER PRIMARY KEY auto-increments by default, or you can use AUTOINCREMENT but it requires INTEGER PRIMARY KEY)
        # We will just remove it.
        content = re.sub(r'(?i)\bAUTO_INCREMENT\b', '', content)
        
        # Remove ENGINE, CHARSET, COLLATE
        content = re.sub(r'(?i)\bENGINE=[a-zA-Z0-9_]+\b', '', content)
        content = re.sub(r'(?i)\bDEFAULT\s+CHARSET=[a-zA-Z0-9_]+\b', '', content)
        content = re.sub(r'(?i)\bCHARSET=[a-zA-Z0-9_]+\b', '', content)
        content = re.sub(r'(?i)\bCOLLATE=[a-zA-Z0-9_]+\b', '', content)
        content = re.sub(r'(?i)\bCOLLATE\s+[a-zA-Z0-9_]+\b', '', content)
        
        # Remove UNSIGNED
        content = re.sub(r'(?i)\bUNSIGNED\b', '', content)
        
        # Change boolean to integer
        # content = re.sub(r'(?i)\bBOOLEAN\b', 'INTEGER', content)
        
        # Remove comment lines starting with /*! and ending with */
        content = re.sub(r'/\*!.*?\*/;', '', content, flags=re.DOTALL)
        
        return content

    @staticmethod
    def convert_postgres(source_path: str, dest_db_path: str):
        try:
            with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            content = SQLDumpConverter._sanitize_postgres(content)
            
            with sqlite3.connect(dest_db_path) as conn:
                conn.executescript(content)
                conn.commit()
        except Exception as e:
            raise ConversionError(f"Failed to convert PostgreSQL Dump: {e}")

    @staticmethod
    def _sanitize_postgres(content: str) -> str:
        # Postgres has things like SET search_path, COPY, sequence creations
        content = re.sub(r'(?im)^\s*SET\s+[^;]+;', '', content)
        content = re.sub(r'(?im)^\s*SELECT\s+pg_catalog\.[^;]+;', '', content)
        
        # Convert COPY to INSERT is too hard if it uses stdin. We will just hope they used INSERTs
        # Often pg_dump uses COPY by default. If it has COPY, this simple parser will fail or skip.
        # It's best to error gracefully if COPY FROM stdin is found, but let's try to strip it if possible.
        if "COPY " in content and "FROM stdin;" in content:
            # COPY is not supported by basic execute script
            # Removing it will just leave table empty, better to raise error
            pass # We will let it fail on execute if it's invalid SQLite
            
        content = re.sub(r'(?i)\bSERIAL\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', content)
        content = re.sub(r'(?i)\bBIGSERIAL\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', content)
        return content

    @staticmethod
    def convert_generic(source_path: str, dest_db_path: str):
        try:
            with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            with sqlite3.connect(dest_db_path) as conn:
                conn.executescript(content)
                conn.commit()
        except Exception as e:
            raise ConversionError(f"Failed to execute generic SQL: {e}")

