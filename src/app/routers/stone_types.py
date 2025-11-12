from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.interface.business_schemas import (
    StoneTypeCreate, StoneTypeUpdate, StoneTypeResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/stone-types", response_model=StoneTypeResponse, status_code=201)
async def create_stone_type(
    stone_type_data: StoneTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new stone type"""
    
    # Check if stone type name already exists
    type_check = await db.execute(select(StoneType).where(StoneType.name == stone_type_data.name))
    if type_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Stone type already exists")
    
    # Create stone type
    stone_type = StoneType(
        name=stone_type_data.name,
        description=stone_type_data.description,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(stone_type)
    await db.commit()
    await db.refresh(stone_type)
    
    return stone_type


@router.get("/stone-types", response_model=List[StoneTypeResponse])
async def get_stone_types(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of stone types with optional filtering"""
    
    query = select(StoneType)
    
    # Apply filters
    if status_id:
        query = query.where(StoneType.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(StoneType.name.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneType.name.asc())
    
    result = await db.execute(query)
    stone_types = result.scalars().all()
    
    return stone_types


@router.get("/stone-types/{type_id}", response_model=StoneTypeResponse)
async def get_stone_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone type by ID"""
    
    result = await db.execute(select(StoneType).where(StoneType.id == type_id))
    stone_type = result.scalar_one_or_none()
    
    if not stone_type:
        raise HTTPException(status_code=404, detail="Stone type not found")
    
    return stone_type


@router.put("/stone-types/{type_id}", response_model=StoneTypeResponse)
async def update_stone_type(
    type_id: int,
    stone_type_data: StoneTypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a stone type"""
    
    # Get existing stone type
    result = await db.execute(select(StoneType).where(StoneType.id == type_id))
    stone_type = result.scalar_one_or_none()
    
    if not stone_type:
        raise HTTPException(status_code=404, detail="Stone type not found")
    
    # Check name uniqueness if being updated
    if stone_type_data.name and stone_type_data.name != stone_type.name:
        type_check = await db.execute(select(StoneType).where(StoneType.name == stone_type_data.name))
        if type_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Stone type already exists")
    
    # Update fields
    update_data = stone_type_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stone_type, field, value)
    
    stone_type.updated_at = datetime.now()
    stone_type.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_type)
    
    return stone_type


@router.delete("/stone-types/{type_id}", status_code=204)
async def delete_stone_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a stone type (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(StoneType).where(StoneType.id == type_id))
    stone_type = result.scalar_one_or_none()
    
    if not stone_type:
        raise HTTPException(status_code=404, detail="Stone type not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    stone_type.status_id = 3  # Deleted status
    stone_type.updated_at = datetime.now()
    stone_type.updated_by = current_user.id
    
    await db.commit()
    
    return None
