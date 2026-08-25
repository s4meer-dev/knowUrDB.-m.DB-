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

    def analyze_intent(self, question: str) -> str:
        """
        Classifies the user's question into one of three categories:
        - VALID: The question can likely be answered with a SQL query against this schema.
        - AMBIGUOUS: The question is related to databases/records, but relies on tables/concepts not in the schema, or is too vague.
        - UNRELATED: The question has nothing to do with this database or its data.
        Returns 'VALID', 'AMBIGUOUS', or 'UNRELATED'.
        """
        ai_status = self.ai_service.get_status()
        if not (ai_status.get("configured") and ai_status.get("status") == "ready"):
            # Deterministic Fallback Heuristic for UNRELATED questions
            return self._deterministic_intent_fallback(question)

        schema_summary = self.schema_service.get_schema_summary().summary

        prompt = f"""Given the following database schema summary, classify the user question into exactly one of these categories:
- VALID: The question can be answered with a SQL query against this schema.
- AMBIGUOUS: The question is related to records or databases, but relies on tables or concepts NOT in the schema (e.g. asking for 'records' when no 'records' table exists), or is too vague to write a safe query.
- UNRELATED: The question has nothing to do with this database or its data (e.g. weather, poetry, generic trivia).

Schema:
{schema_summary}

Question: "{question}"

Return ONLY the classification word: VALID, AMBIGUOUS, or UNRELATED.
"""
        try:
            response = self.ai_service.generate(prompt)
            intent = response["response"].strip().upper()
            if intent in ["VALID", "AMBIGUOUS", "UNRELATED"]:
                return intent
            return self._deterministic_intent_fallback(question)
        except Exception:  # noqa: BLE001
            return self._deterministic_intent_fallback(question)

    def _deterministic_intent_fallback(self, question: str) -> str:
        """
        If AI is down, we use a basic keyword search to catch obviously unrelated questions
        (e.g., weather, joke, president). If it has ANY database keywords or table names, we assume VALID.
        """
        q = question.lower()

        # Check against schema names
        tables = self.schema_service.get_table_names()
        for t in tables:
            if t.lower() in q:
                return "VALID"
            # simple singular check (e.g. 'student' matches 'students' table)
            if t.endswith("s") and t[:-1].lower() in q:
                return "VALID"

        db_keywords = [
            "database",
            "table",
            "record",
            "row",
            "data",
            "schema",
            "structure",
            "summary",
            "student",
            "department",
            "course",
            "instructor",
            "enrollment",
            "mark",
            "scholarship",
            "attendance",
            "profile",
            "credits",
            "score",
            "grade",
        ]

        # We need at least one strong keyword. 'what', 'which' are too generic.
        # But also, we need to make sure we don't accidentally block valid questions like "count all"

        # Let's tokenize and check word by word to avoid substring matches like "data" in "metadata"
        # though "data" is fine, but "row" in "crowd" is bad.
        import re

        words = set(re.findall(r"\b\w+\b", q))

        # Check if any exact word matches a strong DB keyword
        if any(kw in words for kw in db_keywords):
            return "VALID"

        # Also check for exact multi-word strong phrases
        strong_phrases = [
            "how many",
            "total number",
            "average score",
            "list all",
            "show me",
        ]
        if any(phrase in q for phrase in strong_phrases):
            return "VALID"

        return "UNRELATED"

    def repair_sql(self, question: str, bad_sql: str, error_message: str) -> str | None:
        """
        Attempts to repair an invalid SQL query based on the database execution error.
        Returns the repaired SQL string, or None if repair fails/AI is unavailable.
        """
        ai_status = self.ai_service.get_status()
        if not (ai_status.get("configured") and ai_status.get("status") == "ready"):
            return None

        schema_summary = self.schema_service.get_schema_summary().summary

        prompt = f"""The following SQL query was generated for the question '{question}':
{bad_sql}

But it failed database validation with the following error:
{error_message}

Please correct the SQL query using ONLY the provided schema. Do not invent tables, columns, or relationships.

Schema:
{schema_summary}

IMPORTANT RULES:
- Return ONLY the raw SQL query.
- Do NOT wrap the SQL in markdown formatting or backticks (no ```sql ... ```).
- Do NOT include any explanations or conversational text.
- Only generate SELECT statements. No data mutation is allowed.
"""
        try:
            response = self.ai_service.generate(prompt)
            sql = response["response"].strip()
            # Clean up markdown if AI includes it
            if sql.startswith("```sql"):
                sql = sql[6:]
            elif sql.startswith("```"):
                sql = sql[3:]
            sql = sql.removesuffix("```")
            return sql.strip()
        except Exception:  # noqa: BLE001
            return None

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
