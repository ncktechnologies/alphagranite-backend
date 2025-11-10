from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.user import User
from src.app.interface.business_schemas import (
    AccountCreate, AccountUpdate, AccountResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account"""
    
    # Check if account name already exists
    name_check = await db.execute(select(Account).where(Account.name == account_data.name))
    if name_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Account name already exists")
    
    # Check if account number already exists (if provided)
    if account_data.account_number:
        number_check = await db.execute(select(Account).where(Account.account_number == account_data.account_number))
        if number_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Account number already exists")
    
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
    
    return account


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name or account number"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of accounts with optional filtering"""
    
    query = select(Account)
    
    # Apply filters
    if status_id:
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
    
    return accounts


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by ID"""
    
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
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
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check name uniqueness if being updated
    if account_data.name and account_data.name != account.name:
        name_check = await db.execute(select(Account).where(Account.name == account_data.name))
        if name_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Account name already exists")
    
    # Check account number uniqueness if being updated
    if account_data.account_number and account_data.account_number != account.account_number:
        number_check = await db.execute(select(Account).where(Account.account_number == account_data.account_number))
        if number_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Account number already exists")
    
    # Update fields
    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    account.updated_at = datetime.now()
    account.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(account)
    
    return account


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    account.status_id = 3  # Deleted status
    account.updated_at = datetime.now()
    account.updated_by = current_user.id
    
    await db.commit()
    
    return None