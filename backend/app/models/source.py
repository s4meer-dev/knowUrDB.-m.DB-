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
    dataset_id: str | None = Field(default=None, description="Dataset registry identifier in knowurdb.datasets")
    generation_id: str | None = Field(default=None, description="Idempotent generation identifier in knowurdb.generations")
    name: str = Field(..., description="Display name of the source")
    display_name: str | None = Field(default=None, description="Human-friendly dataset display title")
    domain: str | None = Field(default=None, description="Dataset domain identifier (e.g. healthcare, finance)")
    description: str | None = Field(default=None, description="Concise summary of dataset contents")
    source_category: str = Field(
        default="mongodb",
        description="Distinguishes 'mongodb' (native MongoDB database) vs 'uploaded_file'",
    )
    original_filename: str = Field(..., description="Original uploaded filename or database identifier")
    file_type: str = Field(..., description="File extension or .mongodb")
    mime_type: str = Field(..., description="MIME type")
    detected_format: str = Field(
        ..., description="Detected format (e.g., mongodb, csv, json, excel, parquet, pdf)"
    )
    detected_dialect: str | None = Field(None, description="Engine or dialect")
    size_bytes: int = Field(..., description="Size of dataset or file in bytes")
    uploaded_at: str = Field(..., description="ISO datetime of creation/upload")
    status: SourceStatus = Field(..., description="Current status of the source")
    database_name: str | None = Field(
        default=None, description="Dedicated MongoDB database name in MongoDB Compass (e.g. demo_healthcare_a81f)"
    )
    collections: list[str] = Field(
        default_factory=list, description="MongoDB collection names created inside database_name"
    )
    collection_counts: dict[str, int] = Field(
        default_factory=dict, description="Exact document count per collection"
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
    manifest: dict[str, Any] | None = Field(
        default=None, description="Dataset generation manifest metadata"
    )
    filesystem_path: str | None = Field(
        default=None,
        description="Portable project-relative filesystem snapshot path (e.g. demo_datasets/demo_telecom_7aee)",
    )
    sync_status: str = Field(
        default="SYNCED",
        description="Synchronization status between MongoDB runtime and demo_datasets/ filesystem snapshot (SYNCED, EXPORTING, MISSING_FILES, MISSING_DATABASE, FAILED)",
    )
    dataset_artifacts: list[str] = Field(
        default_factory=list,
        description="List of relative artifact files inside the dataset snapshot folder",
    )
    storage_location: str = Field(
        default="mongodb://knowurdb", description="Storage URI or file path", exclude=True
    )
    error_message: str | None = Field(None, description="Error message if failed")

