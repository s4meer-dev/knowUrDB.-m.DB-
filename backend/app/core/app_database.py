import sqlite3
import uuid
import datetime
from pathlib import Path


class AppDatabaseProvider:
    """
    Provides read-write access to the internal Application Database.
    This database stores application state such as query history,
    keeping it separate from the read-only user data database.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a SQLite connection to the app database.
        Creates the file if it does not exist.
        """
        # Connect in read-write mode, create if missing
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """
        Initializes the application database schema idempotently.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            # Settings table for active database state
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            # Query history table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_history (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    generated_sql TEXT,
                    query_source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    row_count INTEGER,
                    execution_time_ms REAL,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Sources Registry table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    detected_format TEXT NOT NULL,
                    detected_dialect TEXT,
                    size_bytes INTEGER NOT NULL,
                    uploaded_at DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    table_count INTEGER DEFAULT 0,
                    record_count INTEGER DEFAULT 0,
                    schema_summary TEXT,
                    storage_location TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            # Add indexes for efficient querying
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)"
            )

            # Initialize demo source if no sources exist
            cursor = conn.execute("SELECT COUNT(*) as count FROM sources")
            if cursor.fetchone()["count"] == 0:
                demo_db_path = Path(__file__).parent.parent.parent.parent / "database" / "demo" / "knowurdb_demo.db"
                
                # Check if file exists, else use relative path string for testing
                path_str = str(demo_db_path.absolute()) if demo_db_path.exists() else "database/demo/knowurdb_demo.db"
                
                conn.execute(
                    """
                    INSERT INTO sources (
                        source_id, name, original_filename, file_type, mime_type,
                        detected_format, size_bytes, uploaded_at, status, storage_location
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "demo-source-id",
                        "Demo Database",
                        "knowurdb_demo.db",
                        ".db",
                        "application/x-sqlite3",
                        "sqlite3",
                        demo_db_path.stat().st_size if demo_db_path.exists() else 0,
                        datetime.datetime.now(datetime.UTC).isoformat(),
                        "ready",
                        path_str
                    )
                )

    def get_setting(self, key: str) -> str | None:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()

# Default provider pointing to the app DB in the database folder
DEFAULT_APP_DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "app.db"
app_db_provider = AppDatabaseProvider(DEFAULT_APP_DB_PATH)
