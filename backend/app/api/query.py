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

from app.services.query_router import QueryRouter
from app.services.source_manager import SourceManager
from app.services.document_processor import DocumentProcessor
from app.services.gemini_provider import GeminiProvider

router = APIRouter()

# Dependencies
schema_service = SchemaService()
text_to_sql_service = TextToSQLService(schema_service)
query_executor = QueryExecutor()
ai_provider = GeminiProvider()
ai_service = AIService()
history_service = HistoryService()
query_intelligence_service = QueryIntelligenceService(ai_service, schema_service)
meta_router = MetaQueryRouter(schema_service, query_executor, ai_provider)
source_manager = SourceManager()
query_router = QueryRouter(ai_provider, source_manager)
document_processor = DocumentProcessor(ai_provider)

@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. New Routing Logic
    routing_decision = query_router.route_query(request.question, request.source_ids)
    
    if routing_decision["decision"] == "UNRELATED":
        error_msg = "I couldn't find relevant data for your question. Please ask something related to the available sources."
        return NaturalLanguageQueryResponse(
            question=request.question, status="error", error=error_msg, confidence=routing_decision["confidence"]
        )

    if routing_decision["decision"] == "META":
        # Let meta_router handle if applicable (it might not have access to multi-source meta, but we'll try)
        # Actually, for source discovery we should answer here.
        sources = source_manager.list_sources()
        names = [s.name for s in sources]
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="success",
            explanation=f"You have {len(sources)} available sources: {', '.join(names)}",
            query_source="meta",
            confidence=routing_decision["confidence"]
        )

    if routing_decision["decision"] == "CLARIFICATION":
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="clarification_required",
            error="I found relevant data in multiple sources. Which one would you like to use?",
            candidates=routing_decision["candidates"],
            confidence=routing_decision["confidence"]
        )

    # 2. Execution for SINGLE_SOURCE or MULTI_SOURCE
    # For now, we take the first source if multiple (we can implement advanced cross-source later)
    target_source = routing_decision["sources"][0]
    source_metadata = source_manager.get_source(target_source["source_id"])
    
    if not source_metadata:
        return NaturalLanguageQueryResponse(
            question=request.question, status="error", error="Selected source not found."
        )

    citations = [{
        "source_id": source_metadata.source_id,
        "name": source_metadata.name,
        "type": source_metadata.file_type
    }]

    if target_source["type"] in ["pdf", "txt", "markdown"]:
        # Document retrieval
        results = document_processor.search(request.question, source_metadata.storage_location)
        if not results:
             return NaturalLanguageQueryResponse(
                question=request.question, status="success",
                explanation="I could not find a specific answer to that question in the document.",
                sources=citations
            )
        
        # Build answer from top chunks
        context_str = "\n\n".join([f"Chunk: {r['text']}" for r in results])
        prompt = f"Answer the user's question based ONLY on the following text from {source_metadata.name}.\n\nText:\n{context_str}\n\nQuestion: {request.question}"
        answer = ai_provider.generate_text(prompt)
        
        # Add page citations if available
        for r in results:
            if r.get("page_number"):
                citations[0]["page"] = r["page_number"]
                break
                
        return NaturalLanguageQueryResponse(
            question=request.question, status="success",
            explanation=answer,
            query_source="single_source",
            sources=citations,
            confidence=routing_decision["confidence"]
        )
        
    # Relational Database Execution
    # Set this source as active for the query execution
    db_path = source_manager.get_internal_db_path(source_metadata.source_id)
    DatabaseManager.set_active_database(db_path)

    # 2.5 Deterministic Meta Query Router (Bypass AI entirely for simple schema/count questions)
    meta_response = meta_router.route_meta_query(request.question)
    if meta_response:
        history_service.log_query(
            question=request.question,
            query_source="meta",
            source_id=source_metadata.source_id,
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
            query_source="meta",
            explanation=meta_response["explanation"],
            follow_up_suggestions=[],
            error=None,
            sources=citations,
            confidence=routing_decision["confidence"]
        )

    sql = None
    query_source = None

    # 3. AI Generation (with retries)
    if not sql:
        ai_status = ai_service.get_status()
        if not (ai_status.get("configured") and ai_status.get("status") == "ready"):
            try:
                sql = text_to_sql_service.translate(request.question)
                query_source = "nlp_lite"
                
                # Still need to validate safety for deterministic output (e.g. from mock tests)
                SQLValidator.validate(sql)
                SQLValidator.validate_against_db(sql, DatabaseManager.get_active_provider())
            except SQLSafetyError:
                error_msg = "The generated query was rejected because it did not meet database safety requirements."
                history_service.log_query(
                    question=request.question,
                    query_source="nlp_lite",
                    source_id=source_metadata.source_id,
                    status="error",
                    generated_sql=sql,
                    error_message=error_msg,
                )
                return NaturalLanguageQueryResponse(
                    question=request.question, status="error", error=error_msg
                )
            except ValueError:
                error_msg = "I couldn't find data related to that concept in the available database."
                history_service.log_query(
                    question=request.question,
                    query_source="fallback",
                    source_id=source_metadata.source_id,
                    status="error",
                    error_message=error_msg,
                )
                return NaturalLanguageQueryResponse(
                    question=request.question, status="error", error=error_msg
                )

        if not sql:
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
                    source_id=source_metadata.source_id,
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
                    source_id=source_metadata.source_id,
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
                source_id=source_metadata.source_id,
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
            source_id=source_metadata.source_id,
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
            sources=citations,
            confidence=routing_decision["confidence"],
            error="Your question was understood successfully, but no matching records were found."
            if row_count == 0
            else None,
        )
    except SQLSafetyError:
        error_msg = "The generated query was rejected because it did not meet database safety requirements."
        history_service.log_query(
            question=request.question,
            query_source=query_source,
            source_id=source_metadata.source_id,
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
            # We want to give the specific DB error without a stack trace
            error_detail = str(e).replace("Database error: ", "")
            error_msg = f"An error occurred while executing the query: {error_detail}"

        history_service.log_query(
            question=request.question,
            query_source=query_source,
            source_id=source_metadata.source_id,
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
