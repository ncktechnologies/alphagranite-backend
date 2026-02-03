from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.interface.business_schemas import (
    AccountCreate, AccountUpdate, AccountResponse, JobResponse,
)
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response
from sqlalchemy.exc import IntegrityError


router = APIRouter()


@router.post("/accounts", response_model=SuccessResponse[AccountResponse], status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("accounts", "create"))
):
    """Create a new account"""
    
    # Normalize empty strings to None
    normalized = account_data.model_dump()
    for key in ["account_number", "description", "contact_person", "email", "phone", "address"]:
        if isinstance(normalized.get(key), str) and normalized[key].strip() == "":
            normalized[key] = None
    
    # Check if account name already exists
    name_check = await db.execute(select(Account).where(Account.name == normalized["name"]))
    if name_check.scalar_one_or_none():
        raise error_response("Account name already exists", 400)
    
    # Check if account number already exists (if provided)
    if normalized.get("account_number"):
        number_check = await db.execute(select(Account).where(Account.account_number == normalized["account_number"]))
        if number_check.scalar_one_or_none():
            raise error_response("Account number already exists", 400)
    
    try:
        account = Account(
            name=normalized["name"],
            account_number=normalized.get("account_number"),
            description=normalized.get("description"),
            contact_person=normalized.get("contact_person"),
            email=normalized.get("email"),
            phone=normalized.get("phone"),
            address=normalized.get("address"),
            status_id=1,
            created_by=current_user.id,
            created_at=datetime.now()
        )
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
    
    except IntegrityError:
        await db.rollback()
        raise error_response("Missing required fields or invalid values", 422)
    
    # Add total_jobs count (new account has 0 jobs)
    account_dict = account.__dict__.copy()
    account_dict["total_jobs"] = 0
    
    return success_response(account_dict, "Account created successfully")


@router.get("/accounts", response_model=SuccessResponse[List[AccountResponse]])
async def get_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name or account number"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("accounts", "read"))
):
    """Get list of accounts with optional filtering"""
    
    query = select(Account)
    
    # Apply filters
    if status_id is not None:
        query = query.where(Account.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Account.name.ilike(search_term)) | 
            (Account.account_number.ilike(search_term))
        )
    
    # Apply pagination (skip only, no limit)
    query = query.offset(skip).order_by(Account.name.asc())
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    # Add total_jobs count for each account
    accounts_with_jobs = []
    for account in accounts:
        job_count_result = await db.execute(
            select(func.count(BusinessJob.id)).where(BusinessJob.account_id == account.id)
        )
        job_count = job_count_result.scalar() or 0
        
        account_dict = account.__dict__.copy()
        account_dict['total_jobs'] = job_count
        accounts_with_jobs.append(account_dict)
    
    return success_response(accounts_with_jobs, "Accounts fetched successfully")


@router.get("/accounts/{account_id}", response_model=SuccessResponse[AccountResponse])
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by ID"""
    
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise error_response("Account not found", 404)
    
    # Add total_jobs count
    job_count_result = await db.execute(
        select(func.count(BusinessJob.id)).where(BusinessJob.account_id == account_id)
    )
    job_count = job_count_result.scalar() or 0
    
    account_dict = account.__dict__.copy()
    account_dict['total_jobs'] = job_count
    
    return success_response(account_dict, "Account fetched successfully")


@router.put("/accounts/{account_id}", response_model=SuccessResponse[AccountResponse])
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an account"""
    
    # Get existing account
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise error_response("Account not found", 404)
    
    # Check name uniqueness if being updated
    if account_data.name and account_data.name != account.name:
        name_check = await db.execute(select(Account).where(Account.name == account_data.name))
        if name_check.scalar_one_or_none():
            raise error_response("Account name already exists", 400)
    
    # Check account number uniqueness if being updated
    if account_data.account_number and account_data.account_number != account.account_number:
        number_check = await db.execute(select(Account).where(Account.account_number == account_data.account_number))
        if number_check.scalar_one_or_none():
            raise error_response("Account number already exists", 400)
    
    # Update fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    account.updated_at = datetime.now()
    account.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(account)
    
    # Add total_jobs count
    job_count_result = await db.execute(
        select(func.count(BusinessJob.id)).where(BusinessJob.account_id == account_id)
    )
    job_count = job_count_result.scalar() or 0
    
    account_dict = account.__dict__.copy()
    account_dict['total_jobs'] = job_count
    
    return success_response(account_dict, "Account updated successfully")


@router.delete("/accounts/{account_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise error_response("Account not found", 404)


    # Permanently delete the account record instead of marking status.
    # Use `await db.delete(...)` with AsyncSession and commit the change.
    await db.delete(account)
    await db.commit()

    return success_response(None, "Account deleted successfully")


@router.get("/accounts/{account_id}/jobs", response_model=SuccessResponse[List[JobResponse]])
async def get_account_jobs(
    account_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by job status ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all jobs under a specific account with optional filtering"""
    
    # Check if account exists
    account_result = await db.execute(select(Account).where(Account.id == account_id))
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise error_response("Account not found", 404)
    
    # Build query for jobs
    query = select(
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone")
    ).outerjoin(Account, BusinessJob.account_id == Account.id).where(BusinessJob.account_id == account_id)
    
    # Apply filters
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
            "created_at": job.created_at,
            "created_by": job.created_by,
            "updated_at": job.updated_at,
            "updated_by": job.updated_by
        })
    
    return success_response(jobs_list, f"Jobs for account '{account.name}' fetched successfully")