from fastapi import APIRouter, HTTPException

from app.core.database import DatabaseManager
from app.models.query import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse
from app.services.ai_service import AIService
from app.services.history_service import HistoryService
from app.services.meta_query_router import MetaQueryRouter
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.query_intelligence_service import QueryIntelligenceService
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLSafetyError, SQLValidator
from app.services.text_to_sql_service import TextToSQLService

router = APIRouter()

# Dependencies
schema_service = SchemaService()
text_to_sql_service = TextToSQLService(schema_service)
query_executor = QueryExecutor()
ai_service = AIService()
history_service = HistoryService()
query_intelligence_service = QueryIntelligenceService(ai_service, schema_service)
meta_router = MetaQueryRouter(schema_service, query_executor)


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 0. Deterministic Meta Query Router (Bypass AI entirely for simple schema/count questions)
    meta_response = meta_router.route_meta_query(request.question)
    if meta_response:
        history_service.log_query(
            question=request.question,
            query_source="fallback",
            status="success",
            generated_sql=meta_response.get("generated_sql", ""),
            row_count=meta_response["row_count"],
            execution_time_ms=meta_response["execution_time_ms"],
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_sql=meta_response.get("generated_sql", ""),
            columns=meta_response["columns"],
            rows=meta_response["rows"],
            row_count=meta_response["row_count"],
            execution_time_ms=meta_response["execution_time_ms"],
            status="success",
            query_source="fallback",
            explanation=meta_response["explanation"],
            follow_up_suggestions=[],
            error=None,
        )

    # 1. Intent Validation
    intent = query_intelligence_service.analyze_intent(request.question)

    if intent == "UNRELATED":
        tables = schema_service.get_table_names()
        table_str = ", ".join(tables[:3]) if tables else ""
        suggestion = f" You can ask about tables such as {table_str}." if table_str else ""
        error_msg = f"This assistant is currently connected to your selected database. Please ask a question related to the data, tables, or relationships available in this database.{suggestion}"
        history_service.log_query(
            question=request.question,
            query_source="none",
            status="error",
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question, status="error", error=error_msg
        )

    if intent == "AMBIGUOUS":
        tables = ", ".join(schema_service.get_table_names())
        error_msg = f"The question is database-related, but it is ambiguous. Please specify which table or type of record you want to query. Available tables include: {tables}."
        history_service.log_query(
            question=request.question,
            query_source="none",
            status="error",
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question, status="error", error=error_msg
        )

    sql = None
    query_source = None

    # 2. Try Deterministic Fallback First
    try:
        fallback_sql = text_to_sql_service.translate(request.question)
        # Validate against actual DB to ensure it didn't hallucinate a table like 'students' when it doesn't exist
        SQLValidator.validate(fallback_sql)
        SQLValidator.validate_against_db(fallback_sql, DatabaseManager.get_active_provider())
        sql = fallback_sql
        query_source = "fallback"
    except SQLSafetyError:
        error_msg = "The generated query was rejected because it did not meet database safety requirements."
        history_service.log_query(
            question=request.question,
            query_source="fallback",
            status="error",
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question, status="error", error=error_msg
        )
    except Exception:  # noqa: BLE001, S110
        # Deterministic generation failed or generated invalid SQL for this schema
        pass

    # 3. AI Generation (with retries)
    if not sql:
        ai_status = ai_service.get_status()
        if not (ai_status.get("configured") and ai_status.get("status") == "ready"):
            error_msg = "I couldn't find data related to that concept in the available database."
            history_service.log_query(
                question=request.question,
                query_source="fallback",
                status="error",
                error_message=error_msg,
            )
            return NaturalLanguageQueryResponse(
                question=request.question, status="error", error=error_msg
            )

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
- Use ONLY tables and columns explicitly present in the supplied schema. Never invent a table, column, or relationship.
"""

        max_retries = 2
        last_error = None
        current_sql = None

        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    ai_response = ai_service.generate(prompt)
                    current_sql = ai_response["response"].strip()
                else:
                    # Repair attempt
                    current_sql = query_intelligence_service.repair_sql(
                        request.question, current_sql, last_error
                    )
                    if not current_sql:
                        break  # Give up if repair fails to generate

                # Clean up AI output
                if current_sql.startswith("```sql"):
                    current_sql = current_sql[6:]
                elif current_sql.startswith("```"):
                    current_sql = current_sql[3:]
                current_sql = current_sql.removesuffix("```").strip()

                # Validate safety and schema
                SQLValidator.validate(current_sql)
                SQLValidator.validate_against_db(current_sql, DatabaseManager.get_active_provider())

                # If we get here, it's valid
                sql = current_sql
                query_source = "ai"
                break

            except SQLSafetyError:
                # Do not retry safety violations
                error_msg = "The generated query was rejected because it did not meet database safety requirements."
                history_service.log_query(
                    question=request.question,
                    query_source="ai",
                    status="error",
                    generated_sql=current_sql,
                    error_message=error_msg,
                )
                return NaturalLanguageQueryResponse(
                    question=request.question,
                    generated_sql=current_sql,
                    status="error",
                    error=error_msg,
                    query_source="ai",
                )
            except RuntimeError:
                # If the AI provider fails (network, auth, etc.), do not retry
                error_msg = "I could not confidently interpret that database request. Please ask about the available tables, columns, records, or data in the connected database."
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
                    query_source="ai",
                )
            except Exception as e:  # noqa: BLE001
                last_error = str(e)
                # Loop will continue and try to repair

        if not sql:
            # Exhausted retries
            error_msg = "I could not confidently interpret that database request. Please ask about the available tables, columns, records, or data in the connected database."
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
                query_source="ai",
            )

    # 4. Execute Query
    try:
        columns, rows, exec_time = query_executor.execute(sql)
        row_count = len(rows)

        explanation = query_intelligence_service.generate_explanation(
            sql, request.question
        )
        follow_ups = query_intelligence_service.generate_follow_up_suggestions(
            request.question, sql
        )

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
