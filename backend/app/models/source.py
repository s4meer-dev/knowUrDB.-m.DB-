from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    DOCUMENT_COLLECTION = "document_collection"
    RELATIONAL = "relational"
    TABULAR = "tabular"
    DOCUMENT = "document"
    MIXED = "mixed"


class SourceStatus(str, Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class SourceMetadata(BaseModel):
    source_id: str = Field(..., description="Unique immutable source identifier")
    name: str = Field(..., description="Display name of the source")
    original_filename: str = Field(..., description="Original uploaded filename")
    file_type: str = Field(..., description="File extension")
    mime_type: str = Field(..., description="MIME type")
    detected_format: str = Field(
        ..., description="Detected format (e.g., mongodb, csv, json, excel, parquet, pdf)"
    )
    detected_dialect: str | None = Field(None, description="Engine or dialect")
    size_bytes: int = Field(..., description="Size of file in bytes")
    uploaded_at: str = Field(..., description="ISO datetime of upload")
    status: SourceStatus = Field(..., description="Current status of the source")
    database_name: str | None = Field(
        default=None, description="Dedicated MongoDB database folder name in MongoDB Compass (e.g. knowurdb_demo)"
    )
    collections: list[str] = Field(
        default_factory=list, description="MongoDB collection names created inside database_name"
    )
    table_count: int | None = Field(
        0, description="Number of MongoDB collections (aliased as table_count for UI compatibility)"
    )
    record_count: int | None = Field(
        0, description="Total MongoDB documents across collections"
    )
    index_count: int | None = Field(
        0, description="Total MongoDB indexes created across collections"
    )
    schema_summary: Any | None = Field(
        None, description="Summary of MongoDB collection schemas for routing"
    )
    storage_location: str = Field(
        default="mongodb://knowurdb", description="Storage URI or file path", exclude=True
    )
    error_message: str | None = Field(None, description="Error message if failed")
