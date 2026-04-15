import os
import mimetypes
from pathlib import Path
from typing import Any
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from src.app.database import get_db
from src.app.database.file import File
from src.app.utils.helpers import error_response

router = APIRouter()

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "static" / "uploads"


def _resolve_media_type(file_name: str, file_path: str, db_file_type: str | None) -> str:
    """Prefer explicit DB/PDF hints to avoid browsers treating PDFs as downloads."""
    candidate = (db_file_type or "").strip().lower()
    if candidate == "application/pdf":
        return "application/pdf"
    if candidate.startswith("image/"):
        return candidate

    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext == "pdf":
        return "application/pdf"

    guessed, _ = mimetypes.guess_type(file_path)
    if guessed == "application/pdf":
        return "application/pdf"
    if guessed:
        return guessed
    return "application/octet-stream"

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


@router.get("/files/{file_id}/view")
async def public_view_file(file_id: int, db: AsyncSession = Depends(get_db)):
    """Public endpoint to stream files inline by file ID."""
    file_expr: Any = File
    file_result = await db.execute(select(File).where(file_expr.id == file_id))
    db_file = file_result.scalar_one_or_none()

    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    absolute_path = Path("/app/static") / db_file.file_path
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    media_type = _resolve_media_type(
        file_name=db_file.name or "",
        file_path=str(absolute_path),
        db_file_type=db_file.file_type,
    )

    disposition = "inline" if media_type == "application/pdf" or media_type.startswith("image/") else "attachment"
    filename = db_file.name or absolute_path.name

    return FileResponse(
        path=str(absolute_path),
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'}
    )
