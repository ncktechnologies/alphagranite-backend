from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

from src.app.database.job import Job, JobApplication, JobStatus, JobType, ExperienceLevel
from src.app.database.user import User
from src.app.utils.config import get_db
from src.app.utils.helpers import success_response, error_response
from src.app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

# --- Request/Response Models ---
class JobStatusEnum(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"

class JobTypeEnum(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"

class ExperienceLevelEnum(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"

class JobCreate(BaseModel):
    title: str
    description: str
    requirements: str
    responsibilities: str
    location: str
    job_type: JobTypeEnum
    experience_level: ExperienceLevelEnum
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    is_remote: bool = False
    status: JobStatusEnum = JobStatusEnum.DRAFT
    application_deadline: Optional[datetime] = None
    skills_required: List[str] = []
    benefits: Optional[str] = None

class JobResponse(JobCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    company_id: int
    applications_count: int = 0

class JobApplicationCreate(BaseModel):
    cover_letter: str
    resume_url: str
    status: str = "applied"

# --- Job Listing Endpoints ---
@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatusEnum] = None,
    job_type: Optional[JobTypeEnum] = None,
    experience_level: Optional[ExperienceLevelEnum] = None,
    is_remote: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get a list of published jobs with filtering options
    """
    query = db.query(Job).filter(Job.status == JobStatus.PUBLISHED)
    
    if status:
        query = query.filter(Job.status == status)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if experience_level:
        query = query.filter(Job.experience_level == experience_level)
    if is_remote is not None:
        query = query.filter(Job.is_remote == is_remote)
    if search:
        search = f"%{search}%"
        query = query.filter(
            (Job.title.ilike(search)) | 
            (Job.description.ilike(search)) |
            (Job.requirements.ilike(search))
        )
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get job details by ID
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new job posting
    """
    db_job = Job(
        **job.dict(),
        created_by=current_user.id,
        company_id=current_user.company_id,  # Assuming user is associated with a company
        created_at=datetime.utcnow()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing job posting
    """
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user has permission to update this job
    if db_job.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this job")
    
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db_job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a job posting
    """
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if db_job.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this job")
    
    db.delete(db_job)
    db.commit()
    return {"ok": True}

# --- Job Application Endpoints ---
@router.post("/{job_id}/apply", status_code=201)
async def apply_for_job(
    job_id: int,
    application: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Apply for a job
    """
    # Check if job exists and is open for applications
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.status == JobStatus.PUBLISHED,
        (Job.application_deadline.is_(None) | (Job.application_deadline >= datetime.utcnow()))
    ).first()
    
    if not job:
        raise HTTPException(status_code=400, detail="Job is not available for applications")
    
    # Check if user has already applied
    existing_application = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.applicant_id == current_user.id
    ).first()
    
    if existing_application:
        raise HTTPException(status_code=400, detail="You have already applied to this job")
    
    # Create new application
    db_application = JobApplication(
        **application.dict(),
        job_id=job_id,
        applicant_id=current_user.id,
        applied_at=datetime.utcnow(),
        status="applied"
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    return {"message": "Application submitted successfully", "application_id": db_application.id}

@router.get("/{job_id}/applications")
async def get_job_applications(
    job_id: int,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get applications for a specific job (for job poster/recruiter)
    """
    # Verify job exists and user has permission to view applications
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view these applications")
    
    query = db.query(JobApplication).filter(JobApplication.job_id == job_id)
    
    if status:
        query = query.filter(JobApplication.status == status)
    
    applications = query.offset(skip).limit(limit).all()
    return applications

@router.put("/applications/{application_id}")
async def update_application_status(
    application_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update application status (e.g., review, interview, hired, rejected)
    """
    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verify user has permission to update this application
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job or (job.created_by != current_user.id and not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to update this application")
    
    # Update application status
    application.status = status
    application.updated_at = datetime.utcnow()
    
    if notes:
        application.notes = notes
    
    db.commit()
    db.refresh(application)
    
    return {"message": "Application status updated successfully", "application": application}
