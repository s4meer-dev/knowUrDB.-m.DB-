from typing import Any

from pydantic import BaseModel, Field


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(
        ..., description="The natural language question to ask the database."
    )


class NaturalLanguageQueryResponse(BaseModel):
    question: str = Field(..., description="The original natural language question.")
    generated_sql: str | None = Field(
        None, description="The SQL query generated from the question."
    )
    columns: list[str] = Field(
        default_factory=list, description="The column names of the result set."
    )
    rows: list[dict[str, Any]] = Field(
        default_factory=list, description="The rows of the result set."
    )
    row_count: int = Field(0, description="The number of rows returned.")
    execution_time_ms: float = Field(
        0.0, description="The execution time in milliseconds."
    )
    status: str = Field(
        ..., description="The status of the query execution (e.g., 'success', 'error')."
    )
    error: str | None = Field(None, description="The error message, if any.")
