from fastapi import APIRouter, HTTPException

from app.models.schema import DatabaseSchema, SchemaSummary, TableInfo
from app.services.schema_service import MongoSchemaService

router = APIRouter()
schema_service = MongoSchemaService()


@router.get("/schema", response_model=DatabaseSchema)
async def get_schema():
    try:
        return schema_service.get_schema()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving MongoDB schema: {exc}") from exc


@router.get("/schema/summary", response_model=SchemaSummary)
async def get_schema_summary():
    try:
        return schema_service.get_schema_summary()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generating schema summary: {exc}") from exc


@router.get("/schema/{table_name}", response_model=TableInfo)
async def get_table_schema(table_name: str):
    try:
        return schema_service.get_table_schema(table_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving collection schema: {exc}") from exc


@router.get("/collections")
async def list_collections():
    schema = schema_service.get_schema()
    return {"collections": schema.get("tables", [])}


@router.get("/collections/{name}/schema", response_model=TableInfo)
async def get_collection_schema(name: str):
    try:
        return schema_service.get_table_schema(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/collections/{name}/preview")
async def get_collection_preview(name: str, limit: int = 50):
    try:
        columns, rows = schema_service.get_table_sample(name, limit)
        return {"collection": name, "columns": columns, "rows": rows, "count": len(rows)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
