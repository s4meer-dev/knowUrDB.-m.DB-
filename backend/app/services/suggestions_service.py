from app.services.schema_service import SchemaService


class SuggestionsService:
    def __init__(self, schema_service: SchemaService):
        self.schema_service = schema_service

    def get_schema_suggestions(self, max_suggestions: int = 5) -> list[str]:
        """
        Generates natural language suggestions based on the actual database schema.
        Handles schemas of various sizes and types.
        """
        schema = self.schema_service.get_schema()
        if not schema.tables:
            return []

        suggestions = set()

        # 1. Simple table counts
        for table in schema.tables[:3]:
            suggestions.add(f"How many records are in {table.name}?")
            suggestions.add(f"Show me all {table.name}")

        # 2. Look for numeric columns for aggregations
        numeric_types = ["INTEGER", "REAL", "NUMERIC", "FLOAT"]
        for table in schema.tables:
            for col in table.columns:
                if (
                    any(t in col.data_type.upper() for t in numeric_types)
                    and not col.primary_key
                    and not col.name.endswith("_id")  # Avoid averaging foreign keys
                ):
                    suggestions.add(
                        f"What is the average of {col.name} in {table.name}?"
                    )
                    suggestions.add(f"Which {table.name} has the highest {col.name}?")
                    break  # One per table is enough

        # 3. Distinct values or categories
        for table in schema.tables:
            for col in table.columns:
                if (
                    (
                        "TEXT" in col.data_type.upper()
                        or "VARCHAR" in col.data_type.upper()
                    )
                    and col.name not in ["id", "uuid"]
                    and not col.primary_key
                ):
                    suggestions.add(
                        f"What are the distinct values of {col.name} in {table.name}?"
                    )
                    break  # One per table

        # Limit and convert to list
        suggestions_list = list(suggestions)
        # Sort for determinism
        suggestions_list.sort()
        return suggestions_list[:max_suggestions]
