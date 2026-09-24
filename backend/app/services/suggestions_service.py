from app.services.schema_service import MongoSchemaService


class SuggestionsService:
    """
    Generates MongoDB schema-aware natural language query suggestions for the active source.
    """

    def __init__(self, schema_service: MongoSchemaService | None = None):
        self.schema_service = schema_service or MongoSchemaService()

    def get_suggestions(self, source_id: str | None = None) -> list[str]:
        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        if not collections:
            return [
                "What collections are in this MongoDB database?",
                "What are the top 10 products by revenue?",
                "Which customers have spent more than ₹1 lakh?",
            ]

        suggestions: list[str] = []
        col_names = {c["name"].split("_")[-1] for c in collections}

        if "products" in col_names:
            suggestions.append("What are the top 10 products by revenue?")
        if "customers" in col_names:
            suggestions.append("Which customers have spent more than ₹1 lakh?")
        if "orders" in col_names:
            suggestions.append("Compare sales between January and February.")
        if "employees" in col_names:
            suggestions.append("Average salary by department")
        if "students" in col_names:
            suggestions.append("How many students have GPA above 3.5?")

        for col in collections[:2]:
            cname = col["name"].split("_")[-1]
            suggestions.append(f"How many documents are in {cname}?")

        return suggestions[:6]
