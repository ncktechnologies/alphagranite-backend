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
) -> dict:
    """
    Create a new job.
    
    Args:
        db: Database session
        job_data: Job creation data (name, job_number, account_id, project_value)
        user_id: ID of user creating the job
        
    Returns:
        Job dict with account details
        
    Raises:
        HTTPException: If job number already exists or account not found
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
    
    # Create job - use model_dump and only set fields that exist in JobCreate
    job_dict = job_data.model_dump(exclude_unset=True)
    
    job = BusinessJob(
        name=job_dict.get("name"),
        job_number=job_dict.get("job_number"),
        account_id=job_dict.get("account_id"),
        description=job_dict.get("description"),
        priority=job_dict.get("priority", "Medium"),
        start_date=job_dict.get("start_date"),
        due_date=job_dict.get("due_date"),
        project_value=job_dict.get("project_value"),
        sales_person_id=job_dict.get("sales_person_id"),
        status_id=job_dict.get("status_id", 1),
        created_by=user_id,
        created_at=datetime.now()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Return job with account details
    return {
        "id": job.id,
        "name": job.name,
        "job_number": job.job_number,
        "account_id": job.account_id,
        "account_name": account.name,
        "account_number": account.account_number,
        "account_contact_person": account.contact_person,
        "account_email": account.email,
        "account_phone": account.phone,
        "description": job.description,
        "priority": job.priority,
        "start_date": job.start_date,
        "due_date": job.due_date,
        "project_value": job.project_value,
        "status_id": job.status_id,
        "sales_person_id": job.sales_person_id,
        "created_at": job.created_at,
        "created_by": job.created_by,
        "updated_at": job.updated_at,
        "updated_by": job.updated_by
    }
    


async def get_jobs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    status_id: Optional[int] = None,
    priority: Optional[str] = None
) -> List[dict]:
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
        List of Job dicts with account details
    """
    from sqlalchemy.orm import aliased
    
    query = select(
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone")
    ).outerjoin(Account, BusinessJob.account_id == Account.id)
    
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
    rows = result.all()
    
    jobs_list = []
    for row in rows:
        job = row[0]
        jobs_list.append({
            "id": job.id,
            "name": job.name,
            "job_number": job.job_number,
            "account_id": job.account_id,
            "account_name": row[1] if job.account_id else None,
            "account_number": row[2] if job.account_id else None,
            "account_contact_person": row[3] if job.account_id else None,
            "account_email": row[4] if job.account_id else None,
            "account_phone": row[5] if job.account_id else None,
            "description": job.description,
            "priority": job.priority,
            "start_date": job.start_date,
            "due_date": job.due_date,
            "project_value": job.project_value,
            "status_id": job.status_id,
            "sales_person_id": job.sales_person_id,
            "created_at": job.created_at,
            "created_by": job.created_by,
            "updated_at": job.updated_at,
            "updated_by": job.updated_by
        })
    
    return jobs_list


async def get_job_by_id(
    db: AsyncSession,
    job_id: int
) -> dict:
    """
    Get a specific job by ID with account details.
    
    Args:
        db: Database session
        job_id: ID of the job to retrieve
        
    Returns:
        Job dict with account details
        
    Raises:
        HTTPException: If job not found
    """
    query = select(
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone")
    ).outerjoin(Account, BusinessJob.account_id == Account.id).where(BusinessJob.id == job_id)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = row[0]
    return {
        "id": job.id,
        "name": job.name,
        "job_number": job.job_number,
        "account_id": job.account_id,
        "account_name": row[1] if job.account_id else None,
        "account_number": row[2] if job.account_id else None,
        "account_contact_person": row[3] if job.account_id else None,
        "account_email": row[4] if job.account_id else None,
        "account_phone": row[5] if job.account_id else None,
        "description": job.description,
        "priority": job.priority,
        "start_date": job.start_date,
        "due_date": job.due_date,
        "project_value": job.project_value,
        "status_id": job.status_id,
        "sales_person_id": job.sales_person_id,
        "created_at": job.created_at,
        "created_by": job.created_by,
        "updated_at": job.updated_at,
        "updated_by": job.updated_by
    }


async def update_job(
    db: AsyncSession,
    job_id: int,
    job_data: JobUpdate,
    user_id: int
) -> dict:
    """
    Update an existing job.
    
    Args:
        db: Database session
        job_id: ID of job to update
        job_data: Job update data (name, job_number, project_value, status_id)
        user_id: ID of user updating the job
        
    Returns:
        Updated Job dict with account details
        
    Raises:
        HTTPException: If job not found or job number already exists
    """
    # Get existing job
    result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    
    # Get account details
    account = None
    if job.account_id:
        account_result = await db.execute(
            select(Account).where(Account.id == job.account_id)
        )
        account = account_result.scalar_one_or_none()
    
    return {
        "id": job.id,
        "name": job.name,
        "job_number": job.job_number,
        "account_id": job.account_id,
        "account_name": account.name if account else None,
        "account_number": account.account_number if account else None,
        "account_contact_person": account.contact_person if account else None,
        "account_email": account.email if account else None,
        "account_phone": account.phone if account else None,
        "description": job.description,
        "priority": job.priority,
        "start_date": job.start_date,
        "due_date": job.due_date,
        "project_value": job.project_value,
        "status_id": job.status_id,
        "sales_person_id": job.sales_person_id,
        "created_at": job.created_at,
        "created_by": job.created_by,
        "updated_at": job.updated_at,
        "updated_by": job.updated_by
    }


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
