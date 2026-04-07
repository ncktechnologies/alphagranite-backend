from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.stone_thickness import StoneThickness
from src.app.interface.business_schemas import (
    StoneThicknessCreate, StoneThicknessUpdate, StoneThicknessResponse,
)
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/stone-thickness", response_model=SuccessResponse[StoneThicknessResponse], status_code=201)
async def create_stone_thickness(
    thickness_data: StoneThicknessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("stone_thickness", "create"))
):
    """Create a new stone thickness"""
    
    # Check if thickness already exists
    thickness_check = await db.execute(select(StoneThickness).where(StoneThickness.thickness == thickness_data.thickness))
    if thickness_check.scalar_one_or_none():
        raise error_response("Stone thickness already exists", 400)
    
    # Create stone thickness
    stone_thickness = StoneThickness(
        thickness=thickness_data.thickness,
        thickness_mm=thickness_data.thickness_mm,
        description=thickness_data.description,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(stone_thickness)
    await db.commit()
    await db.refresh(stone_thickness)
    
    return success_response(stone_thickness, "Stone thickness created successfully")


@router.get("/stone-thickness", response_model=SuccessResponse[List[StoneThicknessResponse]])
async def get_stone_thicknesses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of stone thicknesses with optional filtering"""
    
    query = select(StoneThickness)
    
    # Apply filters
    # Use explicit None check so a provided 0 (invalid) won't be treated as "no filter".
    if status_id is not None:
        query = query.where(StoneThickness.status_id == status_id)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneThickness.thickness_mm.asc())
    
    result = await db.execute(query)
    thicknesses = result.scalars().all()
    
    return success_response(thicknesses, "Stone thicknesses fetched successfully")


@router.get("/stone-thickness/{thickness_id}", response_model=SuccessResponse[StoneThicknessResponse])
async def get_stone_thickness(
    thickness_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone thickness by ID"""
    
    result = await db.execute(select(StoneThickness).where(StoneThickness.id == thickness_id))
    stone_thickness = result.scalar_one_or_none()
    
    if not stone_thickness:
        raise error_response("Stone thickness not found", 404)
    
    return success_response(stone_thickness, "Stone thickness fetched successfully")


@router.put("/stone-thickness/{thickness_id}", response_model=SuccessResponse[StoneThicknessResponse])
async def update_stone_thickness(
    thickness_id: int,
    thickness_data: StoneThicknessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a stone thickness"""
    
    # Get existing stone thickness
    result = await db.execute(select(StoneThickness).where(StoneThickness.id == thickness_id))
    stone_thickness = result.scalar_one_or_none()
    
    if not stone_thickness:
        raise error_response("Stone thickness not found", 404)
    
    # Check thickness uniqueness if being updated
    if thickness_data.thickness and thickness_data.thickness != stone_thickness.thickness:
        thickness_check = await db.execute(select(StoneThickness).where(StoneThickness.thickness == thickness_data.thickness))
        if thickness_check.scalar_one_or_none():
            raise error_response("Stone thickness already exists", 400)
    
    # Update fields
    update_data = thickness_data.model_dump(exclude_unset=True)

    # Validate provided status_id to avoid DB foreign key violations
    if "status_id" in update_data:
        status_val = update_data.get("status_id")
        # Treat 0 or None as invalid/missing
        if status_val is None or status_val == 0:
            raise error_response("Missing or invalid 'status_id'", 400)

        # Lazily import Status model to avoid top-level circular imports
        from src.app.database.status import Status

        status_result = await db.execute(select(Status).where(Status.id == status_val))
        if not status_result.scalar_one_or_none():
            raise error_response("Provided 'status_id' does not exist", 400)

    for field, value in update_data.items():
        setattr(stone_thickness, field, value)
    
    stone_thickness.updated_at = datetime.now()
    stone_thickness.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_thickness)
    
    return success_response(stone_thickness, "Stone thickness updated successfully")


@router.delete("/stone-thickness/{thickness_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_stone_thickness(
    thickness_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a stone thickness (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(StoneThickness).where(StoneThickness.id == thickness_id))
    stone_thickness = result.scalar_one_or_none()
    
    if not stone_thickness:
        raise error_response("Stone thickness not found", 404)
    

    await db.delete(stone_thickness)
    await db.commit()

    # Return a standardized success wrapper so clients receive the
    # confirmation message (204 would suppress the body).
    return success_response(None, "Stone thickness deleted successfully")