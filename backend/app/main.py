from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.query import router as query_router
from app.api.schema import router as schema_router
from app.api.sources import generate_demo_source
from app.api.sources import router as sources_router
from app.api.suggestions import router as suggestions_router
from app.core.app_database import app_db_provider
from app.core.config import settings
from app.core.mongodb import MongoDBManager
from app.services.document_processor import DocumentProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_db_provider.init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MongoDB-Native Natural Language & Multi-Source Data Intelligence API",
    lifespan=lifespan,
)

if settings.ENVIRONMENT == "development":
    origins = [
        settings.FRONTEND_URL,
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]
else:
    origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & /api health endpoints
app.include_router(health_router, tags=["health"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(schema_router, prefix="/api", tags=["schema"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(history_router, prefix="/api/history", tags=["history"])
app.include_router(suggestions_router, prefix="/api/suggestions", tags=["suggestions"])
app.include_router(sources_router, prefix="/api/sources", tags=["sources"])


class DocumentSearchRequest(BaseModel):
    query: str
    source_id: str
    top_k: int = 4


@app.post("/api/documents/search", tags=["documents"])
async def search_documents_endpoint(req: DocumentSearchRequest):
    processor = DocumentProcessor()
    results = processor.search(req.query, req.source_id, top_k=req.top_k)
    return {"query": req.query, "source_id": req.source_id, "results": results, "count": len(results)}


@app.post("/api/demo/generate", tags=["demo"])
async def generate_demo_alias():
    return await generate_demo_source()


@app.get("/api/workspaces", tags=["workspaces"])
async def list_workspaces():
    db = MongoDBManager.get_db()
    workspaces = list(db[MongoDBManager.SYS_WORKSPACES].find({}, {"_id": 0}))
    return {"workspaces": workspaces}
