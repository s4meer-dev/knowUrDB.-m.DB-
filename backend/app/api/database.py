import os
import shutil
import traceback
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.database import DatabaseManager
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.detectors import FileFormat

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "database" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

pipeline = IngestionPipeline(str(UPLOAD_DIR))

class DatabaseStatusResponse(BaseModel):
    is_demo: bool
    name: str
    path: str
    format: Optional[str] = None
    dialect: Optional[str] = None
    table_count: Optional[int] = None
    record_count: Optional[int] = None

class BasicResponse(BaseModel):
    status: str
    message: str

@router.get("/status", response_model=DatabaseStatusResponse)
async def get_status():
    return DatabaseManager.get_active_database_info()

@router.post("/reset", response_model=BasicResponse)
async def reset_to_demo():
    DatabaseManager.reset_to_demo()
    return {"status": "success", "message": "Reset to Demo Database."}

@router.post("/upload")
async def upload_database(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Generate safe unique filename
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        # Process the file via pipeline
        result = pipeline.process_file(str(file_path), file.filename)
        
        # Set as active
        DatabaseManager.set_active_database(result["path"])
        
        info = DatabaseManager.get_active_database_info()
        info.update({
            "format": result["format"],
            "dialect": result["dialect"],
            "table_count": result["table_count"],
            "record_count": result["record_count"]
        })
        
        # Cleanup original file if it's not the DB we are using directly
        if str(file_path) != result["path"] and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
                
        return info

    except ValueError as e:
        # Expected errors like unsupported format or bad conversion
        if file_path.exists():
            file_path.unlink()
        
        err_str = str(e)
        if "Unsupported format" in err_str or "not currently supported" in err_str:
            raise HTTPException(status_code=400, detail={"error_code": "UNSUPPORTED_FILE_FORMAT", "message": err_str})
        else:
            raise HTTPException(status_code=400, detail={"error_code": "INVALID_DATABASE_FILE", "message": err_str})
            
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": f"An unexpected error occurred during processing: {e}"})
