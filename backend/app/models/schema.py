from typing import Any

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str = Field(..., description="Field path (e.g., 'customer_id', 'contact.email', 'items[].price')")
    data_type: str = Field(..., description="Inferred BSON/JSON data type (e.g., String, Double, Int64, Object, Array, Date, ObjectId)")
    type: str | None = Field(None, description="Alias for data_type for frontend compatibility")
    primary_key: bool = Field(
        False, description="Whether the field is _id or an indexed primary identifier"
    )
    nullable: bool = Field(
        True, description="Whether the field can be null or omitted"
    )
    is_nested: bool = Field(
        False, description="Whether the field is inside a nested embedded document"
    )
    is_array: bool = Field(
        False, description="Whether the field is an array or inside an array"
    )
    sample_values: list[Any] = Field(
        default_factory=list, description="Sample values observed in documents"
    )


class ForeignKeyInfo(BaseModel):
    source_column: str = Field(..., description="Field in this collection")
    referenced_table: str = Field(..., description="Referenced collection name")
    referenced_column: str = Field(..., description="Referenced field in target collection")


class IndexInfo(BaseModel):
    name: str = Field(..., description="Index name")
    keys: list[str] = Field(default_factory=list, description="Indexed field keys")
    unique: bool = Field(False, description="Whether the index enforces uniqueness")


class TableInfo(BaseModel):
    name: str = Field(..., description="Name of the MongoDB collection")
    document_count: int = Field(0, description="Number of documents in the collection")
    columns: list[ColumnInfo] = Field(
        default_factory=list, description="Fields (including nested/array paths) in the collection"
    )
    primary_keys: list[str] = Field(
        default_factory=list, description="Primary identifier fields (_id, etc.)"
    )
    foreign_keys: list[ForeignKeyInfo] = Field(
        default_factory=list, description="Inferred $lookup relationships across collections"
    )
    indexes: list[IndexInfo] = Field(
        default_factory=list, description="Active MongoDB indexes on this collection"
    )
    sample_document: dict[str, Any] | None = Field(
        None, description="Representative sample BSON/JSON document"
    )


class DatabaseSchema(BaseModel):
    tables: list[TableInfo] = Field(
        default_factory=list, description="All MongoDB collections in the active source"
    )
    collections: list[TableInfo] = Field(
        default_factory=list, description="MongoDB collections alias"
    )


class SchemaSummary(BaseModel):
    summary: str = Field(
        ..., description="A human-readable summary of the MongoDB collections and document schemas"
    )
