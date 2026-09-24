from app.services.mongo_validator import (
    MongoQuerySafetyError,
    MongoQueryValidator,
    SQLSafetyError,
)

# Backwards-compatible alias for modules importing SQLValidator
SQLValidator = MongoQueryValidator

__all__ = [
    "MongoQuerySafetyError",
    "MongoQueryValidator",
    "SQLSafetyError",
    "SQLValidator",
]
