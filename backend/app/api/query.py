from fastapi import APIRouter, HTTPException

from app.core.database import demo_db_provider
from app.models.query import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.query_intelligence_service import QueryIntelligenceService
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLSafetyError
from app.services.text_to_sql_service import TextToSQLService

router = APIRouter()

# Dependencies
schema_service = SchemaService(demo_db_provider)
text_to_sql_service = TextToSQLService(schema_service)
query_executor = QueryExecutor(demo_db_provider)
ai_service = AIService()
history_service = HistoryService()
query_intelligence_service = QueryIntelligenceService(ai_service, schema_service)


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    sql = None
    query_source = None

    try:
        # 1. Translate NL to SQL (Deterministic Fallback/Internal)
        sql = text_to_sql_service.translate(request.question)
        query_source = "fallback"
    except ValueError:
        # 2. AI Generation
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
                query_source = "ai"
            except Exception:  # noqa: BLE001
                error_msg = "The AI service is temporarily unavailable. A supported fallback was attempted where possible."
                history_service.log_query(
                    question=request.question,
                    query_source="ai",
                    status="error",
                    error_message=error_msg,
                )
                return NaturalLanguageQueryResponse(
                    question=request.question,
                    status="error",
                    error=error_msg,
                )
        else:
            error_msg = "I couldn't find data related to that concept in the available database."
            history_service.log_query(
                question=request.question,
                query_source="fallback",
                status="error",
                error_message=error_msg,
            )
            return NaturalLanguageQueryResponse(
                question=request.question,
                status="error",
                error=error_msg,
            )

    try:
        # 3. Validate & Execute
        columns, rows, exec_time = query_executor.execute(sql)
        row_count = len(rows)

        # 4. Intelligence
        explanation = query_intelligence_service.generate_explanation(
            sql, request.question
        )
        follow_ups = query_intelligence_service.generate_follow_up_suggestions(
            request.question, sql
        )

        # 5. History Logging
        history_service.log_query(
            question=request.question,
            query_source=query_source,
            status="success",
            generated_sql=sql,
            row_count=row_count,
            execution_time_ms=exec_time,
        )

        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=sql,
            columns=columns,
            rows=rows,
            row_count=row_count,
            execution_time_ms=round(exec_time, 2),
            status="success",
            query_source=query_source,
            explanation=explanation,
            follow_up_suggestions=follow_ups,
            # Even if row_count == 0, we treat it as success but we can provide an error/message in the frontend.
            # Wait, the prompt says: "A successful query with zero rows must still be: status = success, with row_count = 0, and a friendly message such as 'No matching records were found.'"
            # We can put this in the `error` field as a message, or just return it. The prompt says "friendly message such as". We'll put it in `error` or handle in frontend? It says "and a friendly message such as 'No matching records were found.' Do not treat an empty result as a server error."
            # We can use the error field for the message if row_count == 0, but status remains 'success'.
            error="Your question was understood successfully, but no matching records were found."
            if row_count == 0
            else None,
        )
    except SQLSafetyError:
        error_msg = "The generated query was rejected because it did not meet database safety requirements."
        history_service.log_query(
            question=request.question,
            query_source=query_source,
            status="error",
            generated_sql=sql,
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=sql,
            status="error",
            error=error_msg,
            query_source=query_source,
        )
    except QueryExecutionError as e:
        if "Safety validation failed" in str(e):
            error_msg = "The generated query was rejected because it did not meet database safety requirements."
        else:
            error_msg = "An error occurred while executing the query on the database."

        history_service.log_query(
            question=request.question,
            query_source=query_source,
            status="error",
            generated_sql=sql,
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=sql,
            status="error",
            error=error_msg,
            query_source=query_source,
        )
