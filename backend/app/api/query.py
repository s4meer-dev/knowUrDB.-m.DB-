from fastapi import APIRouter, HTTPException

from app.core.database import demo_db_provider
from app.models.query import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLSafetyError
from app.services.text_to_sql_service import TextToSQLService

router = APIRouter()

# In a real app, these would be injected dependencies
schema_service = SchemaService(demo_db_provider)
text_to_sql_service = TextToSQLService(schema_service)
query_executor = QueryExecutor(demo_db_provider)


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # 1. Translate NL to SQL
        sql = text_to_sql_service.translate(request.question)
    except ValueError as e:
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=None,
            status="error",
            error=f"Unsupported question: {e!s}",
        )

    try:
        # 2. Validate & Execute
        columns, rows, exec_time = query_executor.execute(sql)

        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=round(exec_time, 2),
            status="success",
        )
    except SQLSafetyError as e:
        return NaturalLanguageQueryResponse(
            question=request.question, generated_sql=sql, status="error", error=str(e)
        )
    except QueryExecutionError as e:
        return NaturalLanguageQueryResponse(
            question=request.question, generated_sql=sql, status="error", error=str(e)
        )
