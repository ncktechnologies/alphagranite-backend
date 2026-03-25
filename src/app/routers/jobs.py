from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FileUpload, status, Request, Form
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from fastapi.responses import FileResponse
import mimetypes
import logging
from pydantic import BaseModel, Field

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
from src.app.service.file import FileService
from src.app.utils.config import get_settings
from src.app.utils.helpers import call_service
from src.app.utils.permissions import PermissionChecker
from src.app.database.job_note import JobNote

router = APIRouter()

BASE_URL = os.getenv("BASE_URL", "https://api.ag.easybusiness.ng")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/root/alphagranite/alpha-granit/static/uploads/jobs")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

logger = logging.getLogger(__name__)

PHOTO_EXTS = {"jpg","jpeg","png","gif","webp","heic","bmp","tiff"}
VIDEO_EXTS = {"mp4","mov","avi","mkv","webm","m4v","wmv"}
DOC_EXTS   = {"pdf","doc","docx","xls","xlsx","ppt","pptx","txt","csv"}


def _is_browser_renderable_file(name: Optional[str], file_type: Optional[str] = None) -> bool:
    filename = name or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in PHOTO_EXTS or ext == "pdf":
        return True

    mime, _ = mimetypes.guess_type(filename)
    if mime and (mime.startswith("image/") or mime == "application/pdf"):
        return True

    # Fallback for stored media classification
    if file_type == "photo":
        return True
    return False


def _build_job_media_view_url(
    *,
    job_id: int,
    file_id: int,
    file_name: Optional[str],
    file_path: Optional[str],
    file_type: Optional[str] = None,
) -> str:
    return f"{BASE_URL}{API_PREFIX}/jobs/{job_id}/media/{file_id}/view"

def classify_file(upload: UploadFile) -> str:
    # Default to document
    name = upload.filename or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext in PHOTO_EXTS:
        return "photo"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in DOC_EXTS:
        return "document"
    # Fallback: use mimetype
    mime, _ = mimetypes.guess_type(name)
    if mime:
        if mime.startswith("image/"):
            return "photo"
        if mime.startswith("video/"):
            return "video"
        if mime in ("application/pdf",):
            return "document"
    return "document"


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "create"))
):
    """Create a new job with job name, job number, and account_id"""
    
    try:
        # Check if job name already exists
        name_check = await db.execute(
            select(BusinessJob).where(BusinessJob.name == job_data.name)
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Job name '{job_data.name}' already exists"
            )
        
        # Check if job number already exists (if provided)
        if job_data.job_number:
            number_check = await db.execute(
                select(BusinessJob).where(BusinessJob.job_number == job_data.job_number)
            )
            if number_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Job number '{job_data.job_number}' already exists"
                )
        
        job = await job_crud.create_job(db, job_data, current_user.id)
        return job
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/jobs", response_model=SuccessResponse[dict])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    need_to_invoice: Optional[bool] = Query(None, description="Filter by invoice flag (true/false)"),
    is_invoiced: Optional[bool] = Query(None, description="Filter by invoiced status (true=invoiced, false=not invoiced)"),
    search: Optional[str] = Query(None, description="Search by job name or job number"),
    include_notes: bool = Query(False, description="Include job notes in response"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "read"))
):
    """Get list of jobs with optional filtering and pagination metadata"""
    jobs, total = await job_crud.get_jobs(db, skip, limit, account_id, status_id, priority, need_to_invoice, search, is_invoiced)
    
    # If include_notes is True, fetch notes for each job
    if include_notes:
        job_ids = [job.get("id") for job in jobs if job.get("id") is not None]
        
        # Fetch all notes for these jobs in one query
        notes_query = select(
            JobNote,
            User.first_name.label("creator_first_name"),
            User.last_name.label("creator_last_name")
        ).where(JobNote.job_id.in_(job_ids)).join(User, JobNote.created_by == User.id, isouter=True)
        
        notes_query = notes_query.order_by(JobNote.job_id, JobNote.created_at.desc())
        
        notes_result = await db.execute(notes_query)
        notes_rows = notes_result.all()
        
        # Group notes by job_id
        notes_by_job = {}
        for row in notes_rows:
            note = row[0]
            if note.job_id not in notes_by_job:
                notes_by_job[note.job_id] = []
            
            notes_by_job[note.job_id].append({
                "id": note.id,
                "note": note.note,
                "created_by": note.created_by,
                "creator_name": f"{row[1]} {row[2]}" if row[1] else None,
                "created_at": note.created_at.isoformat() if note.created_at else None
            })
        
        # Attach notes to jobs
        for job in jobs:
            job["notes"] = notes_by_job.get(job.get("id"), [])
    
    page = (skip // limit) + 1 if limit > 0 else 1
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "data": jobs,
    }

    return success_response(response_data, "Jobs retrieved successfully")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    include_notes: bool = Query(True, description="Include job notes in response"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job by ID"""
    job = await job_crud.get_job_by_id(db, job_id)
    
    # Convert to dict if it's not already
    if not isinstance(job, dict):
        job = job.__dict__
    
    # Fetch notes for this job
    if include_notes:
        notes_query = select(
            JobNote,
            User.first_name.label("creator_first_name"),
            User.last_name.label("creator_last_name")
        ).where(JobNote.job_id == job_id).join(User, JobNote.created_by == User.id, isouter=True)
        
        notes_query = notes_query.order_by(JobNote.created_at.desc())
        
        notes_result = await db.execute(notes_query)
        notes_rows = notes_result.all()
        
        job["notes"] = []
        for row in notes_rows:
            note = row[0]
            job["notes"].append({
                "id": note.id,
                "note": note.note,
                "created_by": note.created_by,
                "creator_name": f"{row[1]} {row[2]}" if row[1] else None,
                "created_at": note.created_at.isoformat() if note.created_at else None
            })
    
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


@router.post(
    "/jobs/{job_id}/upload-media",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["files", "stage_name", "file_design"],
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                            },
                            "stage_name": {"type": "string"},
                            "file_design": {"type": "string"},
                        },
                    }
                }
            },
            "required": True,
        }
    },
)
async def upload_job_media(
    job_id: int,
    files: List[UploadFile] = FileUpload(...),
    stage_name: str = Form(...),
    file_design: str = Form(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings = Depends(get_settings),
):
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        return error_response("Job not found", 404)

    uploaded_files = []
    errors = []

    for file in files:
        try:
            file_type = classify_file(file)  # photo | video | document

            file_data = await call_service(
                FileService.upload_file,
                db=db,
                file=file,
                user_id=current_user.id,
                directory="jobs",
                file_type=file_type,
                file_design=file_design,
                stage_name=stage_name,
                request=request
            )

            await db.execute(
                File.__table__.update()
                .where(File.id == file_data["id"])
                .values(
                    job_id=job_id,
                    file_type=file_type,         # keep existing media classification
                    file_design=file_design,
                    stage=stage_name
                )
            )

            # Build browser-friendly view URL for PDFs/images, fallback to API view endpoint.
            view_url = _build_job_media_view_url(
                job_id=job_id,
                file_id=file_data["id"],
                file_name=file_data.get("name"),
                file_path=file_data.get("file_path"),
                file_type=file_type,
            )
            file_data["url"] = view_url
            file_data["view_url"] = view_url
            file_data["file_type"] = file_type
            file_data["file_design"] = file_design
            file_data["stage"] = stage_name

            serialized = {
                k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in file_data.items()
            }
            uploaded_files.append(serialized)
        except HTTPException as e:
            detail = e.detail
            if isinstance(detail, dict):
                detail_message = detail.get("message") or str(detail)
            else:
                detail_message = str(detail)
            errors.append(f"{file.filename}: {detail_message}")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    await db.commit()

    if uploaded_files:
        return success_response(
            {"uploaded": uploaded_files, "errors": errors or None},
            f"Successfully uploaded {len(uploaded_files)} file(s)" + (f" with {len(errors)} error(s)" if errors else "")
        )
    return error_response("; ".join(errors) if errors else "Upload failed", 400)


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
        
        # Generate browser-friendly view URL for PDFs/images, fallback to API view endpoint.
        file_url = _build_job_media_view_url(
            job_id=job_id,
            file_id=file.id,
            file_name=file.name,
            file_path=file.file_path,
            file_type=file.file_type,
        )
        
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


@router.get("/jobs/{job_id}/media/{file_id}/view")
async def view_job_media(
    job_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Stream a media file for viewing in browser"""
    logger.info(f"Viewing media - job_id: {job_id}, file_id: {file_id}")
    
    # Verify file belongs to this job
    file_result = await db.execute(
        select(File).where(File.id == file_id, File.job_id == job_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        logger.error(f"File not found in database - job_id: {job_id}, file_id: {file_id}")
        return error_response("File not found", 404)
    
    logger.info(f"File found in DB - file.file_path: {file.file_path}, file.name: {file.name}")
    
    # Construct absolute path
    absolute_path = os.path.join("/app/static", file.file_path)
    logger.info(f"Constructed absolute path: {absolute_path}")
    
    # Verify file exists on disk
    if not os.path.exists(absolute_path):
        logger.error(f"File not found on disk: {absolute_path}")
        # List directory contents for debugging
        dir_path = os.path.dirname(absolute_path)
        if os.path.exists(dir_path):
            files_in_dir = os.listdir(dir_path)
            logger.info(f"Files in {dir_path}: {files_in_dir}")
        else:
            logger.error(f"Directory does not exist: {dir_path}")
        return error_response("File not found on server", 404)
    
    logger.info(f"File exists on disk, serving: {absolute_path}")
    
    # Guess media type
    media_type, _ = mimetypes.guess_type(absolute_path)
    if not media_type:
        media_type = "application/octet-stream"
    
    logger.info(f"Media type: {media_type}")
    
    return FileResponse(
        path=absolute_path,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{file.name}"'}
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


@router.get("/jobs/details/{job_id}")
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

    # Explicitly include sq_ft (in case it wasn't captured above)
    job_dict["sq_ft"] = float(job.sq_ft) if job.sq_ft else None
    
    
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

        # Generate browser-friendly view URL for PDFs/images, fallback to API view endpoint.
        file_url = _build_job_media_view_url(
            job_id=job_id,
            file_id=file.id,
            file_name=file.name,
            file_path=file.file_path,
            file_type=file.file_type,
        )

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
    
    # Get notes for this job
    notes_query = select(
        JobNote,
        User.first_name.label("creator_first_name"),
        User.last_name.label("creator_last_name")
    ).where(JobNote.job_id == job_id).join(User, JobNote.created_by == User.id, isouter=True)
    
    notes_query = notes_query.order_by(JobNote.created_at.desc())
    
    notes_result = await db.execute(notes_query)
    notes_rows = notes_result.all()
    
    notes = []
    for row in notes_rows:
        note = row[0]
        notes.append({
            "id": note.id,
            "note": note.note,
            "created_by": note.created_by,
            "creator_name": f"{row[1]} {row[2]}" if row[1] else None,
            "created_at": note.created_at.isoformat() if note.created_at else None
        })
    
    job_dict["notes"] = notes

    return success_response(job_dict, f"Job details retrieved successfully")


class InvoiceToggleRequest(BaseModel):
    note: Optional[str] = Field(None, description="Optional note about invoice status change")

@router.patch("/jobs/{job_id}/toggle-invoice")
async def toggle_need_to_invoice(
    job_id: int,
    invoice_data: InvoiceToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle the need_to_invoice flag for a job with optional note"""
    from src.app.service.job_crud import toggle_job_invoice_flag
    
    result = await toggle_job_invoice_flag(db, job_id, current_user.id, invoice_data.note)
    
    return {
        "success": True,
        "message": "Invoice flag toggled successfully",
        "data": result
    }


class MarkInvoicedRequest(BaseModel):
    invoiced_at: Optional[datetime] = Field(None, description="When the job was invoiced (defaults to now)")

@router.patch("/jobs/{job_id}/mark-invoiced")
async def mark_job_invoiced(
    job_id: int,
    data: MarkInvoicedRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark job as invoiced and store the invoiced date"""
    from src.app.service.job_crud import mark_job_invoiced as svc
    result = await svc(db, job_id, current_user.id, data.invoiced_at)
    return success_response(result, "Job marked as invoiced")


class JobNoteRequest(BaseModel):
    note: str = Field(..., description="Note content", min_length=1)

@router.post("/jobs/{job_id}/notes")
async def add_job_note(
    job_id: int,
    note_data: JobNoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a note to a job"""
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        return error_response("Job not found", 404)
    
    # Create new note
    new_note = JobNote(
        job_id=job_id,
        note=note_data.note,
        created_by=current_user.id,
        created_at=utc_now()
    )
    
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    
    return success_response(
        {
            "id": new_note.id,
            "job_id": job_id,
            "note": new_note.note,
            "created_by": current_user.id,
            "creator_name": f"{current_user.first_name} {current_user.last_name}",
            "created_at": new_note.created_at.isoformat()
        },
        "Note added successfully"
    )

@router.get("/jobs/{job_id}/notes")
async def get_job_notes(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notes for a job"""
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        return error_response("Job not found", 404)
    
    # Get notes with creator info
    query = select(
        JobNote,
        User.first_name.label("creator_first_name"),
        User.last_name.label("creator_last_name")
    ).where(JobNote.job_id == job_id).join(User, JobNote.created_by == User.id)
    
    query = query.order_by(JobNote.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    notes = []
    for row in rows:
        note = row[0]
        notes.append({
            "id": note.id,
            "note": note.note,
            "created_by": note.created_by,
            "creator_name": f"{row[1]} {row[2]}",
            "created_at": note.created_at.isoformat()
        })
    
    return success_response(
        {"notes": notes, "total": len(notes)},
        f"Retrieved {len(notes)} note(s)"
    )
