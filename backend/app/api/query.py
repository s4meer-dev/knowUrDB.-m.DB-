import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import DatabaseManager
from app.core.mongodb import MongoDBManager
from app.models.query import (
    AnswerModel,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
)
from app.services.ai_service import AIService
from app.services.document_processor import DocumentProcessor
from app.services.gemini_provider import GeminiProvider
from app.services.history_service import HistoryService
from app.services.meta_query_router import MetaQueryRouter
from app.services.mongo_validator import MongoQuerySafetyError, MongoQueryValidator
from app.services.query_executor import MongoQueryExecutor, QueryExecutionError
from app.services.query_intelligence_service import QueryIntelligenceService
from app.services.query_router import QueryRouter
from app.services.schema_service import MongoSchemaService
from app.services.source_manager import SourceManager
from app.services.text_to_sql_service import MongoQueryService

router = APIRouter()

schema_service = MongoSchemaService()
mongo_query_service = MongoQueryService(schema_service)
query_executor = MongoQueryExecutor()
ai_provider = GeminiProvider()
ai_service = AIService()
history_service = HistoryService()
query_intelligence_service = QueryIntelligenceService(ai_service, schema_service)
meta_router = MetaQueryRouter(schema_service, query_executor, ai_provider)
source_manager = SourceManager()
query_router = QueryRouter(ai_provider, source_manager)
document_processor = DocumentProcessor(ai_provider)


class ValidateQueryRequest(BaseModel):
    query: dict[str, Any] | str


@router.post("/query/validate")
async def validate_mongo_query(request: ValidateQueryRequest):
    try:
        structured = MongoQueryValidator.validate_against_db(request.query)
        return {
            "valid": True,
            "structured_query": structured,
            "formatted_pipeline": MongoQueryValidator.format_human_readable(structured),
        }
    except MongoQuerySafetyError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "UNSAFE_QUERY", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "COLLECTION_NOT_FOUND", "message": str(exc)},
        ) from exc


@router.post("/query/execute")
async def execute_validated_mongo_query(request: ValidateQueryRequest):
    try:
        structured = MongoQueryValidator.validate_against_db(request.query)
        columns, rows, exec_time = query_executor.execute(structured)
        return {
            "status": "success",
            "collection": structured["collection"],
            "operation": structured["operation"],
            "formatted_pipeline": MongoQueryValidator.format_human_readable(structured),
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": exec_time,
        }
    except MongoQuerySafetyError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "UNSAFE_QUERY", "message": str(exc)},
        ) from exc
    except QueryExecutionError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "QUERY_EXECUTION_ERROR", "message": str(exc)},
        ) from exc


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def query_database(request: NaturalLanguageQueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 0. Security pre-check on natural language input
    try:
        MongoQueryValidator.validate_question_safety(request.question)
    except MongoQuerySafetyError as exc:
        error_msg = "The generated query was rejected because it did not meet MongoDB read-only safety requirements."
        history_service.log_query(
            question=request.question,
            query_source="security_guard",
            status="error",
            error_message=str(exc),
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error=error_msg,
            error_code="UNSAFE_SQL",
            query_source="security_guard",
        )

    # 1. Intelligent Multi-Source Routing
    routing_decision = query_router.route_query(request.question, request.source_ids)

    if routing_decision["decision"] == "UNRELATED":
        error_msg = (
            routing_decision.get("friendly_message")
            or "I couldn't find relevant data for your question in the available MongoDB collections."
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error=error_msg,
            error_code="UNRELATED_QUERY",
            confidence=routing_decision["confidence"],
        )

    if routing_decision["decision"] == "META":
        sources = source_manager.list_sources()
        names = [s.name for s in sources]
        rows = [
            {
                "name": s.name,
                "format": s.detected_format,
                "collections": ", ".join(s.collections) if s.collections else "—",
                "documents": s.record_count or 0,
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            }
            for s in sources
        ]
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query="db._sys_sources.find({}, { name: 1, detected_format: 1, collections: 1, record_count: 1 })",
            generated_sql="db._sys_sources.find({}, { name: 1, detected_format: 1, collections: 1, record_count: 1 })",
            columns=["name", "format", "collections", "documents", "status"],
            rows=rows,
            row_count=len(rows),
            status="success",
            answer=AnswerModel(
                headline="AVAILABLE MONGODB SOURCES",
                value=str(len(sources)),
                unit="sources",
                summary=f"You have {len(sources)} connected MongoDB sources: {', '.join(names)}",
            ),
            query_source="meta",
            confidence=routing_decision["confidence"],
        )

    if routing_decision["decision"] == "CLARIFICATION":
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="clarification_required",
            error="I found matching collections in multiple sources. Which source should I query?",
            candidates=routing_decision["candidates"],
            confidence=routing_decision["confidence"],
        )

    # 2. MULTI_SOURCE Execution across collections
    if routing_decision["decision"] == "MULTI_SOURCE":
        start_ms = time.perf_counter()
        db = MongoDBManager.get_db()
        citations = []
        comparison_rows = []
        for src in routing_decision["sources"]:
            meta = source_manager.get_source(src["source_id"])
            if meta:
                citations.append(
                    {
                        "source_id": meta.source_id,
                        "name": meta.name,
                        "type": meta.file_type,
                        "collection": ", ".join(meta.collections) if meta.collections else None,
                    }
                )
                for col_name in meta.collections or []:
                    doc_cnt = db[col_name].count_documents({})
                    comparison_rows.append(
                        {
                            "source": meta.name,
                            "collection": col_name,
                            "documents": doc_cnt,
                            "format": meta.detected_format,
                        }
                    )

        elapsed_ms = round((time.perf_counter() - start_ms) * 1000.0, 2)
        pipeline_str = "db.adminCommand({ listCollections: 1 }) // Multi-Source Aggregation"
        history_service.log_query(
            question=request.question,
            query_source="multi_source",
            status="success",
            generated_mongo_query=pipeline_str,
            row_count=len(comparison_rows),
            execution_time_ms=elapsed_ms,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=pipeline_str,
            generated_sql=pipeline_str,
            columns=["source", "collection", "documents", "format"],
            rows=comparison_rows,
            row_count=len(comparison_rows),
            execution_time_ms=elapsed_ms,
            status="success",
            answer=AnswerModel(
                headline="MULTI-SOURCE MONGODB ANALYSIS",
                value=str(len(citations)),
                unit="sources compared",
                summary=f"Compared {len(comparison_rows)} MongoDB collections across {len(citations)} sources ({', '.join(c['name'] for c in citations)}).",
            ),
            insights=[
                f"Evaluated {len(comparison_rows)} collections across {len(citations)} connected datasets.",
                f"Total combined documents: {sum(r['documents'] for r in comparison_rows):,}.",
            ],
            query_source="multi_source",
            sources=citations,
            confidence=routing_decision["confidence"],
        )

    # 3. Resolve Target Source for SINGLE_SOURCE or DOCUMENT_RAG
    target_source = routing_decision["sources"][0]
    source_metadata = source_manager.get_source(target_source["source_id"])
    if not source_metadata:
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error="Selected source not found.",
            error_code="SOURCE_NOT_FOUND",
        )

    citations = [
        {
            "source_id": source_metadata.source_id,
            "name": source_metadata.name,
            "type": source_metadata.file_type,
        }
    ]

    # 4. DOCUMENT_RAG Execution via MongoDB Vector Chunks
    if routing_decision["decision"] == "DOCUMENT_RAG" or target_source["type"] in ("pdf", "txt", "markdown"):
        start_ms = time.perf_counter()
        results = document_processor.search(request.question, source_metadata.source_id)
        elapsed_ms = round((time.perf_counter() - start_ms) * 1000.0, 2)
        rag_pipeline_str = (
            f'db._sys_document_chunks.aggregate([\n  {{ "$match": {{ "source_id": "{source_metadata.source_id}" }} }},\n  {{ "$sort": {{ "vector_score": -1 }} }},\n  {{ "$limit": 4 }}\n])'
        )

        if not results:
            return NaturalLanguageQueryResponse(
                question=request.question,
                generated_mongo_query=rag_pipeline_str,
                generated_sql=rag_pipeline_str,
                status="success",
                answer=AnswerModel(
                    headline="NO MATCHING CHUNKS",
                    value="0",
                    unit="matches",
                    summary="No relevant sections were found in the document for that query.",
                ),
                sources=citations,
            )

        top_chunk = results[0]
        citations[0]["page"] = top_chunk.get("page_number", 1)

        # Use AI synthesis if available, otherwise return clean grounded excerpt
        summary_text = top_chunk["text"]
        try:
            ai_status = ai_service.get_status()
            if ai_status.get("configured") and ai_status.get("status") == "ready":
                context_str = "\n\n".join([f"[Page {r.get('page_number', 1)}]: {r['text']}" for r in results])
                prompt = (
                    f"Answer the user's question concisely based ONLY on the following retrieved chunks from '{source_metadata.name}':\n\n"
                    f"{context_str}\n\nQuestion: {request.question}"
                )
                ai_ans = ai_provider.generate_text(prompt)
                if ai_ans and ai_ans.strip():
                    summary_text = ai_ans.strip()
        except Exception:
            pass

        rows = [
            {
                "page": r.get("page_number", 1),
                "relevance_score": r.get("score", 0.0),
                "excerpt": r.get("text", ""),
            }
            for r in results
        ]

        history_service.log_query(
            question=request.question,
            query_source="rag",
            source_id=source_metadata.source_id,
            status="success",
            generated_mongo_query=rag_pipeline_str,
            row_count=len(rows),
            execution_time_ms=elapsed_ms,
        )

        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=rag_pipeline_str,
            generated_sql=rag_pipeline_str,
            columns=["page", "relevance_score", "excerpt"],
            rows=rows,
            row_count=len(rows),
            execution_time_ms=elapsed_ms,
            status="success",
            answer=AnswerModel(
                headline="DOCUMENT RAG RETRIEVAL",
                value=f"Page {top_chunk.get('page_number', 1)}",
                unit=f"({len(results)} chunks matched)",
                summary=summary_text,
            ),
            insights=[
                f"Retrieved {len(results)} vector-indexed chunks from `{source_metadata.name}`.",
                f"Top chunk cosine similarity score: {top_chunk.get('score', 0.0)}.",
            ],
            query_source="rag",
            sources=citations,
            confidence=routing_decision["confidence"],
        )

    # 5. Structured MongoDB Collection Execution
    DatabaseManager.set_active_database(source_metadata.source_id)

    # 5a. Deterministic Meta Query Router (fast schema/collection overview)
    meta_response = meta_router.route_meta_query(request.question)
    if meta_response:
        history_service.log_query(
            question=request.question,
            query_source="meta",
            source_id=source_metadata.source_id,
            status="success",
            generated_mongo_query=meta_response.get("generated_sql", ""),
            row_count=meta_response["row_count"],
            execution_time_ms=meta_response["execution_time_ms"],
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=meta_response.get("generated_sql", ""),
            generated_sql=meta_response.get("generated_sql", ""),
            columns=meta_response["columns"],
            rows=meta_response["rows"],
            row_count=meta_response["row_count"],
            execution_time_ms=meta_response["execution_time_ms"],
            status="success",
            query_source="meta",
            answer=AnswerModel(
                headline=meta_response.get("headline", "MONGODB OVERVIEW"),
                value=meta_response.get("value", str(meta_response["row_count"])),
                unit=meta_response.get("unit", "collections"),
                summary=meta_response.get("summary", ""),
            ),
            follow_up_suggestions=query_intelligence_service.generate_follow_up_suggestions(
                request.question, "", source_metadata.source_id
            ),
            sources=citations,
            confidence=routing_decision["confidence"],
        )

    # 5b. Intent verification
    intent = query_intelligence_service.analyze_intent(request.question, source_metadata.source_id)
    if intent == "UNRELATED":
        error_msg = "I couldn't find data related to that concept in the active MongoDB collections."
        history_service.log_query(
            question=request.question,
            query_source="intent_filter",
            source_id=source_metadata.source_id,
            status="error",
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error=error_msg,
            error_code="UNRELATED_QUERY",
        )

    # 5c. Generate Structured MongoDB Aggregation Pipeline (Hybrid Deterministic + AI)
    structured_query: dict[str, Any] | None = None
    query_source = "deterministic"

    # Try deterministic MongoQueryService first for fast, zero-hallucination pipelines
    try:
        structured_query = mongo_query_service.generate_structured_query(
            request.question, source_metadata.source_id
        )
        structured_query = MongoQueryValidator.validate_against_db(structured_query)
    except MongoQuerySafetyError as exc:
        error_msg = "The generated query was rejected because it did not meet MongoDB safety requirements."
        history_service.log_query(
            question=request.question,
            query_source="security_guard",
            source_id=source_metadata.source_id,
            status="error",
            error_message=str(exc),
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error=error_msg,
            error_code="UNSAFE_SQL",
        )
    except Exception:
        structured_query = None

    # If deterministic engine couldn't resolve and Gemini AI is configured, use AI structured generation
    if structured_query is None:
        ai_status = ai_service.get_status()
        if ai_status.get("configured") and ai_status.get("status") == "ready":
            schema_summary = schema_service.get_schema_summary(source_metadata.source_id).summary
            prompt = f"""You are a MongoDB Aggregation Pipeline expert.
Given the following MongoDB schema:
{schema_summary}

Translate the user question into a strictly read-only JSON object with this exact schema:
{{
  "collection": "<exact_collection_name>",
  "operation": "aggregate",
  "pipeline": [ ... valid MongoDB aggregation stages ... ],
  "limit": 50
}}

User Question: "{request.question}"
Return ONLY raw JSON (no markdown backticks). Never use $out, $merge, or $where."""
            try:
                ai_resp = ai_service.generate(prompt)
                raw_json = ai_resp["response"].strip()
                structured_query = MongoQueryValidator.validate_against_db(raw_json)
                query_source = "ai"
            except MongoQuerySafetyError:
                error_msg = "The generated query was rejected because it did not meet MongoDB safety requirements."
                return NaturalLanguageQueryResponse(
                    question=request.question,
                    status="error",
                    error=error_msg,
                    error_code="UNSAFE_SQL",
                    query_source="ai",
                )
            except Exception:
                structured_query = None

    if structured_query is None:
        error_msg = "I could not confidently map that question to the fields in the active MongoDB collections."
        history_service.log_query(
            question=request.question,
            query_source="fallback",
            source_id=source_metadata.source_id,
            status="error",
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            status="error",
            error=error_msg,
            error_code="UNRELATED_QUERY",
        )

    # 6. Execute Validated MongoDB Pipeline
    formatted_pipeline = MongoQueryValidator.format_human_readable(structured_query)
    citations[0]["table"] = structured_query["collection"]
    citations[0]["collection"] = structured_query["collection"]

    try:
        columns, rows, exec_time = query_executor.execute(structured_query)
        row_count = len(rows)

        analysis = query_intelligence_service.generate_analysis(
            formatted_pipeline, request.question, rows, columns
        )
        answer_dict = analysis.get("answer")
        insights = analysis.get("insights", [])
        follow_ups = query_intelligence_service.generate_follow_up_suggestions(
            request.question, formatted_pipeline, source_metadata.source_id
        )

        history_service.log_query(
            question=request.question,
            query_source=query_source,
            source_id=source_metadata.source_id,
            status="success",
            generated_mongo_query=formatted_pipeline,
            row_count=row_count,
            execution_time_ms=exec_time,
        )

        ans_obj = (
            AnswerModel(**answer_dict)
            if isinstance(answer_dict, dict)
            else AnswerModel(headline="MONGODB ANALYSIS COMPLETE", value=str(row_count), unit="documents")
        )

        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=formatted_pipeline,
            structured_query=structured_query,
            generated_sql=formatted_pipeline,
            columns=columns,
            rows=rows,
            row_count=row_count,
            execution_time_ms=round(exec_time, 2),
            status="success",
            query_source=query_source,
            answer=ans_obj,
            insights=insights,
            follow_up_suggestions=follow_ups,
            sources=citations,
            confidence=routing_decision["confidence"],
            error=(
                "Your question was understood, but 0 matching documents were found in the collection."
                if row_count == 0
                else None
            ),
        )

    except MongoQuerySafetyError:
        error_msg = "The generated query was rejected because it did not meet MongoDB safety requirements."
        history_service.log_query(
            question=request.question,
            query_source=query_source,
            source_id=source_metadata.source_id,
            status="error",
            generated_mongo_query=formatted_pipeline,
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=formatted_pipeline,
            generated_sql=formatted_pipeline,
            status="error",
            error=error_msg,
            error_code="UNSAFE_SQL",
            query_source=query_source,
        )
    except QueryExecutionError as exc:
        error_detail = str(exc).replace("Database error: ", "")
        error_msg = f"An error occurred while executing the MongoDB pipeline: {error_detail}"
        history_service.log_query(
            question=request.question,
            query_source=query_source,
            source_id=source_metadata.source_id,
            status="error",
            generated_mongo_query=formatted_pipeline,
            error_message=error_msg,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            generated_mongo_query=formatted_pipeline,
            generated_sql=formatted_pipeline,
            status="error",
            error=error_msg,
            error_code="QUERY_EXECUTION_ERROR",
            query_source=query_source,
        )
