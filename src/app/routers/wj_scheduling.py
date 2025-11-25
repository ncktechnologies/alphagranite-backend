from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import WJScheduling
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    WJSchedulingCreate,
    WJSchedulingUpdate,
    WJSchedulingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/wj-scheduling", response_model=SuccessResponse[WJSchedulingResponse], status_code=201)
async def create_wj_scheduling(
    wj_data: WJSchedulingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create WJ scheduling for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == wj_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(WJScheduling).where(WJScheduling.fab_id == wj_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("WJ Scheduling already exists for this fab", 400)
    
    # Create WJ scheduling
    wj_scheduling = WJScheduling(
        fab_id=wj_data.fab_id,
        scheduled_start_date=wj_data.scheduled_start_date,
        scheduled_end_date=wj_data.scheduled_end_date,
        total_ln_ft=wj_data.total_ln_ft,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "wj_schedulings"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(wj_scheduling)
    await db.commit()
    await db.refresh(wj_scheduling)
    
    return success_response(
        WJSchedulingResponse(
            id=wj_scheduling.id,
            fab_id=wj_scheduling.fab_id,
            technician_id=wj_scheduling.technician_id,
            scheduled_start_date=wj_scheduling.scheduled_start_date,
            scheduled_end_date=wj_scheduling.scheduled_end_date,
            actual_start_date=wj_scheduling.actual_start_date,
            actual_end_date=wj_scheduling.actual_end_date,
            total_ln_ft=wj_scheduling.total_ln_ft,
            completed_ln_ft=wj_scheduling.completed_ln_ft,
            is_completed=wj_scheduling.is_completed,
            status_id=wj_scheduling.status_id,
            created_at=wj_scheduling.created_at,
            updated_at=wj_scheduling.updated_at,
            updated_by=wj_scheduling.updated_by
        ),
        "WJ Scheduling created successfully"
    )


@router.put("/wj-scheduling/{wj_scheduling_id}", response_model=SuccessResponse[WJSchedulingResponse])
async def update_wj_scheduling(
    wj_scheduling_id: int,
    update_data: WJSchedulingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update WJ scheduling"""
    
    result = await db.execute(select(WJScheduling).where(WJScheduling.id == wj_scheduling_id))
    wj_scheduling = result.scalar_one_or_none()
    
    if not wj_scheduling:
        raise error_response("WJ Scheduling not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(wj_scheduling, key, value)
    
    wj_scheduling.updated_at = datetime.now()
    wj_scheduling.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(wj_scheduling)
    
    return success_response(
        WJSchedulingResponse(
            id=wj_scheduling.id,
            fab_id=wj_scheduling.fab_id,
            technician_id=wj_scheduling.technician_id,
            scheduled_start_date=wj_scheduling.scheduled_start_date,
            scheduled_end_date=wj_scheduling.scheduled_end_date,
            actual_start_date=wj_scheduling.actual_start_date,
            actual_end_date=wj_scheduling.actual_end_date,
            total_ln_ft=wj_scheduling.total_ln_ft,
            completed_ln_ft=wj_scheduling.completed_ln_ft,
            is_completed=wj_scheduling.is_completed,
            status_id=wj_scheduling.status_id,
            created_at=wj_scheduling.created_at,
            updated_at=wj_scheduling.updated_at,
            updated_by=wj_scheduling.updated_by
        ),
        "WJ Scheduling updated successfully"
    )


@router.get("/wj-scheduling/fab/{fab_id}", response_model=SuccessResponse[WJSchedulingResponse])
async def get_wj_scheduling_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get WJ scheduling by fab ID"""
    
    result = await db.execute(select(WJScheduling).where(WJScheduling.fab_id == fab_id))
    wj_scheduling = result.scalar_one_or_none()
    
    if not wj_scheduling:
        raise error_response("WJ Scheduling not found for this fab", 404)
    
    return success_response(
        WJSchedulingResponse(
            id=wj_scheduling.id,
            fab_id=wj_scheduling.fab_id,
            technician_id=wj_scheduling.technician_id,
            scheduled_start_date=wj_scheduling.scheduled_start_date,
            scheduled_end_date=wj_scheduling.scheduled_end_date,
            actual_start_date=wj_scheduling.actual_start_date,
            actual_end_date=wj_scheduling.actual_end_date,
            total_ln_ft=wj_scheduling.total_ln_ft,
            completed_ln_ft=wj_scheduling.completed_ln_ft,
            is_completed=wj_scheduling.is_completed,
            status_id=wj_scheduling.status_id,
            created_at=wj_scheduling.created_at,
            updated_at=wj_scheduling.updated_at,
            updated_by=wj_scheduling.updated_by
        ),
        "WJ Scheduling retrieved successfully"
    )
