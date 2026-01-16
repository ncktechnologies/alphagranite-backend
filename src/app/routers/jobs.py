from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FileUpload, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from src.app.database import get_db
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.database.user import User
from src.app.database.file import File
from src.app.database.fab import Fab
from src.app.interface.response_wrappers import SuccessResponse, error_response, success_response
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import utc_now
from src.app.interface.business_schemas import (
    JobCreate, JobUpdate, JobResponse,
)
from src.app.service import job_crud
from src.app.utils.permissions import PermissionChecker

router = APIRouter()

BASE_URL = os.getenv("BASE_URL", "https://api.ag.easybusiness.ng")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/root/alphagranite/alpha-granit/static/uploads/jobs")


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "create"))
):
    """Create a new job with job name, job number, and account_id"""
    job = await job_crud.create_job(db, job_data, current_user.id)
    return job


@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    need_to_invoice: Optional[bool] = Query(None, description="Filter by invoice flag (true/false)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "read"))
):
    """Get list of jobs with optional filtering"""
    jobs = await job_crud.get_jobs(db, skip, limit, account_id, status_id, priority, need_to_invoice)
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job by ID"""
    job = await job_crud.get_job_by_id(db, job_id)
    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job"""
    job = await job_crud.update_job(db, job_id, job_data, current_user.id)
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job (soft delete by setting status to deleted)"""
    await job_crud.delete_job(db, job_id, current_user.id)
    return None


@router.post("/jobs/{job_id}/upload-media")
async def upload_job_media(
    job_id: int,
    files: List[UploadFile] = FileUpload(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload media files (photos, videos, etc) for a job.
    Supports multiple file uploads at once.
    """
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        return error_response("Job not found", 404)
    
    uploaded_files = []
    errors = []
    
    # Allowed file types
    ALLOWED_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'webp',  # Images
        'mp4', 'avi', 'mov', 'mkv', 'webm',  # Videos
        'pdf', 'doc', 'docx', 'txt'           # Documents
    }
    
    # Ensure upload directory exists with proper permissions
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Set directory permissions to 755
        os.chmod(UPLOAD_DIR, 0o755)
    except Exception as e:
        return error_response(f"Failed to create upload directory: {str(e)}", 500)
    
    for file in files:
        try:
            # Validate file extension
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                errors.append(f"{file.filename}: File type not allowed")
                continue
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Generate unique filename with job_id for tracking
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"job_{job_id}_{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save file to disk
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Set file permissions to be readable by everyone (644)
            os.chmod(file_path, 0o644)
            
            # Determine file type
            if file_ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
                file_type = "photo"
            elif file_ext in {'mp4', 'avi', 'mov', 'mkv', 'webm'}:
                file_type = "video"
            else:
                file_type = "document"
            
            # Store file metadata in database - just store filename
            db_file = File(
                name=file.filename,
                file_path=unique_filename,
                file_type=file_type,
                file_size=str(file_size),
                job_id=job_id,
                uploaded_by=current_user.id,
                created_at=datetime.now()
            )
            
            db.add(db_file)
            await db.flush()
            
            # Generate direct static URL
            file_url = f"{BASE_URL}/static/jobs/{unique_filename}"
            
            uploaded_files.append({
                "id": db_file.id,
                "name": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "file_url": file_url,
                "uploaded_by": current_user.id,
                "created_at": db_file.created_at.isoformat()
            })
        
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    await db.commit()
    
    response = {
        "uploaded": uploaded_files,
        "errors": errors if errors else None
    }
    
    if uploaded_files:
        return success_response(
            response,
            f"Successfully uploaded {len(uploaded_files)} file(s)" + 
            (f" with {len(errors)} error(s)" if errors else "")
        )
    else:
        return error_response(
            {"errors": errors},
            400
        )


@router.get("/jobs/{job_id}/media")
async def get_job_media(
    job_id: int,
    media_type: Optional[str] = Query(None, description="Filter by type: photo, video, or document"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all media files uploaded for a job."""
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        return error_response("Job not found", 404)
    
    # Build query
    query = select(
        File,
        User.first_name.label("uploader_first_name"),
        User.last_name.label("uploader_last_name")
    ).where(File.job_id == job_id)
    
    if media_type:
        query = query.where(File.file_type == media_type)
    
    # Join with User for uploader info
    query = query.join(User, File.uploaded_by == User.id, isouter=True)
    
    # Get total count
    count_query = select(func.count()).select_from(File).where(File.job_id == job_id)
    if media_type:
        count_query = count_query.where(File.file_type == media_type)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(File.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    media_files = []
    for row in rows:
        file = row[0]
        uploader_first = row[1]
        uploader_last = row[2]
        
        # Generate direct static URL
        file_url = f"{BASE_URL}/static/jobs/{file.file_path}"
        
        media_files.append({
            "id": file.id,
            "name": file.name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "file_url": file_url,
            "uploaded_by": file.uploaded_by,
            "uploader_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
            "created_at": file.created_at.isoformat() if file.created_at else None
        })
    
    page = (skip // limit) + 1 if limit > 0 else 1
    
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "media_type_filter": media_type,
        "data": media_files
    }
    
    return success_response(response_data, f"Retrieved {len(media_files)} media file(s) for job {job_id}")


@router.get("/jobs/{job_id}/media/{file_id}/download")
async def download_job_media(
    job_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a media file for a job"""
    from fastapi.responses import FileResponse
    
    # Verify file belongs to this job
    file_result = await db.execute(
        select(File).where(File.id == file_id, File.job_id == job_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        return error_response("File not found", 404)
    
    # Verify file exists on disk
    if not os.path.exists(file.file_path):
        return error_response("File not found on server", 404)
    
    return FileResponse(
        path=file.file_path,
        filename=file.name,
        media_type="application/octet-stream"
    )


@router.delete("/jobs/{job_id}/media/{file_id}")
async def delete_job_media(
    job_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a media file from a job"""
    # Verify file belongs to this job
    file_result = await db.execute(
        select(File).where(File.id == file_id, File.job_id == job_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        return error_response("File not found", 404)
    
    # Delete file from disk if it exists
    if os.path.exists(file.file_path):
        try:
            os.remove(file.file_path)
        except Exception as e:
            return error_response(f"Failed to delete file: {str(e)}", 500)
    
    # Delete from database
    await db.delete(file)
    await db.commit()
    
    return success_response(
        {"deleted_file_id": file_id},
        f"Media file {file_id} deleted successfully"
    )


@router.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job details by job ID with FAB count and media files"""
    return await get_job_details(job_id, db, current_user, search_by="id")


@router.get("/jobs/number/{job_number}")
async def get_job_by_number(
    job_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job details by job number with FAB count and media files"""
    return await get_job_details(job_number, db, current_user, search_by="number")


async def get_job_details(
    search_value,
    db: AsyncSession,
    current_user: User,
    search_by: str = "id"  # "id" or "number"
):
    """Helper function to get job details with FAB count and media"""
    from sqlalchemy.orm import aliased
    
    # Build query
    query = select(
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone"),
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name")
    ).select_from(BusinessJob)
    
    query = query.join(Account, BusinessJob.account_id == Account.id, isouter=True)
    query = query.join(User, BusinessJob.sales_person_id == User.id, isouter=True)
    
    # Apply search filter
    if search_by == "id":
        query = query.where(BusinessJob.id == search_value)
    elif search_by == "number":
        query = query.where(BusinessJob.job_number == search_value)
    else:
        return error_response("Invalid search type", 400)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        job_not_found = "Job ID not found" if search_by == "id" else f"Job number '{search_value}' not found"
        return error_response(job_not_found, 404)
    
    # Unpack row
    job = row[0]
    job_id = job.id  # Store job ID before converting to dict
    account_name = row[1]
    account_number = row[2]
    account_contact_person = row[3]
    account_email = row[4]
    account_phone = row[5]
    sales_person_first_name = row[6]
    sales_person_last_name = row[7]
    
    # Convert job to dict and serialize
    job_dict = {
        k: v.isoformat() if isinstance(v, (datetime,)) else (float(v) if isinstance(v, Decimal) else v)
        for k, v in job.__dict__.items() if not k.startswith('_')
    }
    
    # Add account details
    job_dict["account_name"] = account_name
    job_dict["account_number"] = account_number
    job_dict["account_contact_person"] = account_contact_person
    job_dict["account_email"] = account_email
    job_dict["account_phone"] = account_phone
    
    # Add sales person
    job_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
    
    # Get FAB count for this job
    fab_count_query = select(func.count()).select_from(Fab).where(Fab.job_id == job_id)
    fab_count_result = await db.execute(fab_count_query)
    fab_count = fab_count_result.scalar()
    
    job_dict["fab_count"] = fab_count
    
    # Get FAB breakdown by stage
    stage_breakdown_query = select(
        Fab.current_stage,
        func.count().label("count")
    ).where(Fab.job_id == job_id).group_by(Fab.current_stage)
    
    stage_result = await db.execute(stage_breakdown_query)
    stage_rows = stage_result.all()
    
    fab_by_stage = {row[0]: row[1] for row in stage_rows}
    job_dict["fab_by_stage"] = fab_by_stage
    
    # Get all media files for this job
    media_query = select(
        File,
        User.first_name.label("uploader_first_name"),
        User.last_name.label("uploader_last_name")
    ).where(File.job_id == job_id)
    
    media_query = media_query.join(User, File.uploaded_by == User.id, isouter=True)
    media_query = media_query.order_by(File.created_at.desc())
    
    media_result = await db.execute(media_query)
    media_rows = media_result.all()
    
    media_files = []
    media_summary = {"photos": 0, "videos": 0, "documents": 0, "total": 0}

    for row in media_rows:
        file = row[0]
        uploader_first = row[1]
        uploader_last = row[2]

        # Generate direct static URL
        file_url = f"{BASE_URL}/static/jobs/{file.file_path}"

        media_files.append({
            "id": file.id,
            "name": file.name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "file_url": file_url,
            "uploaded_by": file.uploaded_by,
            "uploader_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
            "created_at": file.created_at.isoformat() if file.created_at else None
        })

        # Robust summary update
        if file.file_type == "photo":
            media_summary["photos"] += 1
        elif file.file_type == "video":
            media_summary["videos"] += 1
        elif file.file_type == "document":
            media_summary["documents"] += 1
        else:
            # For any unexpected type, add a new key
            media_summary[file.file_type] = media_summary.get(file.file_type, 0) + 1

        media_summary["total"] += 1

    job_dict["media_files"] = media_files
    job_dict["media_summary"] = media_summary

    return success_response(job_dict, f"Job details retrieved successfully")


@router.patch("/jobs/{job_id}/toggle-invoice")
async def toggle_need_to_invoice(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle the need_to_invoice flag for a job"""
    from src.app.service.job_crud import toggle_job_invoice_flag
    
    result = await toggle_job_invoice_flag(db, job_id, current_user.id)
    
    return {
        "success": True,
        "message": "Invoice flag toggled successfully",
        "data": result
    }
