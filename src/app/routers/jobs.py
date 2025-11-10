from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.app.database import get_db
from src.app.database.job import Job
from src.app.database.account import Account
from src.app.database.user import User
from src.app.interface.business_schemas import (
    JobCreate, JobUpdate, JobResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job"""
    
    # Check if account exists
    account_result = await db.execute(select(Account).where(Account.id == job_data.account_id))
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if job number already exists
    job_check = await db.execute(select(Job).where(Job.job_number == job_data.job_number))
    if job_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Job number already exists")
    
    # Create job
    job = Job(
        name=job_data.name,
        job_number=job_data.job_number,
        account_id=job_data.account_id,
        description=job_data.description,
        priority=job_data.priority,
        start_date=job_data.start_date,
        due_date=job_data.due_date,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return job


@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of jobs with optional filtering"""
    
    query = select(Job)
    
    # Apply filters
    if account_id:
        query = query.where(Job.account_id == account_id)
    if status_id:
        query = query.where(Job.status_id == status_id)
    if priority:
        query = query.where(Job.priority == priority)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job by ID"""
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job"""
    
    # Get existing job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check account exists if being updated
    if job_data.account_id:
        account_result = await db.execute(select(Account).where(Account.id == job_data.account_id))
        if not account_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Account not found")
    
    # Check job number uniqueness if being updated
    if job_data.job_number and job_data.job_number != job.job_number:
        job_check = await db.execute(select(Job).where(Job.job_number == job_data.job_number))
        if job_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Job number already exists")
    
    # Update fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    job.updated_at = datetime.now()
    job.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(job)
    
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    job.status_id = 3  # Deleted status
    job.updated_at = datetime.now()
    job.updated_by = current_user.id
    
    await db.commit()
    
    return None