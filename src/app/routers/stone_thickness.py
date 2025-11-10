from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.stone_thickness import StoneThickness
from src.app.database.user import User
from src.app.interface.business_schemas import (
    StoneThicknessCreate, StoneThicknessUpdate, StoneThicknessResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/stone-thickness", response_model=StoneThicknessResponse, status_code=201)
async def create_stone_thickness(
    thickness_data: StoneThicknessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new stone thickness"""
    
    # Check if thickness already exists
    thickness_check = await db.execute(select(StoneThickness).where(StoneThickness.thickness == thickness_data.thickness))
    if thickness_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Stone thickness already exists")
    
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
    
    return stone_thickness


@router.get("/stone-thickness", response_model=List[StoneThicknessResponse])
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
    if status_id:
        query = query.where(StoneThickness.status_id == status_id)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneThickness.thickness.asc())
    
    result = await db.execute(query)
    thicknesses = result.scalars().all()
    
    return thicknesses


@router.get("/stone-thickness/{thickness_id}", response_model=StoneThicknessResponse)
async def get_stone_thickness(
    thickness_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone thickness by ID"""
    
    result = await db.execute(select(StoneThickness).where(StoneThickness.id == thickness_id))
    stone_thickness = result.scalar_one_or_none()
    
    if not stone_thickness:
        raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    return stone_thickness


@router.put("/stone-thickness/{thickness_id}", response_model=StoneThicknessResponse)
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
        raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    # Check thickness uniqueness if being updated
    if thickness_data.thickness and thickness_data.thickness != stone_thickness.thickness:
        thickness_check = await db.execute(select(StoneThickness).where(StoneThickness.thickness == thickness_data.thickness))
        if thickness_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Stone thickness already exists")
    
    # Update fields
    update_data = thickness_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stone_thickness, field, value)
    
    stone_thickness.updated_at = datetime.now()
    stone_thickness.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_thickness)
    
    return stone_thickness


@router.delete("/stone-thickness/{thickness_id}", status_code=204)
async def delete_stone_thickness(
    thickness_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a stone thickness (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(StoneThickness).where(StoneThickness.id == thickness_id))
    stone_thickness = result.scalar_one_or_none()
    
    if not stone_thickness:
        raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    stone_thickness.status_id = 3  # Deleted status
    stone_thickness.updated_at = datetime.now()
    stone_thickness.updated_by = current_user.id
    
    await db.commit()
    
    return None