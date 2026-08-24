from fastapi import APIRouter

from app.core.database import demo_db_provider
from app.models.query import SuggestionsResponse
from app.services.schema_service import SchemaService
from app.services.suggestions_service import SuggestionsService

router = APIRouter()
schema_service = SchemaService(demo_db_provider)
suggestions_service = SuggestionsService(schema_service)


@router.get("", response_model=SuggestionsResponse)
async def get_suggestions():
    """Retrieve intelligent query suggestions based on the database schema."""
    suggestions = suggestions_service.get_schema_suggestions()
    return SuggestionsResponse(suggestions=suggestions)
