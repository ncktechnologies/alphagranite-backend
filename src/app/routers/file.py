from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException, status

from src.app.database.user import User
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

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form(None),
    directory: str = Form("uploads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings = Depends(get_settings)
):
    """
    Upload a file and get its metadata including a URL to access it
    
    The file will be stored in the server's file system and its metadata
    will be stored in the database for later retrieval.
    
    Returns the file's metadata including its ID which can be used to
    retrieve the file later.
    """
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks for checking
    
    # Read file in chunks to determine size without loading whole file in memory
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
    
    # Reset file pointer for later use
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
        request=request
    )
    
    file_path = f"{directory}/{file.filename}"
    uid = pwd.getpwnam("www-data").pw_uid
    gid = grp.getgrnam("www-data").gr_gid
    os.chown(file_path, uid, gid)
    os.chmod(file_path, 0o777)
    
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