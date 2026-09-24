import shutil
import traceback
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.database import DatabaseManager
from app.core.mongodb import MongoDBManager
from app.models.source import SourceMetadata, SourceType
from app.services.demo_generator import DemoGenerator
from app.services.schema_service import MongoSchemaService
from app.services.source_manager import SourceManager

router = APIRouter()
source_manager = SourceManager()
schema_service = MongoSchemaService()


class BasicResponse(BaseModel):
    status: str
    message: str


@router.get("", response_model=list[SourceMetadata])
async def list_sources():
    return source_manager.list_sources()


@router.post("/generate-demo", response_model=SourceMetadata)
async def generate_demo_source():
    generator = DemoGenerator()
    try:
        source_id, display_name = generator.generate_demo_database()
        metadata = source_manager.get_source(source_id)
        if not metadata:
            metadata = generator.generate_And_register_demo(source_id=source_id, name=display_name)
        return metadata
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": f"Failed to generate MongoDB demo dataset: {exc}"},
        ) from exc


@router.post("/upload", response_model=SourceMetadata)
async def upload_source(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    temp_dir = Path(__file__).parent.parent.parent.parent / "database" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / safe_filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        size = temp_file_path.stat().st_size
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file temporarily: {exc}") from exc

    try:
        metadata = source_manager.register_source(
            original_filename=file.filename,
            file_path=str(temp_file_path),
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=size,
        )
        return metadata
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_FILE", "message": str(exc)},
        ) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": f"An error occurred during MongoDB ingestion: {exc}"},
        ) from exc
    finally:
        try:
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)
        except OSError:
            pass


@router.post("/upload/batch", response_model=list[SourceMetadata])
async def upload_sources_batch(
    files: list[UploadFile] = File(..., json_schema_extra={"items": {"type": "string", "format": "binary"}})
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results: list[SourceMetadata] = []
    temp_dir = Path(__file__).parent.parent.parent.parent / "database" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        if not file.filename:
            continue
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = f"{unique_id}_{file.filename}"
        temp_file_path = temp_dir / safe_filename

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            size = temp_file_path.stat().st_size
            metadata = source_manager.register_source(
                original_filename=file.filename,
                file_path=str(temp_file_path),
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=size,
            )
            results.append(metadata)
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail={"error_code": "INTERNAL_ERROR", "message": f"Error processing '{file.filename}': {exc}"},
            ) from exc
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)

    return results


@router.get("/{source_id}", response_model=SourceMetadata)
async def get_source(source_id: str):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.delete("/{source_id}", response_model=BasicResponse)
async def delete_source(source_id: str):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source_manager.delete_source(source_id)
    return {"status": "success", "message": "Source and associated MongoDB collections deleted"}


@router.get("/{source_id}/schema")
async def get_source_schema(source_id: str):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source_type = source_manager._determine_source_type(source.detected_format)
    if source_type != SourceType.DOCUMENT:
        try:
            DatabaseManager.set_active_database(source_id)
            return schema_service.get_schema(source_id)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to inspect MongoDB schema: {exc}") from exc
    else:
        chunks_cnt = MongoDBManager.get_db()[MongoDBManager.SYS_DOCUMENT_CHUNKS].count_documents(
            {"source_id": source_id}
        )
        return {
            "tables": [
                {
                    "name": "document_chunks",
                    "document_count": chunks_cnt,
                    "columns": [
                        {"name": "chunk_id", "data_type": "String", "type": "String", "primary_key": True},
                        {"name": "page_number", "data_type": "Int64", "type": "Int64", "primary_key": False},
                        {"name": "text", "data_type": "String", "type": "String", "primary_key": False},
                        {"name": "embedding", "data_type": "Array", "type": "Array", "primary_key": False},
                    ],
                    "primary_keys": ["chunk_id"],
                    "foreign_keys": [],
                    "indexes": [{"name": "chunk_id_1", "keys": ["chunk_id"], "unique": True}],
                }
            ]
        }


@router.get("/{source_id}/schema/{table_name}/sample")
async def get_source_table_sample(source_id: str, table_name: str, limit: int = 50):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source_type = source_manager._determine_source_type(source.detected_format)
    if source_type != SourceType.DOCUMENT:
        try:
            DatabaseManager.set_active_database(source_id)
            columns, rows = schema_service.get_table_sample(table_name, limit)
            return {"columns": columns, "rows": rows}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to fetch sample documents: {exc}") from exc
    else:
        chunks = list(
            MongoDBManager.get_db()[MongoDBManager.SYS_DOCUMENT_CHUNKS]
            .find({"source_id": source_id}, {"_id": 0, "page_number": 1, "text": 1})
            .limit(limit)
        )
        return {"columns": ["page_number", "text"], "rows": chunks}
