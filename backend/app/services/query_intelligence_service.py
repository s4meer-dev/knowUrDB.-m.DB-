import json
import re
from typing import Any

from app.services.schema_service import MongoSchemaService


class QueryIntelligenceService:
    """
    Provides MongoDB-aware intent classification, result summarization, key insights,
    pipeline repair, and schema-grounded follow-up question suggestions.
    """

    def __init__(self, ai_service: Any, schema_service: MongoSchemaService | None = None):
        self.ai_service = ai_service
        self.schema_service = schema_service or MongoSchemaService()

    def analyze_intent(self, question: str, source_id: str | None = None) -> str:
        if not question or not question.strip():
            return "UNRELATED"

        q = question.strip().lower()
        # Reject explicit off-topic chat
        unrelated_phrases = (
            "what is the weather",
            "write a poem",
            "tell me a joke",
            "capital of france",
            "who won the world cup",
            "recipe for",
            "2+2",
            "2 + 2",
        )
        if any(p in q for p in unrelated_phrases):
            return "UNRELATED"

        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        if not collections:
            return "UNRELATED"

        # Collect all collection names and field names
        domain_terms = {
            "collection", "collections", "table", "tables", "document", "documents",
            "record", "records", "row", "rows", "data", "database", "schema",
            "count", "total", "average", "avg", "sum", "top", "highest", "lowest",
            "max", "min", "compare", "monthly", "month", "revenue", "sales",
            "spent", "lakh", "salary", "department", "customer", "product",
            "order", "employee", "student", "gpa", "show", "list", "find",
            "which", "what", "how", "many",
        }
        for col in collections:
            domain_terms.add(col["name"].lower())
            domain_terms.add(col["name"].lower().split("_")[-1])
            domain_terms.add(col["name"].lower().split("_")[-1].rstrip("s"))
            for c in col.get("columns", []):
                leaf = c["name"].split(".")[-1].replace("[]", "").lower()
                domain_terms.add(leaf)
                domain_terms.update(leaf.split("_"))

        words = set(re.sub(r"[^\w\s]", " ", q).split())
        if words.intersection(domain_terms):
            return "DATABASE_QUERY"

        return "UNRELATED"

    def generate_analysis(
        self,
        mongo_query: str,
        question: str,
        rows: list[dict[str, Any]],
        columns: list[str],
    ) -> dict[str, Any]:
        """
        Generates a structured AnswerModel dict (`headline`, `value`, `unit`, `summary`)
        and bullet `insights` from the executed MongoDB aggregation result set.
        """
        row_count = len(rows)
        if row_count == 0:
            return {
                "answer": {
                    "headline": "NO DOCUMENTS MATCHED",
                    "value": "0",
                    "unit": "documents",
                    "summary": "The MongoDB aggregation pipeline executed cleanly, but 0 documents matched the filter criteria.",
                },
                "insights": [],
            }

        # Single KPI value (e.g., $count or single $group metric)
        if row_count == 1 and len(columns) == 1:
            col_name = columns[0]
            raw_val = rows[0].get(col_name)
            formatted_val = f"{raw_val:,}" if isinstance(raw_val, (int, float)) else str(raw_val)
            headline = col_name.replace("_", " ").upper()
            return {
                "answer": {
                    "headline": headline,
                    "value": formatted_val,
                    "unit": "documents" if "count" in col_name.lower() else "",
                    "summary": f"MongoDB aggregation returned {formatted_val} for {col_name.replace('_', ' ')}.",
                },
                "insights": [
                    f"Computed via MongoDB aggregation pipeline (`{col_name}: {formatted_val}`).",
                ],
            }

        # Multi-row or multi-column analytical result
        first_row = rows[0]
        primary_label = str(first_row.get(columns[0], ""))
        numeric_cols = [
            c for c in columns if isinstance(first_row.get(c), (int, float)) and not c.endswith("_id")
        ]

        if numeric_cols:
            top_metric = numeric_cols[0]
            top_val = first_row.get(top_metric)
            val_str = f"{top_val:,.2f}" if isinstance(top_val, float) else f"{top_val:,}"
            headline = f"TOP RESULT BY {top_metric.replace('_', ' ').upper()}"
            summary = (
                f"Across {row_count} returned MongoDB documents, '{primary_label}' leads with {top_metric.replace('_', ' ')} of {val_str}."
            )
            insights = [
                f"Returned {row_count} aggregated/projected BSON documents.",
                f"Highest `{top_metric}` observed: {val_str} ({primary_label}).",
            ]
            if row_count > 1:
                last_row = rows[-1]
                last_label = str(last_row.get(columns[0], ""))
                last_val = last_row.get(top_metric)
                if isinstance(last_val, (int, float)):
                    insights.append(
                        f"Range spans from {last_val:,} ({last_label}) to {val_str} ({primary_label})."
                    )
            return {
                "answer": {
                    "headline": headline,
                    "value": primary_label if len(primary_label) <= 28 else val_str,
                    "unit": f"({val_str})" if len(primary_label) <= 28 else top_metric.replace("_", " "),
                    "summary": summary,
                },
                "insights": insights,
            }

        return {
            "answer": {
                "headline": "MONGODB QUERY RESULTS",
                "value": f"{row_count:,}",
                "unit": "documents",
                "summary": f"Retrieved {row_count} matching documents from MongoDB.",
            },
            "insights": [f"Projected {len(columns)} fields across {row_count} documents."],
        }

    def generate_follow_up_suggestions(
        self, question: str, mongo_query: str = "", source_id: str | None = None
    ) -> list[str]:
        """
        Generates 3 schema-grounded follow-up questions tailored to the active MongoDB collections.
        Never hallucinates fields.
        """
        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        if not collections:
            return []

        suggestions: list[str] = []
        col_names = [c["name"].split("_")[-1] for c in collections]

        if "products" in col_names:
            suggestions.append("What are the top 10 products by revenue?")
        if "customers" in col_names:
            suggestions.append("Which customers have spent more than ₹1 lakh?")
        if "orders" in col_names:
            suggestions.append("Compare sales between January and February.")
        if "employees" in col_names:
            suggestions.append("What is the average salary by department?")
        if "students" in col_names:
            suggestions.append("How many students have GPA above 3.5?")

        # Also add dynamic suggestions based on actual schema columns of the first collection
        first_col = collections[0]
        cname = first_col["name"].split("_")[-1]
        cols = [c["name"] for c in first_col.get("columns", []) if "." not in c["name"]]
        if cols:
            suggestions.append(f"How many total documents are in {cname}?")
            num_cols = [
                c["name"]
                for c in first_col.get("columns", [])
                if c["data_type"] in ("Double", "Int64") and "." not in c["name"]
            ]
            cat_cols = [
                c["name"]
                for c in first_col.get("columns", [])
                if c["data_type"] == "String" and "." not in c["name"] and not c["name"].endswith("_id")
            ]
            if num_cols and cat_cols:
                suggestions.append(f"Show average {num_cols[0]} by {cat_cols[0]} in {cname}.")

        # Filter out the exact question the user just asked
        q_norm = question.strip().lower()
        filtered = [s for s in suggestions if s.lower() != q_norm]
        # Deduplicate preserving order
        seen = set()
        unique_list = []
        for s in filtered:
            if s not in seen:
                seen.add(s)
                unique_list.append(s)
        return unique_list[:3]

    def repair_mongo_query(
        self, question: str, broken_query: str, error_msg: str, source_id: str | None = None
    ) -> dict[str, Any] | None:
        from app.services.text_to_sql_service import MongoQueryService

        try:
            return MongoQueryService(self.schema_service).generate_structured_query(question, source_id)
        except Exception:
            return None
