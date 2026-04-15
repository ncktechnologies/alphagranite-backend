from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
import mimetypes

from src.app.database.user import User
from src.app.database.file import File as FileModel
from src.app.service.file import FileService
from src.app.utils.config import get_db, get_settings
from src.app.utils.helpers import success_response, call_service
from src.app.middleware.jwt_auth import JWTBearer, get_current_user
import pwd, grp, os

router = APIRouter(
    prefix="/files",
    tags=["Files"],
    # JWT authentication is already applied at the middleware level,
    # so we don't need the dependency here
)


def _resolve_media_type(file_name: str, file_path: str, db_file_type: Optional[str]) -> str:
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

@router.post(
    "/upload",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file", "file_design", "stage_name"],
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "file_type": {"type": "string"},
                            "file_design": {"type": "string"},
                            "stage_name": {"type": "string"},
                            "job_id": {"type": "integer"},
                            "directory": {"type": "string"},
                        },
                    }
                }
            },
            "required": True,
        }
    },
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form(None),
    file_design: str = Form(...),
    stage_name: str = Form(...),
    job_id: int = Form(None),    # add this
    directory: str = Form("uploads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings = Depends(get_settings)
):
    """Upload a file and get its metadata including a URL to access it"""
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks for checking
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes"
            )
    
    await file.seek(0)
    
    # Check file extension
    if file.filename:
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else None
        if ext and ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension not allowed. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
    
    # Upload the file
    file_data = await call_service(
        FileService.upload_file,
        db=db,
        file=file,
        user_id=current_user.id,
        directory=directory,
        file_type=file_type,
        file_design=file_design,
        stage_name=stage_name,
        job_id=job_id,
        request=request
    )
    
    # Fix ownership and permissions using absolute path
    # file_data["file_path"] is relative like "jobs/uuid.jpg"
    # Construct absolute path
    absolute_file_path = os.path.join("/app/static", file_data["file_path"])
    
    try:
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(absolute_file_path, uid, gid)
        os.chmod(absolute_file_path, 0o777)
    except Exception as e:
        print(f"Warning: Could not fix file permissions: {e}")
    
    return success_response(
        data=file_data,
        message="File uploaded successfully"
    )

@router.get("/{file_id}")
async def get_file(
    request: Request,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get file metadata by ID
    
    Returns the file's metadata including its URL for access.
    """
    file_data = await call_service(
        FileService.get_file,
        db=db,
        file_id=file_id,
        request=request
    )

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )

    return success_response(
        data=file_data,
        message="File details retrieved successfully"
    )

@router.delete("/{file_id}")
async def delete_file(
    request: Request,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a file by ID
    
    Deletes the file from both the file system and the database.
    """
    result = await call_service(
        FileService.delete_file,
        db=db,
        file_id=file_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    return success_response(
        data=None,
        message="File deleted successfully"
    )

@router.get("")
async def get_all_files(
    request: Request,
    job_id: Optional[int] = None,
    stage: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    file_type: Optional[str] = Query(None, description="Filter by file MIME type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get files with optional filters and pagination."""
    response_data = await call_service(
        FileService.get_all_files,
        db=db,
        job_id=job_id,
        stage=stage,
        uploaded_by=uploaded_by,
        file_type=file_type,
        skip=skip,
        limit=limit,
        request=request,
    )
    count = len(response_data.get("data", []))
    return success_response(data=response_data, message=f"Retrieved {count} file(s)")


@router.get("/{file_id}/view")
async def view_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Stream a file for in-browser rendering where supported (e.g., PDF)."""
    file_expr: Any = FileModel
    file_result = await db.execute(select(FileModel).where(file_expr.id == file_id))
    db_file = file_result.scalar_one_or_none()

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )

    absolute_path = os.path.join("/app/static", db_file.file_path)
    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    media_type = _resolve_media_type(
        file_name=db_file.name or "",
        file_path=absolute_path,
        db_file_type=db_file.file_type,
    )

    # Render PDFs/images in-browser instead of forcing download.
    disposition = "inline" if media_type == "application/pdf" or media_type.startswith("image/") else "attachment"
    filename = db_file.name or os.path.basename(absolute_path)

    return FileResponse(
        path=absolute_path,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'}
    )