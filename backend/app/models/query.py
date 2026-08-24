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
    query_source: str | None = Field(
        None, description="The source of the generated query (e.g., 'ai', 'fallback')."
    )
    explanation: str | None = Field(
        None, description="Plain English explanation of the executed SQL."
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list, description="Follow-up question suggestions."
    )


class QueryHistoryItem(BaseModel):
    id: str = Field(..., description="Unique query ID")
    question: str = Field(..., description="Original natural language question")
    generated_sql: str | None = Field(None, description="The generated SQL")
    query_source: str = Field(
        ..., description="Source of the query (e.g., 'ai', 'fallback')"
    )
    status: str = Field(..., description="Status ('success', 'error')")
    row_count: int | None = Field(None, description="Number of rows returned")
    execution_time_ms: float | None = Field(None, description="Execution time in ms")
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")


class SuggestionsResponse(BaseModel):
    suggestions: list[str] = Field(
        ..., description="List of natural language suggestions based on schema"
    )
