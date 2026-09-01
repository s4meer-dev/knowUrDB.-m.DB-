from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
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
    detected_format: str = Field(..., description="Detected format (e.g., CSV, SQLite, PDF)")
    detected_dialect: str | None = Field(None, description="SQL dialect if applicable")
    size_bytes: int = Field(..., description="Size of file in bytes")
    uploaded_at: str = Field(..., description="ISO datetime of upload")
    status: SourceStatus = Field(..., description="Current status of the source")
    table_count: int | None = Field(0, description="Number of tables if structured")
    record_count: int | None = Field(0, description="Number of total records if structured")
    schema_summary: Any | None = Field(None, description="Summary of schema for routing")
    storage_location: str = Field(..., description="Path to the storage directory")
    error_message: str | None = Field(None, description="Error message if failed")

