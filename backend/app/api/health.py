from fastapi import APIRouter

from app.core.config import settings
from app.core.mongodb import MongoDBManager

router = APIRouter()


@router.get("/health")
async def health_check():
    mongo_status = MongoDBManager.ping()
    return {
        "status": "ok" if mongo_status.get("connected") else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": mongo_status,
    }
