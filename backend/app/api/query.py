import logging
import time
import uuid
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import DatabaseManager
from app.core.mongodb import MongoDBManager
from app.models.query import (
    AnswerModel,
    ClarificationCandidate,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
)
from app.services.ai_service import AIService
from app.services.document_processor import DocumentProcessor
from app.services.gemini_provider import GeminiProvider
from app.services.history_service import HistoryService
from app.services.meta_query_router import MetaQueryRouter
from app.services.mongo_validator import MongoQuerySafetyError, MongoQueryValidator
from app.services.presentation_planner import PresentationPlanner
from app.services.query_executor import MongoQueryExecutor, QueryExecutionError
from app.services.query_intelligence_service import QueryIntelligenceService
from app.services.query_router import QueryRouter
from app.services.schema_service import MongoSchemaService
from app.services.source_manager import SourceManager
from app.services.text_to_sql_service import MongoQueryService

logger = logging.getLogger("knowurdb.query")

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
    request_id = f"req-{uuid.uuid4().hex[:8]}"
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
            intent="UNSAFE",
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
            intent="UNRELATED",
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
        summary_text = f"You have {len(sources)} connected MongoDB sources: {', '.join(names)}."
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent="METADATA_QUERY",
            presentation={
                "type": "dataset_overview",
                "title": "Available Data Sources",
                "subtitle": f"{len(sources)} connected sources",
                "summary": summary_text,
                "primary_value": str(len(sources)),
                "primary_unit": "sources",
                "show_technical_by_default": False,
            },
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
                summary=summary_text,
            ),
            query_source="meta",
            confidence=routing_decision["confidence"],
        )

    if routing_decision["decision"] == "CLARIFICATION":
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent="CLARIFICATION",
            presentation={
                "type": "clarification",
                "title": "Select Data Source",
                "summary": "I found matching collections in multiple sources. Which source should I use?",
            },
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
        summary_text = f"Compared {len(comparison_rows)} MongoDB collections across {len(citations)} sources ({', '.join(c['name'] for c in citations)})."
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent="MULTI_SOURCE",
            presentation={
                "type": "comparison",
                "title": "Multi-Source Comparison",
                "subtitle": f"{len(citations)} sources compared",
                "summary": summary_text,
                "primary_value": str(len(citations)),
                "primary_unit": "sources compared",
                "show_technical_by_default": False,
            },
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
                summary=summary_text,
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
            intent="ERROR",
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
                intent="DOCUMENT_RAG",
                presentation={
                    "type": "empty",
                    "title": "No Matching Document Sections",
                    "summary": "No relevant sections were found in the document for that question.",
                },
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
            intent="DOCUMENT_RAG",
            presentation={
                "type": "document_answer",
                "title": source_metadata.name,
                "subtitle": f"Page {top_chunk.get('page_number', 1)} • {len(results)} matching excerpts",
                "summary": summary_text,
                "primary_value": f"Page {top_chunk.get('page_number', 1)}",
                "primary_unit": f"{len(results)} excerpts",
                "show_technical_by_default": False,
            },
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

    # 5. Structured MongoDB Collection Intelligence Pipeline
    DatabaseManager.set_active_database(source_metadata.source_id)
    schema = schema_service.get_schema(source_metadata.source_id)
    collections = schema.get("tables", [])

    plan = mongo_query_service.build_query_plan(
        question=request.question,
        source_id=source_metadata.source_id,
        source_name=source_metadata.name,
        active_collection=request.active_collection,
        conversation_context=request.conversation_context,
    )

    # 5A. DATASET_OVERVIEW or COLLECTION_OVERVIEW (All Collections)
    if plan.intent in ("DATASET_OVERVIEW", "COLLECTION_OVERVIEW") and not plan.collection:
        start_ms = time.perf_counter()
        overview_payload = PresentationPlanner.build_dataset_overview(
            source_metadata.name, collections
        )
        elapsed_ms = round((time.perf_counter() - start_ms) * 1000.0, 2)
        pipeline_str = "db.getCollectionInfos()"
        history_service.log_query(
            question=request.question,
            query_source="meta",
            source_id=source_metadata.source_id,
            status="success",
            generated_mongo_query=pipeline_str,
            row_count=len(overview_payload["rows"]),
            execution_time_ms=elapsed_ms,
        )
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent=plan.intent,
            query_plan=asdict(plan),
            presentation=overview_payload["presentation"],
            generated_mongo_query=pipeline_str,
            generated_sql=pipeline_str,
            columns=overview_payload["columns"],
            rows=overview_payload["rows"],
            row_count=len(overview_payload["rows"]),
            execution_time_ms=elapsed_ms,
            status="success",
            query_source="meta",
            answer=AnswerModel(**overview_payload["answer"]),
            insights=overview_payload["insights"],
            follow_up_suggestions=overview_payload["follow_ups"],
            sources=citations,
            confidence=plan.confidence,
        )

    # 5B. SCHEMA_QUERY ("what fields are available?", "show schema of products")
    if plan.intent == "SCHEMA_QUERY":
        start_ms = time.perf_counter()
        schema_payload = PresentationPlanner.build_schema_presentation(
            source_metadata.name, collections, plan.collection
        )
        elapsed_ms = round((time.perf_counter() - start_ms) * 1000.0, 2)
        pipeline_str = f"db.{plan.collection or 'collections'}.findOne()"
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent=plan.intent,
            collection=plan.collection,
            query_plan=asdict(plan),
            presentation=schema_payload["presentation"],
            generated_mongo_query=pipeline_str,
            generated_sql=pipeline_str,
            columns=schema_payload["columns"],
            rows=schema_payload["rows"],
            row_count=len(schema_payload["rows"]),
            execution_time_ms=elapsed_ms,
            status="success",
            query_source="meta",
            answer=AnswerModel(**schema_payload["answer"]),
            insights=schema_payload["insights"],
            follow_up_suggestions=schema_payload["follow_ups"],
            sources=citations,
            confidence=plan.confidence,
        )

    # 5C. Specific COLLECTION_OVERVIEW ("tell me about the products collection")
    if plan.intent == "COLLECTION_OVERVIEW" and plan.collection:
        # Execute a preview find/aggregate on that collection + schema overview
        plan.intent = "LIST_RECORDS"
        plan.target_fields = [
            c["name"]
            for col in collections
            if col["name"] == plan.collection
            for c in col.get("columns", [])
            if "." not in c["name"] and "[]" not in c["name"] and c["name"] != "_id"
        ][:8]

    # 5D. CLARIFICATION (Ambiguous collection or non-existent collection)
    if plan.intent == "CLARIFICATION":
        return NaturalLanguageQueryResponse(
            question=request.question,
            intent="CLARIFICATION",
            query_plan=asdict(plan),
            presentation={
                "type": "clarification",
                "title": "NEED A LITTLE MORE CONTEXT",
                "summary": plan.clarification_message,
                "candidate_collections": plan.clarification_options,
            },
            status="clarification_required",
            error=plan.clarification_message,
            candidates=[
                ClarificationCandidate(
                    source_id=opt.get("source_id") or source_metadata.source_id,
                    name=opt.get("name") or opt.get("collection", ""),
                    collection=opt.get("collection"),
                    document_count=opt.get("document_count"),
                    field_count=opt.get("field_count"),
                    fields_preview=opt.get("fields_preview", []),
                    description=opt.get("description"),
                )
                for opt in plan.clarification_options
            ],
            confidence=plan.confidence,
        )

    # 5E. UNRELATED
    if plan.intent == "UNRELATED":
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
            intent="UNRELATED",
            status="error",
            error=error_msg,
            error_code="UNRELATED_QUERY",
        )

    # 6. Compile Structured MongoDB Query from QueryPlan
    structured_query: dict[str, Any] | None = None
    query_source = "deterministic"

    try:
        structured_query = mongo_query_service.planner.compile_to_mongo_query(plan)
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
            intent="ERROR",
            status="error",
            error=error_msg,
            error_code="UNSAFE_SQL",
        )
    except Exception:
        structured_query = None

    # AI Fallback if deterministic compilation could not produce a valid pipeline
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
                    intent="ERROR",
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
            intent="UNRELATED",
            status="error",
            error=error_msg,
            error_code="UNRELATED_QUERY",
        )

    # 7. Execute Validated MongoDB Pipeline & Plan Presentation
    formatted_pipeline = MongoQueryValidator.format_human_readable(structured_query)
    citations[0]["table"] = structured_query["collection"]
    citations[0]["collection"] = structured_query["collection"]

    try:
        columns, rows, exec_time = query_executor.execute(structured_query)
        planned_ui = PresentationPlanner.plan_presentation(plan, rows, columns, collections)

        final_cols = planned_ui.get("columns", columns)
        final_rows = planned_ui.get("rows", rows)
        row_count = len(final_rows)

        logger.info(
            "QueryExecuted request_id=%s intent=%s source=%s collection=%s rows=%d exec_ms=%.2f presentation=%s",
            request_id,
            plan.intent,
            source_metadata.source_id,
            structured_query["collection"],
            row_count,
            exec_time,
            planned_ui["presentation"]["type"],
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

        return NaturalLanguageQueryResponse(
            question=request.question,
            intent=plan.intent,
            collection=structured_query["collection"],
            query_plan=asdict(plan),
            presentation=planned_ui["presentation"],
            generated_mongo_query=formatted_pipeline,
            structured_query=structured_query,
            generated_sql=formatted_pipeline,
            columns=final_cols,
            rows=final_rows,
            row_count=row_count,
            execution_time_ms=round(exec_time, 2),
            status="success",
            query_source=query_source,
            answer=AnswerModel(**planned_ui["answer"]),
            insights=planned_ui.get("insights", []),
            follow_up_suggestions=planned_ui.get("follow_ups", []),
            sources=citations,
            confidence=plan.confidence,
            error=(
                planned_ui["answer"]["summary"]
                if row_count == 0 and plan.intent != "COUNT"
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
            intent="ERROR",
            generated_mongo_query=formatted_pipeline,
            generated_sql=formatted_pipeline,
            status="error",
            error=error_msg,
            error_code="UNSAFE_SQL",
            query_source=query_source,
        )
    except QueryExecutionError as exc:
        error_detail = str(exc).replace("Database error: ", "")
        error_msg = f"I couldn't complete that query because an operation failed on the selected collection: {error_detail}"
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
            intent="ERROR",
            generated_mongo_query=formatted_pipeline,
            generated_sql=formatted_pipeline,
            status="error",
            error=error_msg,
            error_code="QUERY_EXECUTION_ERROR",
            query_source=query_source,
        )
