import os
import uuid
import shutil
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status, Request


from src.app.database.file import File


class FileService:
    """Service for managing file uploads and retrievals"""
    
    @staticmethod
    def get_base_url(request: Request = None) -> str:
        """Get the base URL from the request or fall back to settings"""
        if request:
            # Build base URL from request
            scheme = request.url.scheme
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
        file_type: str = None,
        file_design: str = None,
        stage_name: str = None,
        request: Request = None
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
        file_extension = os.path.splitext(file.filename)[1]
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
            name=file.filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            stage=stage_name,
            file_design=file_design,
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
    async def get_file(db: AsyncSession, file_id: int, request: Request = None) -> Dict[str, Any]:
        """
        Get file metadata by ID and generate URL
        
        Args:
            db: Database session
            file_id: The ID of the file to retrieve
            request: The FastAPI request object to extract base URL
            
        Returns:
            Dictionary containing file information including URL
        """
        # Query file from database
        query = select(File).where(File.id == file_id)
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            return None
        
        # Get base URL from request or settings
        base_url = FileService.get_base_url(request)
        
        # Generate file URL
        file_url = f"{base_url}/static/{file.file_path}"
        
        return FileService._serialize_file(file, base_url)
        
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
        query = select(File).where(File.id == file_id)
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
        job_id: int = None,
        stage: str = None,
        uploaded_by: int = None,
        request: Request = None
    ) -> List[Dict[str, Any]]:
        query = select(File)
        if job_id is not None:
            query = query.where(File.job_id == job_id)
        if stage is not None:
            query = query.where(File.stage == stage)
        if uploaded_by is not None:
            query = query.where(File.uploaded_by == uploaded_by)
        query = query.order_by(File.created_at.desc())

        result = await db.execute(query)
        files = result.scalars().all()

        base_url = FileService.get_base_url(request)
        return [
            FileService._serialize_file(f, base_url)
            for f in files
        ]

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
            "uploaded_by": f.uploaded_by,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
            "url": f"{base_url}/static/{f.file_path}"
        }