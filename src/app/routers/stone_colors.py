from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.stone_color import StoneColor
from src.app.database.user import User
from src.app.interface.business_schemas import (
    StoneColorCreate, StoneColorUpdate, StoneColorResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/stone-colors", response_model=StoneColorResponse, status_code=201)
async def create_stone_color(
    color_data: StoneColorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new stone color"""
    
    # Check if color name already exists
    color_check = await db.execute(select(StoneColor).where(StoneColor.name == color_data.name))
    if color_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Stone color already exists")
    
    # Create stone color
    stone_color = StoneColor(
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
    
    return stone_color


@router.get("/stone-colors", response_model=List[StoneColorResponse])
async def get_stone_colors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of stone colors with optional filtering"""
    
    query = select(StoneColor)
    
    # Apply filters
    if status_id:
        query = query.where(StoneColor.status_id == status_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(StoneColor.name.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(StoneColor.name.asc())
    
    result = await db.execute(query)
    colors = result.scalars().all()
    
    return colors


@router.get("/stone-colors/{color_id}", response_model=StoneColorResponse)
async def get_stone_color(
    color_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific stone color by ID"""
    
    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()
    
    if not stone_color:
        raise HTTPException(status_code=404, detail="Stone color not found")
    
    return stone_color


@router.put("/stone-colors/{color_id}", response_model=StoneColorResponse)
async def update_stone_color(
    color_id: int,
    color_data: StoneColorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a stone color"""
    
    # Get existing stone color
    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()
    
    if not stone_color:
        raise HTTPException(status_code=404, detail="Stone color not found")
    
    # Check name uniqueness if being updated
    if color_data.name and color_data.name != stone_color.name:
        color_check = await db.execute(select(StoneColor).where(StoneColor.name == color_data.name))
        if color_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Stone color already exists")
    
    # Update fields
    update_data = color_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stone_color, field, value)
    
    stone_color.updated_at = datetime.now()
    stone_color.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(stone_color)
    
    return stone_color


@router.delete("/stone-colors/{color_id}", status_code=204)
async def delete_stone_color(
    color_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a stone color (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(StoneColor).where(StoneColor.id == color_id))
    stone_color = result.scalar_one_or_none()
    
    if not stone_color:
        raise HTTPException(status_code=404, detail="Stone color not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    stone_color.status_id = 3  # Deleted status
    stone_color.updated_at = datetime.now()
    stone_color.updated_by = current_user.id
    
    await db.commit()
    
    return None