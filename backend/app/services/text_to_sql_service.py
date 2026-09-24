from typing import Any

from app.services.intent_classifier import QueryPlan, QueryPlannerEngine
from app.services.mongo_validator import MongoQueryValidator
from app.services.schema_service import MongoSchemaService


class MongoQueryService:
    """
    Deterministic + Schema-Aware Natural Language to MongoDB Aggregation Pipeline Engine.
    Uses QueryPlannerEngine so that LIST_RECORDS, FILTER, COUNT, TOP_N, MAXIMUM,
    AVERAGE, COMPARISON, and GROUP_BY queries strictly reflect user intent.
    """

    def __init__(self, schema_service: MongoSchemaService | None = None):
        self.schema_service = schema_service or MongoSchemaService()
        self.planner = QueryPlannerEngine(self.schema_service)

    def build_query_plan(
        self,
        question: str,
        source_id: str | None = None,
        source_name: str | None = None,
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> QueryPlan:
        MongoQueryValidator.validate_question_safety(question)
        return self.planner.build_plan(
            question=question,
            source_id=source_id,
            source_name=source_name,
            active_collection=active_collection,
            conversation_context=conversation_context,
        )

    def generate_structured_query(
        self,
        question: str,
        source_id: str | None = None,
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = self.build_query_plan(
            question=question,
            source_id=source_id,
            active_collection=active_collection,
            conversation_context=conversation_context,
        )
        if plan.intent in ("UNRELATED", "CLARIFICATION", "DATASET_OVERVIEW", "COLLECTION_OVERVIEW", "SCHEMA_QUERY"):
            raise ValueError(f"Non-collection query intent: {plan.intent}")
        return self.planner.compile_to_mongo_query(plan)

    def translate(self, question: str, source_id: str | None = None) -> str:
        structured = self.generate_structured_query(question, source_id)
        return MongoQueryValidator.format_human_readable(structured)


# Backwards-compatible alias
TextToSQLService = MongoQueryService
