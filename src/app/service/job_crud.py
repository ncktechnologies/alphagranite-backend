"""
Job CRUD service layer containing business logic for job operations.
This separates business logic from API endpoints for better testability.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.interface.business_schemas import JobCreate, JobUpdate


async def create_job(
    db: AsyncSession,
    job_data: JobCreate,
    user_id: int
) -> BusinessJob:
    """
    Create a new job.
    
    Args:
        db: Database session
        job_data: Job creation data
        user_id: ID of user creating the job
        
    Returns:
        Created Job object
        
    Raises:
        HTTPException: If account not found or job number already exists
    """
    # Check if account exists
    account_result = await db.execute(
        select(Account).where(Account.id == job_data.account_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if job number already exists
    job_check = await db.execute(
        select(BusinessJob).where(BusinessJob.job_number == job_data.job_number)
    )
    if job_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Job number already exists")
    
    # Create job
    job = BusinessJob(
        name=job_data.name,
        job_number=job_data.job_number,
        account_id=job_data.account_id,
        description=job_data.description,
        priority=job_data.priority,
        start_date=job_data.start_date,
        due_date=job_data.due_date,
        status_id=1,  # Active status
        created_by=user_id,
        created_at=datetime.now()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return job


async def get_jobs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    status_id: Optional[int] = None,
    priority: Optional[str] = None
) -> List[BusinessJob]:
    """
    Get list of jobs with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        account_id: Filter by account ID
        status_id: Filter by status ID
        priority: Filter by priority
        
    Returns:
        List of Job objects
    """
    query = select(BusinessJob)
    
    # Apply filters
    if account_id is not None:
        query = query.where(BusinessJob.account_id == account_id)
    if status_id is not None:
        query = query.where(BusinessJob.status_id == status_id)
    if priority:
        query = query.where(BusinessJob.priority == priority)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(BusinessJob.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return jobs


async def get_job_by_id(
    db: AsyncSession,
    job_id: int
) -> BusinessJob:
    """
    Get a specific job by ID.
    
    Args:
        db: Database session
        job_id: ID of the job to retrieve
        
    Returns:
        Job object
        
    Raises:
        HTTPException: If job not found
    """
    result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


async def update_job(
    db: AsyncSession,
    job_id: int,
    job_data: JobUpdate,
    user_id: int
) -> BusinessJob:
    """
    Update an existing job.
    
    Args:
        db: Database session
        job_id: ID of job to update
        job_data: Job update data
        user_id: ID of user updating the job
        
    Returns:
        Updated Job object
        
    Raises:
        HTTPException: If job not found, account not found, or job number already exists
    """
    # Get existing job
    result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check account exists if being updated
    if job_data.account_id:
        account_result = await db.execute(
            select(Account).where(Account.id == job_data.account_id)
        )
        if not account_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Account not found")
    
    # Check job number uniqueness if being updated
    if job_data.job_number and job_data.job_number != job.job_number:
        job_check = await db.execute(
            select(BusinessJob).where(BusinessJob.job_number == job_data.job_number)
        )
        if job_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Job number already exists")
    
    # Update fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    job.updated_at = datetime.now()
    job.updated_by = user_id
    
    await db.commit()
    await db.refresh(job)
    
    return job


async def delete_job(
    db: AsyncSession,
    job_id: int,
    user_id: int
) -> None:
    """
    Delete a job (soft delete by setting status to deleted).
    
    Args:
        db: Database session
        job_id: ID of job to delete
        user_id: ID of user deleting the job
        
    Raises:
        HTTPException: If job not found
    """
    result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Soft delete by setting status to deleted (status_id 3)
    job.status_id = 3  # Deleted status
    job.updated_at = datetime.now()
    job.updated_by = user_id
    
    await db.commit()


async def get_job_count(
    db: AsyncSession,
    account_id: Optional[int] = None,
    status_id: Optional[int] = None
) -> int:
    """
    Get count of jobs with optional filtering.
    
    Args:
        db: Database session
        account_id: Filter by account ID
        status_id: Filter by status ID
        
    Returns:
        Count of jobs
    """
    from sqlalchemy import func
    
    query = select(func.count(BusinessJob.id))
    
    if account_id is not None:
        query = query.where(BusinessJob.account_id == account_id)
    if status_id is not None:
        query = query.where(BusinessJob.status_id == status_id)
    
    result = await db.execute(query)
    count = result.scalar()
    
    return count or 0


async def get_jobs_by_account(
    db: AsyncSession,
    account_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[BusinessJob]:
    """
    Get all jobs for a specific account.
    
    Args:
        db: Database session
        account_id: ID of account to get jobs for
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of Job objects
    """
    query = select(BusinessJob).where(BusinessJob.account_id == account_id)
    query = query.offset(skip).limit(limit).order_by(BusinessJob.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return jobs


async def check_job_number_exists(
    db: AsyncSession,
    job_number: str,
    exclude_job_id: Optional[int] = None
) -> bool:
    """
    Check if a job number already exists.
    
    Args:
        db: Database session
        job_number: Job number to check
        exclude_job_id: Optionally exclude a specific job ID from the check
        
    Returns:
        True if job number exists, False otherwise
    """
    query = select(BusinessJob).where(BusinessJob.job_number == job_number)
    
    if exclude_job_id is not None:
        query = query.where(BusinessJob.id != exclude_job_id)
    
    result = await db.execute(query)
    existing_job = result.scalar_one_or_none()
    
    return existing_job is not None
