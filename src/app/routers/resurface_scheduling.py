from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import ResurfaceScheduling
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    ResurfaceSchedulingCreate,
    ResurfaceSchedulingUpdate,
    ResurfaceSchedulingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/resurface-scheduling", response_model=SuccessResponse[ResurfaceSchedulingResponse], status_code=201)
async def create_resurface_scheduling(
    resurface_data: ResurfaceSchedulingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create resurface scheduling for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == resurface_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(ResurfaceScheduling).where(ResurfaceScheduling.fab_id == resurface_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("Resurface Scheduling already exists for this fab", 400)
    
    # Create resurface scheduling
    resurface_scheduling = ResurfaceScheduling(
        fab_id=resurface_data.fab_id,
        scheduled_start_date=resurface_data.scheduled_start_date,
        scheduled_end_date=resurface_data.scheduled_end_date,
        total_sqft=resurface_data.total_sqft,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "resurface_schedulings"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(resurface_scheduling)
    await db.commit()
    await db.refresh(resurface_scheduling)
    
    return success_response(
        ResurfaceSchedulingResponse(
            id=resurface_scheduling.id,
            fab_id=resurface_scheduling.fab_id,
            technician_id=resurface_scheduling.technician_id,
            scheduled_start_date=resurface_scheduling.scheduled_start_date,
            scheduled_end_date=resurface_scheduling.scheduled_end_date,
            actual_start_date=resurface_scheduling.actual_start_date,
            actual_end_date=resurface_scheduling.actual_end_date,
            total_sqft=resurface_scheduling.total_sqft,
            completed_sqft=resurface_scheduling.completed_sqft,
            is_completed=resurface_scheduling.is_completed,
            status_id=resurface_scheduling.status_id,
            created_at=resurface_scheduling.created_at,
            updated_at=resurface_scheduling.updated_at,
            updated_by=resurface_scheduling.updated_by
        ),
        "Resurface Scheduling created successfully"
    )


@router.put("/resurface-scheduling/{resurface_scheduling_id}", response_model=SuccessResponse[ResurfaceSchedulingResponse])
async def update_resurface_scheduling(
    resurface_scheduling_id: int,
    update_data: ResurfaceSchedulingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update resurface scheduling"""
    
    result = await db.execute(select(ResurfaceScheduling).where(ResurfaceScheduling.id == resurface_scheduling_id))
    resurface_scheduling = result.scalar_one_or_none()
    
    if not resurface_scheduling:
        raise error_response("Resurface Scheduling not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(resurface_scheduling, key, value)
    
    resurface_scheduling.updated_at = datetime.now()
    resurface_scheduling.updated_by = current_user.id
    
    # If is_completed is True, move FAB to cut_list stage
    if resurface_scheduling.is_completed:
        fab_result = await db.execute(select(Fab).where(Fab.id == resurface_scheduling.fab_id))
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "cut_list"
            fab.next_stage = "cut_list_review"
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(resurface_scheduling)
    
    return success_response(
        ResurfaceSchedulingResponse(
            id=resurface_scheduling.id,
            fab_id=resurface_scheduling.fab_id,
            technician_id=resurface_scheduling.technician_id,
            scheduled_start_date=resurface_scheduling.scheduled_start_date,
            scheduled_end_date=resurface_scheduling.scheduled_end_date,
            actual_start_date=resurface_scheduling.actual_start_date,
            actual_end_date=resurface_scheduling.actual_end_date,
            total_sqft=resurface_scheduling.total_sqft,
            completed_sqft=resurface_scheduling.completed_sqft,
            is_completed=resurface_scheduling.is_completed,
            status_id=resurface_scheduling.status_id,
            created_at=resurface_scheduling.created_at,
            updated_at=resurface_scheduling.updated_at,
            updated_by=resurface_scheduling.updated_by
        ),
        "Resurface Scheduling updated successfully"
    )


@router.get("/resurface-scheduling/fab/{fab_id}", response_model=SuccessResponse[ResurfaceSchedulingResponse])
async def get_resurface_scheduling_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resurface scheduling by fab ID"""
    
    result = await db.execute(select(ResurfaceScheduling).where(ResurfaceScheduling.fab_id == fab_id))
    resurface_scheduling = result.scalar_one_or_none()
    
    if not resurface_scheduling:
        raise error_response("Resurface Scheduling not found for this fab", 404)
    
    return success_response(
        ResurfaceSchedulingResponse(
            id=resurface_scheduling.id,
            fab_id=resurface_scheduling.fab_id,
            technician_id=resurface_scheduling.technician_id,
            scheduled_start_date=resurface_scheduling.scheduled_start_date,
            scheduled_end_date=resurface_scheduling.scheduled_end_date,
            actual_start_date=resurface_scheduling.actual_start_date,
            actual_end_date=resurface_scheduling.actual_end_date,
            total_sqft=resurface_scheduling.total_sqft,
            completed_sqft=resurface_scheduling.completed_sqft,
            is_completed=resurface_scheduling.is_completed,
            status_id=resurface_scheduling.status_id,
            created_at=resurface_scheduling.created_at,
            updated_at=resurface_scheduling.updated_at,
            updated_by=resurface_scheduling.updated_by
        ),
        "Resurface Scheduling retrieved successfully"
    )
