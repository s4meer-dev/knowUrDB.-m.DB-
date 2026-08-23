from fastapi import APIRouter, HTTPException

from app.core.database import demo_db_provider
from app.models.schema import DatabaseSchema, SchemaSummary, TableInfo
from app.services.schema_service import SchemaService

router = APIRouter()

# In a real app, these would be injected dependencies
schema_service = SchemaService(demo_db_provider)


@router.get("/schema", response_model=DatabaseSchema)
async def get_database_schema():
    """
    Returns the complete structured database schema.
    """
    try:
        return schema_service.get_schema()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/summary", response_model=SchemaSummary)
async def get_schema_summary():
    """
    Returns a human-readable schema description suitable for future AI prompting.
    """
    try:
        return schema_service.get_schema_summary()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{table_name}", response_model=TableInfo)
async def get_table_schema(table_name: str):
    """
    Returns detailed schema information for one valid table.
    """
    try:
        return schema_service.get_table_schema(table_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
