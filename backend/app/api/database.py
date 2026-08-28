import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import sqlite3

from app.core.database import DatabaseManager

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "database" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DatabaseStatusResponse(BaseModel):
    is_demo: bool
    name: str
    path: str

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

@router.post("/upload", response_model=DatabaseStatusResponse)
async def upload_database(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = {".db", ".sqlite", ".sqlite3", ".sql"}
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension {ext}. Allowed: .db, .sqlite, .sqlite3, .sql")

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

    # If it's a .sql dump, convert it to a SQLite DB
    if ext == ".sql":
        db_path = UPLOAD_DIR / f"{unique_id}_imported.db"
        try:
            conn = sqlite3.connect(db_path)
            with open(file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn.executescript(sql_script)
            conn.commit()
            conn.close()
            # Replace file_path with new DB path
            file_path = db_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to import SQL dump: {e}")

    # Validate that it's a valid SQLite DB
    try:
        conn = sqlite3.connect(f"file:{file_path.absolute().as_posix()}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        # It's ok if there are no tables if it's an empty DB, but usually we expect at least one.
        # But we won't strictly fail it if empty. Let's just catch SQLite errors.
    except Exception as e:
        # Cleanup invalid file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Invalid SQLite database: {e}")

    # Set as active
    DatabaseManager.set_active_database(str(file_path.absolute()))
    
    return DatabaseManager.get_active_database_info()
