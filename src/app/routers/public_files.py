import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from src.app.utils.helpers import error_response

router = APIRouter()

UPLOAD_DIR = Path("uploads/drafting")

@router.get("/files/download/{filename}")
async def download_file(filename: str):
    """Public endpoint to download files without authentication"""
    file_path = UPLOAD_DIR / filename
    
    if not os.path.exists(file_path):
        raise error_response("File not found on disk", 404)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )