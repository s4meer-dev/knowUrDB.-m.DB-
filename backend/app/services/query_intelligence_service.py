from typing import Any

from app.services.intent_classifier import QueryPlannerEngine
from app.services.presentation_planner import PresentationPlanner
from app.services.schema_service import MongoSchemaService


class QueryIntelligenceService:
    """
    Provides MongoDB-aware intent classification, intent-faithful result presentation,
    pipeline repair, and schema-grounded follow-up question suggestions.
    Never invents rankings ('Top Result by Price') when the user asked for a list or filter.
    """

    def __init__(self, ai_service: Any, schema_service: MongoSchemaService | None = None):
        self.ai_service = ai_service
        self.schema_service = schema_service or MongoSchemaService()
        self.planner = QueryPlannerEngine(self.schema_service)

    def analyze_intent(
        self,
        question: str,
        source_id: str | None = None,
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> str:
        if not question or not question.strip():
            return "UNRELATED"
        plan = self.planner.build_plan(
            question=question,
            source_id=source_id,
            active_collection=active_collection,
            conversation_context=conversation_context,
        )
        return plan.intent

    def generate_analysis(
        self,
        mongo_query: str,
        question: str,
        rows: list[dict[str, Any]],
        columns: list[str],
        source_id: str | None = None,
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generates a structured AnswerModel dict, PresentationContract, insights, and follow-ups
        strictly aligned with the user's intent.
        """
        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        plan = self.planner.build_plan(
            question=question,
            source_id=source_id,
            active_collection=active_collection,
            conversation_context=conversation_context,
        )
        planned = PresentationPlanner.plan_presentation(plan, rows, columns, collections)
        return {
            "intent": plan.intent,
            "collection": plan.collection,
            "presentation": planned["presentation"],
            "answer": planned["answer"],
            "insights": planned.get("insights", []),
            "follow_ups": planned.get("follow_ups", []),
            "columns": planned.get("columns", columns),
            "rows": planned.get("rows", rows),
        }

    def generate_follow_up_suggestions(
        self, question: str, mongo_query: str = "", source_id: str | None = None
    ) -> list[str]:
        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        if not collections:
            return []
        plan = self.planner.build_plan(question=question, source_id=source_id)
        return PresentationPlanner._generate_follow_ups(plan, collections)

    def repair_mongo_query(
        self, question: str, broken_query: str, error_msg: str, source_id: str | None = None
    ) -> dict[str, Any] | None:
        from app.services.text_to_sql_service import MongoQueryService

        try:
            return MongoQueryService(self.schema_service).generate_structured_query(question, source_id)
        except Exception:
            return None
