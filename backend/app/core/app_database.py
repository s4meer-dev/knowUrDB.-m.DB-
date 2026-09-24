from app.core.mongodb import MongoDBManager


class AppDatabaseProvider:
    """
    MongoDB-native Application Database Provider.
    Delegates application settings, sources registry, and query history initialization
    to MongoDBManager.
    """

    def init_db(self) -> None:
        MongoDBManager.init_db()

    def get_setting(self, key: str) -> str | None:
        return MongoDBManager.get_setting(key)

    def set_setting(self, key: str, value: str) -> None:
        MongoDBManager.set_setting(key, value)


app_db_provider = AppDatabaseProvider()
