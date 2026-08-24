import sqlite3
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
            # Add indexes for efficient querying
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC)"
            )


# Default provider pointing to the app DB in the database folder
DEFAULT_APP_DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "app.db"
app_db_provider = AppDatabaseProvider(DEFAULT_APP_DB_PATH)
