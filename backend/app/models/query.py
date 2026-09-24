from typing import Any

from pydantic import BaseModel, Field


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(
        ..., description="The natural language question to ask MongoDB."
    )
    source_ids: list[str] | None = Field(
        None, description="Explicit source IDs to restrict the query to."
    )
    active_collection: str | None = Field(
        None, description="Optional currently selected collection in the UI workspace."
    )
    conversation_context: dict[str, Any] | None = Field(
        None, description="Optional conversational context (last collection, filters, intent)."
    )


class StructuredMongoQuery(BaseModel):
    collection: str = Field(..., description="Target MongoDB collection name")
    operation: str = Field(
        default="aggregate",
        description="Allowed read-only operation: 'aggregate', 'find', 'count', 'distinct'",
    )
    pipeline: list[dict[str, Any]] = Field(
        default_factory=list,
        description="MongoDB aggregation pipeline stages (for operation='aggregate')",
    )
    filter: dict[str, Any] = Field(
        default_factory=dict,
        description="MongoDB filter query (for find/count/distinct)",
    )
    projection: dict[str, Any] | None = Field(
        default=None,
        description="MongoDB field projection",
    )
    sort: list[tuple[str, int]] | dict[str, int] | None = Field(
        default=None,
        description="Sort specification",
    )
    limit: int = Field(default=100, description="Maximum documents to return")
    distinct_field: str | None = Field(
        default=None, description="Field name when operation='distinct'"
    )


class QuerySourceCitation(BaseModel):
    source_id: str
    name: str
    type: str
    table: str | None = None
    collection: str | None = None
    page: int | None = None


class ClarificationCandidate(BaseModel):
    source_id: str
    name: str
    collection: str | None = None


class AnswerModel(BaseModel):
    headline: str | None = Field(
        None, description="The title of the primary answer (e.g., 'TOTAL CUSTOMERS')"
    )
    value: str | None = Field(
        None, description="The primary value (e.g., '1,250', 'Electronics')"
    )
    unit: str | None = Field(
        None, description="The unit or suffix for the value (e.g., 'documents')"
    )
    summary: str | None = Field(
        None, description="A full-sentence summary of the finding."
    )


class NaturalLanguageQueryResponse(BaseModel):
    question: str = Field(..., description="The original natural language question.")
    intent: str | None = Field(
        None, description="Detected canonical intent (e.g., 'LIST_RECORDS', 'COUNT', 'DATASET_OVERVIEW')."
    )
    collection: str | None = Field(
        None, description="Resolved target collection name."
    )
    query_plan: dict[str, Any] | None = Field(
        None, description="Internal structured query plan object."
    )
    presentation: dict[str, Any] | None = Field(
        None, description="Deterministic presentation plan contract for UI rendering."
    )
    generated_mongo_query: str | None = Field(
        None, description="Human-readable MongoDB aggregation pipeline / query string."
    )
    structured_query: dict[str, Any] | None = Field(
        None, description="Structured MongoDB query representation executed."
    )
    generated_sql: str | None = Field(
        None,
        description="Populated with the human-readable MongoDB pipeline string for UI panel compatibility.",
    )
    columns: list[str] = Field(
        default_factory=list, description="The field names of the result set."
    )
    rows: list[dict[str, Any]] = Field(
        default_factory=list, description="The projected documents of the result set."
    )
    row_count: int = Field(0, description="The number of documents returned.")
    execution_time_ms: float = Field(
        0.0, description="The execution time in milliseconds."
    )
    status: str = Field(
        ...,
        description="Status of execution ('success', 'clarification_required', 'error').",
    )
    error: str | None = Field(None, description="The error message, if any.")
    error_code: str | None = Field(
        None,
        description="Semantic error code ('SOURCE_NOT_FOUND', 'UNRELATED_QUERY', 'UNSAFE_QUERY', 'UNSAFE_SQL').",
    )
    query_source: str | None = Field(
        None, description="Source of query ('ai', 'deterministic', 'rag', 'meta')."
    )
    answer: AnswerModel | None = Field(
        None, description="Structured primary answer to the question."
    )
    insights: list[str] = Field(
        default_factory=list, description="List of key insights from the data."
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list, description="Follow-up question suggestions."
    )
    sources: list[QuerySourceCitation] = Field(
        default_factory=list, description="Citations for the sources used."
    )
    candidates: list[ClarificationCandidate] = Field(
        default_factory=list, description="Candidates when clarification is required."
    )
    confidence: float | None = Field(
        None, description="Confidence score of the routing."
    )


class QueryHistoryItem(BaseModel):
    id: str = Field(..., description="Unique query ID")
    question: str = Field(..., description="Original natural language question")
    generated_mongo_query: str | None = Field(
        None, description="The generated MongoDB query / aggregation pipeline"
    )
    generated_sql: str | None = Field(
        None, description="Alias containing the generated MongoDB pipeline for UI compatibility"
    )
    query_source: str = Field(
        ..., description="Source of the query (e.g., 'ai', 'deterministic', 'rag')"
    )
    source_id: str | None = Field(None, description="The ID of the source queried")
    status: str = Field(..., description="Status ('success', 'error')")
    row_count: int | None = Field(None, description="Number of documents returned")
    execution_time_ms: float | None = Field(None, description="Execution time in ms")
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")


class SuggestionsResponse(BaseModel):
    suggestions: list[Any] = Field(
        ..., description="List of natural language suggestions based on MongoDB collection schemas"
    )
