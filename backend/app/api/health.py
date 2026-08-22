from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic application health check endpoint.
    """
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION
    )
