import re

from app.services.ai_service import AIService
from app.services.schema_service import SchemaService


class QueryIntelligenceService:
    """
    Provides intelligent explanations and follow-up suggestions for executed queries.
    Gracefully falls back if AI is unavailable.
    """

    def __init__(self, ai_service: AIService, schema_service: SchemaService):
        self.ai_service = ai_service
        self.schema_service = schema_service

    def generate_explanation(self, sql: str, question: str) -> str | None:
        """
        Generates a plain-English explanation for the given SQL query.
        Returns None if generation fails, so as not to break the main query flow.
        """
        if not sql:
            return None

        # 1. Try AI explanation
        ai_status = self.ai_service.get_status()
        if ai_status.get("configured") and ai_status.get("status") == "ready":
            prompt = f"""Explain this SQL query in a short, simple sentence for a non-technical user.
Do not use technical terms like 'JOIN', 'GROUP BY', or 'ORDER BY'.
Just explain what the query is finding based on their question.

Question: "{question}"
SQL: {sql}

Explanation:"""
            try:
                response = self.ai_service.generate(prompt)
                return response["response"].strip()
            except Exception:  # noqa: BLE001, S110
                # Ignore AI errors and fall back
                pass

        # 2. Deterministic fallback
        return self._generate_deterministic_explanation(sql)

    def _generate_deterministic_explanation(self, sql: str) -> str | None:
        """Simple deterministic explanation for common SQL patterns."""
        sql_upper = sql.upper()
        if "COUNT(" in sql_upper and "GROUP BY" not in sql_upper:
            return (
                "This query counts the total number of records matching your criteria."
            )
        if "SELECT * " in sql_upper and "WHERE" not in sql_upper:
            return "This query retrieves all the available records."
        if "ORDER BY" in sql_upper and "DESC" in sql_upper and "LIMIT" in sql_upper:
            return "This query sorts the results to find the top records matching your criteria."

        return "This query retrieves data from the database based on your question."

    def generate_follow_up_suggestions(self, question: str, sql: str) -> list[str]:
        """
        Generates follow-up question suggestions based on the current context.
        Returns empty list if generation fails.
        """
        if not sql:
            return []

        ai_status = self.ai_service.get_status()
        if not (ai_status.get("configured") and ai_status.get("status") == "ready"):
            return []

        schema_summary = self.schema_service.get_schema_summary().summary

        prompt = f"""Based on the database schema and the user's previous question, suggest exactly 3 brief follow-up questions the user might want to ask next.

Schema:
{schema_summary}

Previous Question: "{question}"
Previous SQL: {sql}

Provide the suggestions as a simple bulleted list. Do not repeat the previous question. Do not hallucinate tables or columns not in the schema. Do not include introductory text.

Follow-ups:"""

        try:
            response = self.ai_service.generate(prompt)
            lines = response["response"].split("\n")

            suggestions = []
            for line in lines:
                cleaned = re.sub(r"^[-*•0-9.]+\s*", "", line.strip())
                if cleaned and cleaned.lower() != question.lower():
                    suggestions.append(cleaned)

            # Return max 3
            return suggestions[:3]
        except Exception:  # noqa: BLE001
            return []
