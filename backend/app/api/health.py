from app.core.config import settings
from fastapi import APIRouter
from pydantic import BaseModel

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
