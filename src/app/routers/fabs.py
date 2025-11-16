from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.job import Job
from src.app.database.user import User
from src.app.database.edge import Edge
from src.app.database.stone_type import StoneType
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.interface.business_schemas import (
    FabCreate, FabUpdate, FabResponse,
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/fabs", response_model=FabResponse, status_code=201)
async def create_fab(
    fab_data: FabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new fab"""
    
    # Validate foreign key relationships
    # Check if job exists
    job_result = await db.execute(select(Job).where(Job.id == fab_data.job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if sales person exists
    sales_person_result = await db.execute(select(User).where(User.id == fab_data.sales_person_id))
    if not sales_person_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sales person not found")
    
    # Check if stone type exists
    stone_type_result = await db.execute(select(StoneType).where(StoneType.id == fab_data.stone_type_id))
    if not stone_type_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Stone type not found")
    
    # Check if stone color exists
    stone_color_result = await db.execute(select(StoneColor).where(StoneColor.id == fab_data.stone_color_id))
    if not stone_color_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Stone color not found")
    
    # Check if stone thickness exists
    thickness_result = await db.execute(select(StoneThickness).where(StoneThickness.id == fab_data.stone_thickness_id))
    if not thickness_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    # Check if edge exists
    edge_result = await db.execute(select(Edge).where(Edge.id == fab_data.edge_id))
    if not edge_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Edge not found")
    
    # Create fab
    fab = Fab(
        job_id=fab_data.job_id,
        fab_type=fab_data.fab_type,
        sales_person_id=fab_data.sales_person_id,
        stone_type_id=fab_data.stone_type_id,
        stone_color_id=fab_data.stone_color_id,
        stone_thickness_id=fab_data.stone_thickness_id,
        edge_id=fab_data.edge_id,
        input_area=fab_data.input_area,
        total_sqft=fab_data.total_sqft,
        notes=fab_data.notes,
        template_needed=fab_data.template_needed,
        drafting_needed=fab_data.drafting_needed,
        slab_smith_cust_needed=fab_data.slab_smith_cust_needed,
        slab_smith_ag_needed=fab_data.slab_smith_ag_needed,
        sct_needed=fab_data.sct_needed,
        final_programming_needed=fab_data.final_programming_needed,
        current_stage="initial",  # Starting stage
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(fab)
    await db.commit()
    await db.refresh(fab)
    
    return fab


@router.get("/fabs", response_model=List[FabResponse])
async def get_fabs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    fab_type: Optional[str] = Query(None, description="Filter by fab type"),
    sales_person_id: Optional[int] = Query(None, description="Filter by sales person ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fabs with optional filtering"""
    
    query = select(Fab)
    
    # Apply filters
    # Use explicit None checks so provided falsy values are handled explicitly
    if job_id is not None:
        query = query.where(Fab.job_id == job_id)
    if fab_type:
        query = query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        query = query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        query = query.where(Fab.status_id == status_id)
    if current_stage:
        query = query.where(Fab.current_stage == current_stage)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Fab.created_at.desc())
    
    result = await db.execute(query)
    fabs = result.scalars().all()
    
    return fabs


@router.get("/fabs/{fab_id}", response_model=FabResponse)
async def get_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific fab by ID"""
    
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(status_code=404, detail="Fab not found")
    
    return fab


@router.put("/fabs/{fab_id}", response_model=FabResponse)
async def update_fab(
    fab_id: int,
    fab_data: FabUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a fab"""
    
    # Get existing fab
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(status_code=404, detail="Fab not found")
    
    # Validate foreign key relationships if being updated
    if fab_data.sales_person_id:
        sales_person_result = await db.execute(select(User).where(User.id == fab_data.sales_person_id))
        if not sales_person_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Sales person not found")
    
    if fab_data.stone_type_id:
        stone_type_result = await db.execute(select(StoneType).where(StoneType.id == fab_data.stone_type_id))
        if not stone_type_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone type not found")
    
    if fab_data.stone_color_id:
        stone_color_result = await db.execute(select(StoneColor).where(StoneColor.id == fab_data.stone_color_id))
        if not stone_color_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone color not found")
    
    if fab_data.stone_thickness_id:
        thickness_result = await db.execute(select(StoneThickness).where(StoneThickness.id == fab_data.stone_thickness_id))
        if not thickness_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    if fab_data.edge_id:
        edge_result = await db.execute(select(Edge).where(Edge.id == fab_data.edge_id))
        if not edge_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Edge not found")
    
    # Update fields
    update_data = fab_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fab, field, value)
    
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(fab)
    
    return fab


@router.delete("/fabs/{fab_id}", status_code=204)
async def delete_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a fab (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(status_code=404, detail="Fab not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    fab.status_id = 3  # Deleted status
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    
    return None


@router.get("/jobs/{job_id}/fabs", response_model=List[FabResponse])
async def get_fabs_by_job(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all fabs for a specific job"""
    
    # Check if job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    query = select(Fab).where(Fab.job_id == job_id)
    query = query.offset(skip).limit(limit).order_by(Fab.created_at.desc())
    
    result = await db.execute(query)
    fabs = result.scalars().all()
    
    return fabs
