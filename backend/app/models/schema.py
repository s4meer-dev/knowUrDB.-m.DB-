from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str = Field(..., description="Name of the column")
    data_type: str = Field(..., description="SQLite data type of the column")
    primary_key: bool = Field(
        False, description="Whether the column is part of the primary key"
    )
    nullable: bool = Field(
        True, description="Whether the column can contain null values"
    )


class ForeignKeyInfo(BaseModel):
    source_column: str = Field(..., description="Column in this table")
    referenced_table: str = Field(..., description="Table being referenced")
    referenced_column: str = Field(..., description="Column in the referenced table")


class TableInfo(BaseModel):
    name: str = Field(..., description="Name of the table")
    columns: list[ColumnInfo] = Field(
        default_factory=list, description="Columns in the table"
    )
    primary_keys: list[str] = Field(
        default_factory=list, description="List of primary key column names"
    )
    foreign_keys: list[ForeignKeyInfo] = Field(
        default_factory=list, description="Foreign key relationships"
    )


class DatabaseSchema(BaseModel):
    tables: list[TableInfo] = Field(
        default_factory=list, description="All tables in the database"
    )


class SchemaSummary(BaseModel):
    summary: str = Field(
        ..., description="A human-readable summary of the database schema"
    )
