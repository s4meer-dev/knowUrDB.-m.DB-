from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.query import QueryHistoryItem
from app.services.history_service import HistoryService

router = APIRouter()
history_service = HistoryService()


class SuccessResponse(BaseModel):
    message: str


@router.get("", response_model=list[QueryHistoryItem])
async def get_history(limit: int = Query(50, ge=1, le=100)):
    """Retrieve recent query history."""
    return history_service.get_history(limit=limit)


@router.get("/{query_id}", response_model=QueryHistoryItem)
async def get_history_item(query_id: str):
    """Retrieve a specific query history item by ID."""
    item = history_service.get_history_item(query_id)
    if not item:
        raise HTTPException(status_code=404, detail="Query history not found")
    return item


@router.delete("/{query_id}", response_model=SuccessResponse)
async def delete_history_item(query_id: str):
    """Delete a specific query history item by ID."""
    deleted = history_service.delete_history_item(query_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query history not found")
    return SuccessResponse(message="Query history item deleted")


@router.delete("", response_model=SuccessResponse)
async def clear_history():
    """Clear all query history."""
    history_service.clear_history()
    return SuccessResponse(message="All query history cleared")
