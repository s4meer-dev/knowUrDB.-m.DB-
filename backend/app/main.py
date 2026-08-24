from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.query import router as query_router
from app.api.schema import router as schema_router
from app.api.suggestions import router as suggestions_router
from app.core.app_database import app_db_provider
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize application database on startup
    app_db_provider.init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for knowUrDB",
    lifespan=lifespan,
)

# CORS configuration
if settings.ENVIRONMENT == "development":
    origins = [settings.FRONTEND_URL, "http://127.0.0.1:5173"]
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
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(schema_router, prefix="/api", tags=["schema"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(history_router, prefix="/api/history", tags=["history"])
app.include_router(suggestions_router, prefix="/api/suggestions", tags=["suggestions"])
