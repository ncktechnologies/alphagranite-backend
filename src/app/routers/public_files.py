import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from src.app.utils.helpers import error_response

router = APIRouter()

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "static" / "uploads"

@router.get("/test-public")
async def test_public_route():
    """Test endpoint to verify public access without authentication"""
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Public route is working! No authentication required.",
            "data": {
                "authenticated": False,
                "upload_dir": str(UPLOAD_DIR),
                "upload_dir_exists": UPLOAD_DIR.exists()
            }
        }
    )

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
