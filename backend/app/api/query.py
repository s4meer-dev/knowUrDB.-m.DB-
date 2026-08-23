from app.core.database import demo_db_provider
from app.models.query import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse
from app.services.ai_service import AIService
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLSafetyError
from app.services.text_to_sql_service import TextToSQLService
from fastapi import APIRouter, HTTPException

router = APIRouter()

# In a real app, these would be injected dependencies
schema_service = SchemaService(demo_db_provider)
text_to_sql_service = TextToSQLService(schema_service)
query_executor = QueryExecutor(demo_db_provider)
ai_service = AIService()


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    sql = None
    try:
        # 1. Translate NL to SQL
        sql = text_to_sql_service.translate(request.question)
    except ValueError as e:
        # 2. AI Fallback
        ai_status = ai_service.get_status()
        if ai_status.get("configured") and ai_status.get("status") == "ready":
            try:
                schema_summary = schema_service.get_schema_summary().summary
                prompt = f"""You are a SQL generation assistant for a SQLite database.
The database schema is as follows:
{schema_summary}

Based on this schema, write a valid SQLite SQL query to answer the following user question:
"{request.question}"

IMPORTANT RULES:
- Return ONLY the raw SQL query.
- Do NOT wrap the SQL in markdown formatting or backticks (no ```sql ... ```).
- Do NOT include any explanations or conversational text.
- Only generate SELECT statements. No data mutation is allowed.
"""
                ai_response = ai_service.generate(prompt)

                # Clean up AI output
                sql = ai_response["response"].strip()
                if sql.startswith("```sql"):
                    sql = sql[6:]
                elif sql.startswith("```"):
                    sql = sql[3:]
                sql = sql.removesuffix("```")
                sql = sql.strip()
            except Exception as ai_e:  # noqa: BLE001
                return NaturalLanguageQueryResponse(
                    question=request.question,
                    generated_sql=None,
                    status="error",
                    error=f"Unsupported question: AI generation failed - {ai_e!s}",
                )
        else:
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
