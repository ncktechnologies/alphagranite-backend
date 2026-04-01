from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.interface.business_schemas import (
    StoneColorCreate, StoneColorUpdate, StoneColorResponse,
)
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/stone-colors", response_model=SuccessResponse[StoneColorResponse], status_code=201)
async def create_stone_color(
    color_data: StoneColorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("stone_color", "create"))
):
    """Create a new stone color"""

    stone_type = await db.get(StoneType, color_data.stone_type_id)
    if not stone_type:
        raise error_response("Stone type not found", 404)
    
    # Check if color name already exists for the stone type
    color_check = await db.execute(
        select(StoneColor).where(
            StoneColor.name == color_data.name,
            StoneColor.stone_type_id == color_data.stone_type_id,
        )
    )
    if color_check.scalar_one_or_none():
        raise error_response("Stone color already exists for this stone type", 400)
    
    # Create stone color
    stone_color = StoneColor(
        stone_type_id=color_data.stone_type_id,
        name=color_data.name,
        color_code=color_data.color_code,
        description=color_data.description,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(stone_color)
    await db.commit()
    await db.refresh(stone_color)

    return success_response(stone_color, "Stone color created successfully")


@router.get("/stone-colors", response_model=SuccessResponse[List[StoneColorResponse]])
async def get_stone_colors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    stone_type_id: Optional[int] = Query(None, description="Filter by stone type ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of stone colors with optional filtering"""
    
    query = select(StoneColor)
    
    # Apply filters
    if stone_type_id is not None:
        query = query.where(StoneColor.stone_type_id == stone_type_id)

    # Use explicit None check so a provided 0 (invalid) won't be treated as "no filter".
    if status_id is not None:
        query = query.where(StoneColor.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(StoneColor.name.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneColor.name.asc())
    
    result = await db.execute(query)
    colors = result.scalars().all()

    return success_response(colors, "Stone colors fetched successfully")


@router.get("/stone-colors/{color_id}", response_model=SuccessResponse[StoneColorResponse])
async def get_stone_color(
    color_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone color by ID"""
    
    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()
    
    if not stone_color:
        raise error_response("Stone color not found", 404)

    return success_response(stone_color, "Stone color fetched successfully")


@router.put("/stone-colors/{color_id}", response_model=SuccessResponse[StoneColorResponse])
async def update_stone_color(
    color_id: int,
    color_data: StoneColorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("stone_color", "update"))
):
    """Update a stone color"""
    
    # Get existing stone color
    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()
    
    if not stone_color:
        raise error_response("Stone color not found", 404)
    
    # Update fields
    update_data = color_data.model_dump(exclude_unset=True)

    if "stone_type_id" in update_data:
        stone_type = await db.get(StoneType, update_data["stone_type_id"])
        if not stone_type:
            raise error_response("Stone type not found", 404)

    # Validate provided status_id to avoid DB foreign key violations
    if "status_id" in update_data:
        status_val = update_data.get("status_id")
        if status_val is None or status_val == 0:
            raise error_response("Missing or invalid 'status_id'", 400)

        # Lazily import Status to avoid circular imports
        from src.app.database.status import Status

        status_result = await db.execute(select(Status).where(Status.id == status_val))
        if not status_result.scalar_one_or_none():
            raise error_response("Provided 'status_id' does not exist", 400)

    effective_name = update_data.get("name", stone_color.name)
    effective_stone_type_id = update_data.get("stone_type_id", stone_color.stone_type_id)

    duplicate_query = select(StoneColor).where(
        StoneColor.id != color_id,
        StoneColor.name == effective_name,
    )
    if effective_stone_type_id is None:
        duplicate_query = duplicate_query.where(StoneColor.stone_type_id.is_(None))
    else:
        duplicate_query = duplicate_query.where(StoneColor.stone_type_id == effective_stone_type_id)

    duplicate_result = await db.execute(duplicate_query)
    if duplicate_result.scalar_one_or_none():
        raise error_response("Stone color already exists for this stone type", 400)

    for field, value in update_data.items():
        setattr(stone_color, field, value)
    
    stone_color.updated_at = datetime.now()
    stone_color.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_color)

    return success_response(stone_color, "Stone color updated successfully")


@router.delete("/stone-colors/{color_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_stone_color(
    color_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("stone_color", "delete"))
):
    """Delete a stone color (soft delete by setting status to deleted)"""

    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()

    if not stone_color:
        raise error_response("Stone color not found", 404)

    # Perform a hard delete (remove the record)
    await db.delete(stone_color)
    await db.commit()

    return success_response(None, "Stone color deleted successfully")


#Get stone color by stone type
@router.get("/stone-types/{stone_type_id}/stone-colors", response_model=SuccessResponse[List[StoneColorResponse]])
async def get_stone_colors_by_type(
    stone_type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all stone colors for a specific stone type"""

    result = await db.execute(select(StoneColor).where(StoneColor.stone_type_id == stone_type_id))
    colors = result.scalars().all()

    return success_response(colors, "Stone colors fetched successfully")