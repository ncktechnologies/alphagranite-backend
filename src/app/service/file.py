import os
import uuid
import shutil
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status, Request


from src.app.database.file import File
from src.app.database.user import User


class FileService:
    """Service for managing file uploads and retrievals"""
    
    @staticmethod
    def get_base_url(request: Optional[Request] = None) -> str:
        """Get the base URL from the request or fall back to settings"""
        if request:
            # Respect reverse-proxy headers so generated URLs are HTTPS in production.
            forwarded_proto = request.headers.get("x-forwarded-proto")
            scheme = (forwarded_proto.split(",")[0].strip() if forwarded_proto else request.url.scheme)
            host = request.headers.get("host", request.url.netloc)
            return f"{scheme}://{host}"
        
        # Fall back to settings
        from src.app.utils.config import get_settings
        settings = get_settings()
        return settings.API_BASE_URL
    
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        file: UploadFile,
        user_id: int,
        directory: str = "uploads",
        file_type: Optional[str] = None,
        file_design: Optional[str] = None,
        stage_name: Optional[str] = None,
        job_id: Optional[int] = None,
        fab_id: Optional[int] = None,
        task_id: Optional[int] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to the server and save its metadata in the database
        
        Args:
            db: Database session
            file: The file to upload
            user_id: The ID of the user uploading the file
            directory: The directory to save the file in (relative to UPLOADS_DIR)
            file_type: The type of file (defaults to derived from content-type)
            file_design: The design of the file (defaults to derived from content-type)
            stage_name: The stage name of the file (defaults to derived from content-type)
            job_id: The job ID to associate with the file
            fab_id: The FAB ID to associate with the file
            task_id: The task ID to associate with the file
            request: The FastAPI request object to extract base URL
            
        Returns:
            Dictionary containing file information including ID
        """
        # Get environment configuration
        from src.app.utils.config import get_settings
        settings = get_settings()
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(settings.STATIC_DIR, directory)
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate a unique filename
        original_name = file.filename or "upload.bin"
        file_extension = os.path.splitext(original_name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(directory, unique_filename)
        full_path = os.path.join(settings.STATIC_DIR, file_path)
        
        # Determine file type if not provided
        if not file_type:
            file_type = file.content_type
            
        # Calculate file size
        file_size = "0"
        try:
            # Get file size
            contents = await file.read()
            file_size = str(len(contents))
            
            # Write file to disk
            with open(full_path, "wb") as dest_file:
                dest_file.write(contents)
                
            # Reset file pointer for potential future use
            await file.seek(0)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file: {str(e)}"
            )
            
        # Create file record in database
        db_file = File(
            name=original_name,
            file_path=file_path,
            file_type=file_type or "application/octet-stream",
            file_size=file_size,
            stage=stage_name,
            stage_name=stage_name,
            file_design=file_design,
            job_id=job_id,
            fab_id=fab_id,
            task_id=task_id,
            uploaded_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(db_file)
        await db.flush()
        await db.commit()
        await db.refresh(db_file)
        
        # Get base URL from request or settings
        base_url = FileService.get_base_url(request)
        return FileService._serialize_file(db_file, base_url)
        
    @staticmethod
    async def get_file(db: AsyncSession, file_id: int, request: Optional[Request] = None) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by ID and generate URL
        
        Args:
            db: Database session
            file_id: The ID of the file to retrieve
            request: The FastAPI request object to extract base URL
            
        Returns:
            Dictionary containing file information including URL
        """
        file_expr: Any = File
        user_expr: Any = User

        query = (
            select(
                File,
                user_expr.first_name.label("uploader_first_name"),
                user_expr.last_name.label("uploader_last_name"),
            )
            .where(file_expr.id == file_id)
            .join(User, file_expr.uploaded_by == user_expr.id, isouter=True)
        )
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            return None

        file = row[0]
        uploader_first = row[1]
        uploader_last = row[2]
        
        # Get base URL from request or settings
        base_url = FileService.get_base_url(request)

        return FileService._serialize_file_with_uploader(
            file=file,
            base_url=base_url,
            uploader_first=uploader_first,
            uploader_last=uploader_last,
        )
        
    @staticmethod
    async def delete_file(db: AsyncSession, file_id: int) -> bool:
        """
        Delete a file from the server and database
        
        Args:
            db: Database session
            file_id: The ID of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Get environment configuration
        from src.app.utils.config import get_settings
        settings = get_settings()
        
        # Query file from database
        file_expr: Any = File
        query = select(File).where(file_expr.id == file_id)
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            return False
        
        # Delete file from disk
        full_path = os.path.join(settings.STATIC_DIR, file.file_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            # Continue even if file deletion fails
            pass
        
        # Delete file from database
        await db.delete(file)
        await db.commit()
        
        return True

    @staticmethod
    async def get_all_files(
        db: AsyncSession,
        job_id: Optional[int] = None,
        stage: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        file_expr: Any = File
        user_expr: Any = User

        query = (
            select(
                File,
                user_expr.first_name.label("uploader_first_name"),
                user_expr.last_name.label("uploader_last_name"),
            )
            .join(User, file_expr.uploaded_by == user_expr.id, isouter=True)
        )

        if job_id is not None:
            query = query.where(file_expr.job_id == job_id)
        if stage is not None:
            query = query.where(file_expr.stage == stage)
        if uploaded_by is not None:
            query = query.where(file_expr.uploaded_by == uploaded_by)
        if file_type is not None:
            query = query.where(file_expr.file_type == file_type)

        count_query = select(func.count()).select_from(File)
        if job_id is not None:
            count_query = count_query.where(file_expr.job_id == job_id)
        if stage is not None:
            count_query = count_query.where(file_expr.stage == stage)
        if uploaded_by is not None:
            count_query = count_query.where(file_expr.uploaded_by == uploaded_by)
        if file_type is not None:
            count_query = count_query.where(file_expr.file_type == file_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(file_expr.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        base_url = FileService.get_base_url(request)
        data = [
            FileService._serialize_file_with_uploader(
                file=row[0],
                base_url=base_url,
                uploader_first=row[1],
                uploader_last=row[2],
            )
            for row in rows
        ]

        page = (skip // limit) + 1 if limit > 0 else 1
        return {
            "total": total,
            "page": page,
            "per_page": limit,
            "filters": {
                "job_id": job_id,
                "stage": stage,
                "uploaded_by": uploaded_by,
                "file_type": file_type,
            },
            "data": data,
        }

    @staticmethod
    def _build_file_view_url(base_url: str, file_id: int) -> str:
        return f"{base_url}/api/v1/files/{file_id}/view"

    @staticmethod
    def _serialize_file_with_uploader(
        file: File,
        base_url: str,
        uploader_first: Optional[str],
        uploader_last: Optional[str],
    ) -> Dict[str, Any]:
        uploader_name = None
        if uploader_first:
            uploader_name = f"{uploader_first} {uploader_last}".strip()

        safe_file_id = int(file.id or 0)
        return {
            "id": file.id,
            "name": file.name,
            "file_path": file.file_path,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "file_design": file.file_design,
            "stage": file.stage,
            "stage_name": file.stage_name,
            "job_id": file.job_id,
            "fab_id": file.fab_id,
            "task_id": file.task_id,
            "uploaded_by": file.uploaded_by,
            "uploader_name": uploader_name,
            "file_url": FileService._build_file_view_url(base_url, safe_file_id),
            "url": FileService._build_file_view_url(base_url, safe_file_id),
            "created_at": file.created_at.isoformat() if file.created_at else None,
            "updated_at": file.updated_at.isoformat() if file.updated_at else None,
        }

    @staticmethod
    def _serialize_file(f: File, base_url: str) -> Dict[str, Any]:
        return {
            "id": f.id,
            "name": f.name,
            "file_path": f.file_path,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "file_design": f.file_design,
            "stage": f.stage,
            "stage_name": f.stage_name,
            "job_id": f.job_id,
            "task_id": f.task_id,
            "uploaded_by": f.uploaded_by,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
            "url": f"{base_url}/api/v1/files/{f.id}/view"
        }