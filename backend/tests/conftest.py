import pytest

from app.core.mongodb import MongoDBManager
from app.services.demo_generator import DemoGenerator


@pytest.fixture(scope="session", autouse=True)
def configure_real_mongodb_test_environment():
    """
    Connects to the isolated `knowurdb_test` database on the real MongoDB server
    (or embedded mongomock fallback if offline) and seeds the MongoDB Demo Dataset.
    """
    MongoDBManager.reset_client(use_mock=False, db_name="knowurdb_test")
    db = MongoDBManager.get_db()

    # Clean previous test collections
    for col in db.list_collection_names():
        if not col.startswith("system."):
            db[col].drop()

    MongoDBManager.init_db()
    DemoGenerator().seed_initial_demo_if_empty()

    yield

    # Clean up test databases after suite completion
    try:
        client = MongoDBManager.get_client()
        for db_n in client.list_database_names():
            if db_n.startswith("knowurdb_test"):
                client.drop_database(db_n)
    except Exception:
        pass
