from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.account import Account
from src.app.interface.business_schemas import (
    AccountCreate, AccountUpdate, AccountResponse,
)
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response


router = APIRouter()


@router.post("/accounts", response_model=SuccessResponse[AccountResponse], status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("accounts", "create"))
):
    """Create a new account"""
    
    # Check if account name already exists
    name_check = await db.execute(select(Account).where(Account.name == account_data.name))
    if name_check.scalar_one_or_none():
        raise error_response("Account name already exists", 400)
    
    # Check if account number already exists (if provided)
    if account_data.account_number:
        number_check = await db.execute(select(Account).where(Account.account_number == account_data.account_number))
        if number_check.scalar_one_or_none():
            raise error_response("Account number already exists", 400)
    
    # Create account
    account = Account(
        name=account_data.name,
        account_number=account_data.account_number,
        description=account_data.description,
        contact_person=account_data.contact_person,
        email=account_data.email,
        phone=account_data.phone,
        address=account_data.address,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    return success_response(account, "Account created successfully")


@router.get("/accounts", response_model=SuccessResponse[List[AccountResponse]])
async def get_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name or account number"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("accounts", "read"))
):
    """Get list of accounts with optional filtering"""
    
    query = select(Account)
    
    # Apply filters
    # Use explicit None check so a provided 0 (invalid) won't be treated as "no filter".
    if status_id is not None:
        query = query.where(Account.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Account.name.ilike(search_term)) | 
            (Account.account_number.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Account.name.asc())
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    return success_response(accounts, "Accounts fetched successfully")


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
    
  
    
    return success_response(account, "Account fetched successfully")


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
    
    return success_response(account, "Account updated successfully")


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