import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from src.app.utils.helpers import error_response

router = APIRouter()

# Define multiple possible upload directories
UPLOAD_DIRS = [
    Path("uploads/drafting"),
    Path("uploads/slabsmith"),
    Path("uploads/finalprogramming"),
    Path("uploads"),  # Generic uploads folder
]

@router.get("/files/download/{filename}")
async def download_file(filename: str):
    """Public endpoint to download files without authentication"""
    
    # Search for file in all possible directories
    for upload_dir in UPLOAD_DIRS:
        file_path = upload_dir / filename
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/octet-stream"
            )
    
    # File not found in any directory
    raise error_response("File not found on disk", 404)