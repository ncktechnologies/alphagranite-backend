from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.stone_type import StoneType
from src.app.interface.business_schemas import (
    StoneTypeCreate, StoneTypeUpdate, StoneTypeResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response, error_response

router = APIRouter()


@router.post("/stone-types", response_model=SuccessResponse[StoneTypeResponse], status_code=201)
async def create_stone_type(
    stone_type_data: StoneTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new stone type"""
    
    # Check if stone type name already exists
    type_check = await db.execute(select(StoneType).where(StoneType.name == stone_type_data.name))
    if type_check.scalar_one_or_none():
        raise error_response("Stone type already exists", 400)
    
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
    
    return success_response(stone_type, "Stone type created successfully")


@router.get("/stone-types", response_model=SuccessResponse[List[StoneTypeResponse]])
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
    # Use explicit None check so a provided 0 (invalid) won't be treated as "no filter".
    if status_id is not None:
        query = query.where(StoneType.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(StoneType.name.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneType.name.asc())
    
    result = await db.execute(query)
    stone_types = result.scalars().all()
    
    return success_response(stone_types, "Stone types fetched successfully")


@router.get("/stone-types/{type_id}", response_model=SuccessResponse[StoneTypeResponse])
async def get_stone_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone type by ID"""
    
    result = await db.execute(select(StoneType).where(StoneType.id == type_id))
    stone_type = result.scalar_one_or_none()
    
    if not stone_type:
        raise error_response("Stone type not found", 404)
    
    return success_response(stone_type, "Stone type fetched successfully")


@router.put("/stone-types/{type_id}", response_model=SuccessResponse[StoneTypeResponse])
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
        raise error_response("Stone type not found", 404)
    
    # Check name uniqueness if being updated
    if stone_type_data.name and stone_type_data.name != stone_type.name:
        type_check = await db.execute(select(StoneType).where(StoneType.name == stone_type_data.name))
        if type_check.scalar_one_or_none():
            raise error_response("Stone type already exists", 400)
    
    # Update fields
    update_data = stone_type_data.model_dump(exclude_unset=True)

    # Validate provided status_id to avoid DB foreign key violations
    if "status_id" in update_data:
        status_val = update_data.get("status_id")
        if status_val is None or status_val == 0:
            raise error_response("Missing or invalid 'status_id'", 400)

        from src.app.database.status import Status

        status_result = await db.execute(select(Status).where(Status.id == status_val))
        if not status_result.scalar_one_or_none():
            raise error_response("Provided 'status_id' does not exist", 400)

    for field, value in update_data.items():
        setattr(stone_type, field, value)
    
    stone_type.updated_at = datetime.now()
    stone_type.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_type)
    
    return success_response(stone_type, "Stone type updated successfully")


@router.delete("/stone-types/{type_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_stone_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a stone type (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(StoneType).where(StoneType.id == type_id))
    stone_type = result.scalar_one_or_none()
    
    if not stone_type:
        raise error_response("Stone type not found", 404)
    
    await db.delete(stone_type)
    await db.commit()
    
   
    
    return success_response(None, "Stone type deleted successfully")
