from app.api.health import router as health_router
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for knowUrDB",
)

# CORS configuration
if settings.ENVIRONMENT == "development":
    origins = [
        settings.FRONTEND_URL,
        "http://127.0.0.1:5173"
    ]
else:
    # Fallback to no origins allowed, require specific config in prod
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
