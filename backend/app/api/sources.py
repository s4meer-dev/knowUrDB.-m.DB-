import os
import shutil
import traceback
import uuid
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.models.source import SourceMetadata, SourceType
from app.services.source_manager import SourceManager
from app.services.schema_service import SchemaService
from app.core.database import DatabaseManager
from app.services.demo_generator import DemoGenerator

router = APIRouter()
source_manager = SourceManager()
schema_service = SchemaService()

class BasicResponse(BaseModel):
    status: str
    message: str

@router.get("", response_model=List[SourceMetadata])
async def list_sources():
    return source_manager.list_sources()

@router.post("/generate-demo", response_model=SourceMetadata)
async def generate_demo_source():
    generator = DemoGenerator()
    
    try:
        file_path, filename = generator.generate_demo_database()
        size = Path(file_path).stat().st_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demo database: {e}")

    try:
        # Register and process
        metadata = source_manager.register_source(
            original_filename=filename,
            file_path=file_path,
            mime_type="application/x-sqlite3",
            size_bytes=size
        )
        
        # Cleanup temp
        if Path(file_path).exists():
            Path(file_path).unlink()
            
        return metadata
    except Exception as e:
        if Path(file_path).exists():
            Path(file_path).unlink()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": f"An unexpected error occurred during processing: {e}"})

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file temporarily: {e}")

    try:
        # Register and process
        metadata = source_manager.register_source(
            original_filename=file.filename,
            file_path=str(temp_file_path),
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=size
        )
        
        # Cleanup temp
        if temp_file_path.exists():
            temp_file_path.unlink()
            
        return metadata
    except Exception as e:
        if temp_file_path.exists():
            temp_file_path.unlink()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": f"An unexpected error occurred during processing: {e}"})

@router.post("/upload/batch", response_model=List[SourceMetadata])
async def upload_sources_batch(files: list[UploadFile] = File(..., json_schema_extra={"items": {"type": "string", "format": "binary"}})):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = []
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file '{file.filename}' temporarily: {e}")

        try:
            metadata = source_manager.register_source(
                original_filename=file.filename,
                file_path=str(temp_file_path),
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=size
            )
            results.append(metadata)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": f"Error processing '{file.filename}': {e}"})
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
                
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
    return {"status": "success", "message": "Source deleted"}

@router.get("/{source_id}/schema")
async def get_source_schema(source_id: str):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    source_type = source_manager._determine_source_type(source.detected_format)
    
    if source_type == SourceType.RELATIONAL:
        try:
            db_path = source_manager.get_internal_db_path(source_id)
            # Temporarily set active to fetch schema
            # In a truly concurrent system, SchemaService should accept connection/path directly
            DatabaseManager.set_active_database(db_path)
            schema = schema_service.get_schema()
            return schema
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get schema: {e}")
    else:
        # Document sources do not have a relational schema in the same way
        return {"tables": [{"name": "Document Pages", "columns": [{"name": "text", "type": "TEXT"}]}]}

@router.get("/{source_id}/schema/{table_name}/sample")
async def get_source_table_sample(source_id: str, table_name: str, limit: int = 50):
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    source_type = source_manager._determine_source_type(source.detected_format)
    
    if source_type == SourceType.RELATIONAL:
        try:
            db_path = source_manager.get_internal_db_path(source_id)
            DatabaseManager.set_active_database(db_path)
            columns, rows = schema_service.get_table_sample(table_name, limit)
            return {"columns": columns, "rows": rows}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get sample data: {e}")
    else:
        return {"columns": ["text"], "rows": [{"text": "Sample text from document..."}]}
