from app.core.mongodb import MongoDBManager


class DatabaseProvider:
    """
    MongoDB-native database provider facade.
    Replaces legacy SQLite connection logic with MongoDB database/collection access.
    """

    def __init__(self, source_id: str | None = None):
        self.source_id = source_id or MongoDBManager.get_active_source_id()

    def get_db(self):
        return MongoDBManager.get_db()


class DatabaseManager:
    @staticmethod
    def get_active_provider() -> DatabaseProvider:
        return DatabaseProvider(MongoDBManager.get_active_source_id())

    @staticmethod
    def get_active_database_info() -> dict:
        source_id = MongoDBManager.get_active_source_id()
        db = MongoDBManager.get_db()
        src = db[MongoDBManager.SYS_SOURCES].find_one({"source_id": source_id}) if source_id else None
        if src:
            return {
                "is_demo": bool(src.get("is_demo", False)),
                "name": src.get("name", "MongoDB Collection"),
                "source_id": src.get("source_id"),
                "collections": src.get("collections", []),
                "engine": "mongodb",
            }
        return {
            "is_demo": True,
            "name": "knowUrDB MongoDB",
            "source_id": "demo-source-id",
            "collections": [],
            "engine": "mongodb",
        }

    @staticmethod
    def set_active_database(source_or_path: str) -> None:
        """
        Sets the active source ID (or resolves a legacy storage identifier to source_id).
        """
        db = MongoDBManager.get_db()
        src = db[MongoDBManager.SYS_SOURCES].find_one(
            {"$or": [{"source_id": source_or_path}, {"storage_location": source_or_path}]}
        )
        if src:
            MongoDBManager.set_active_source(src["source_id"])
        else:
            MongoDBManager.set_active_source(source_or_path)

    @staticmethod
    def reset_to_demo() -> None:
        MongoDBManager.set_active_source("demo-source-id")
