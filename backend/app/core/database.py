import sqlite3
from pathlib import Path


class DatabaseProvider:
    """
    Provides safe, read-only access to the knowUrDB Demo Database.
    This is the foundation for Phase 2 backend integration.
    Future phases will expand this to support user-uploaded databases.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a read-only SQLite connection.
        Using URI with mode=ro ensures no accidental modifications.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        # Open in read-only mode using uri
        # The path must be absolute and formatted correctly for URI
        db_uri = f"file:{self.db_path.absolute().as_posix()}?mode=ro"

        conn = sqlite3.connect(db_uri, uri=True)
        # We can also enforce foreign keys even on read, though not strictly necessary
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


# Default provider pointing to the demo DB
DEFAULT_DEMO_DB_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "database"
    / "demo"
    / "knowurdb_demo.db"
)
demo_db_provider = DatabaseProvider(DEFAULT_DEMO_DB_PATH)
