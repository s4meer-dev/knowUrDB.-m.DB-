import re
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd


def import_sql_source_to_mongodb(
    file_path: str, format_type: str, fallback_name: str
) -> dict[str, pd.DataFrame]:
    """
    Isolated migration helper that extracts rows from legacy SQLite or SQL script files
    and returns pandas DataFrames so FormatConverter can model and insert them as native
    MongoDB collections. Never used during query runtime.
    """
    results: dict[str, pd.DataFrame] = {}
    if format_type == "sqlite":
        conn = sqlite3.connect(f"file:{Path(file_path).absolute().as_posix()}?mode=ro", uri=True)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]
            for t in tables:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
                results[t] = df
        finally:
            conn.close()
        return results

    # For SQL script files (.sql), execute into a temporary in-memory sqlite instance solely to extract rows
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        sql_text = f.read()

    # Basic dialect sanitization for migration import
    sql_clean = re.sub(r"ENGINE=\w+", "", sql_text, flags=re.IGNORECASE)
    sql_clean = re.sub(r"AUTO_INCREMENT=\d+", "", sql_clean, flags=re.IGNORECASE)
    sql_clean = re.sub(r"DEFAULT CHARSET=\w+", "", sql_clean, flags=re.IGNORECASE)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
        conn = sqlite3.connect(tmp.name)
        try:
            conn.executescript(sql_clean)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]
            for t in tables:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
                results[t] = df
        finally:
            conn.close()

    return results
