import re
from dataclasses import dataclass, field
from typing import Any

from app.services.schema_service import SchemaService


@dataclass
class QueryPlan:
    intent: str
    entity: str
    metrics: list[str] = field(default_factory=list)
    filters: list[dict[str, Any]] = field(default_factory=list)
    group_by: str | None = None
    having: str | None = None
    order_by: str | None = None
    limit: int | None = None
    custom_sql: str | None = None


class TextToSQLService:
    """
    Deterministic Text-to-SQL translation engine used strictly as a fallback
    when AI is unavailable. It attempts to parse very basic questions.
    """

    def __init__(self, schema_service: SchemaService):
        self.schema_service = schema_service

    def normalize_question(self, question: str) -> str:
        q = question.lower().strip()
        q = q.removesuffix("?")
        q = q.replace(".", "")
        return q.strip()

    def create_query_plan(self, question: str) -> QueryPlan:
        q = self.normalize_question(question)

        # Basic NLP-Lite Fallback
        q_clean = re.sub(r'[^\w\s]', '', q)
        q_clean = re.sub(r'\s+', ' ', q_clean)
        words = q_clean.split()
        
        forbidden_keywords = {"delete", "drop", "update", "insert", "alter", "create"}
        if forbidden_keywords.intersection(set(words)):
            raise ValueError(f"Could not parse question safely: {question}")
            
        valid_tables = self.schema_service.get_table_names()
        
        def find_entity(token_list: list[str]) -> str | None:
            for w in token_list:
                for t in valid_tables:
                    if w == t or w + "s" == t or (w.endswith("s") and w[:-1] == t):
                        return t
            joined = "_".join(token_list)
            for t in valid_tables:
                if t in joined or t.replace("_", "") in "".join(token_list):
                    return t
            return None

        entity = find_entity(words)

        if entity:
            count_keywords = {"count", "number", "how", "many", "total"}
            is_count = bool(count_keywords.intersection(set(words)))

            if is_count:
                return QueryPlan(intent="count", entity=entity, metrics=["*"])
            return QueryPlan(intent="select", entity=entity, metrics=["*"])

        # Default fallback
        raise ValueError(f"Could not parse question deterministically: {question}")

    def generate_sql(self, plan: QueryPlan) -> str:
        if plan.intent == "custom" and plan.custom_sql:
            return plan.custom_sql

        # Basic SQL Builder
        select_clause = ", ".join(plan.metrics)
        if (
            plan.intent == "count"
            and not select_clause
            or plan.intent == "count"
            and select_clause == "*"
        ):
            select_clause = "COUNT(*)"

        sql = f"SELECT {select_clause} FROM {plan.entity}"

        if plan.filters:
            conditions = []
            for f in plan.filters:
                val = f["val"]
                if f.get("type") == "str":
                    val = f"'{val.replace("'", "''")}'"

                conditions.append(f"{f['col']} {f['op']} {val}")
            sql += f" WHERE {' AND '.join(conditions)}"

        if plan.group_by:
            sql += f" GROUP BY {plan.group_by}"

        if plan.having:
            sql += f" HAVING {plan.having}"

        if plan.order_by:
            sql += f" ORDER BY {plan.order_by}"

        if plan.limit is not None:
            sql += f" LIMIT {plan.limit}"

        return sql + ";"

    def translate(self, question: str) -> str:
        """
        Main pipeline method: Text -> Plan -> SQL
        """
        plan = self.create_query_plan(question)
        sql = self.generate_sql(plan)
        return sql
