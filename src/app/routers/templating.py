from datetime import datetime
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Body

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.templating import Templating
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    TemplatingScheduleCreate,
    TemplatingScheduleUpdate,
    TemplatingCompleteRequest,
    TemplatingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/templating/schedule", response_model=SuccessResponse[TemplatingResponse], status_code=201)
async def schedule_templating(
    templating_data: TemplatingScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schedule templating for a fab.
    Flow: Select Technician, Add scheduled date, Add Total sqft for draft, Add any drafting notes, Add due date
    """
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == templating_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if technician exists
    tech_result = await db.execute(select(User).where(User.id == templating_data.technician_id))
    if not tech_result.scalar_one_or_none():
        raise error_response("Technician not found", 404)
    
    # Check if templating already scheduled for this fab
    existing = await db.execute(
        select(Templating).where(Templating.fab_id == templating_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("Templating already scheduled for this fab", 400)
    
    # Create templating schedule
    templating = Templating(
        fab_id=templating_data.fab_id,
        technician_id=templating_data.technician_id,
        schedule_start_date=templating_data.schedule_start_date,
        schedule_due_date=templating_data.schedule_due_date,
        total_sqft=templating_data.total_sqft,
        notes=templating_data.notes,
        is_templating_schedule=True,
        status_id=1,  # Active status
        created_at=datetime.now(),
        updated_at=None,
        updated_by=None
    )
    
    # Update fab: move to templating stage and set next stage to pre_draft_review
    fab.current_stage = "templating"
    fab.next_stage = "pre_draft_review"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(templating)
    await db.commit()
    await db.refresh(templating)
    
    # Fetch technician and status details for enriched response
    technician = await db.get(User, templating.technician_id)
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date,
        schedule_due_date=templating.schedule_due_date,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating scheduled successfully")


@router.put("/templating/{templating_id}/unschedule", response_model=SuccessResponse[None])
async def unschedule_templating(
    templating_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unschedule/cancel templating"""
    
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Update templating to unscheduled
    templating.is_templating_schedule = False
    templating.updated_at = datetime.now()
    templating.updated_by = current_user.id
    
    # Reset fab stage back to fab_created with next_stage as templating
    fab_result = await db.execute(select(Fab).where(Fab.id == templating.fab_id))
    fab = fab_result.scalar_one_or_none()
    if fab and fab.current_stage == "templating":
        fab.current_stage = "fab_created"
        fab.next_stage = "templating"
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Templating unscheduled successfully")


@router.put("/templating/{templating_id}", response_model=SuccessResponse[TemplatingResponse])
async def update_templating(
    templating_id: int,
    templating_data: TemplatingScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update templating schedule details"""
    
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Update fields
    update_data = templating_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(templating, field, value)
    
    templating.updated_at = datetime.now()
    templating.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(templating)
    
    # Fetch technician and status details for enriched response
    technician = await db.get(User, templating.technician_id) if templating.technician_id else None
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date,
        schedule_due_date=templating.schedule_due_date,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating updated successfully")


@router.post("/templating/{templating_id}/complete", response_model=SuccessResponse[TemplatingResponse])
async def complete_templating(
    templating_id: int,
    request_data: TemplatingCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Technician marks templating as complete.
    Updates: actual square footage, notes (appends new notes to existing), status to completed.
    Also updates FAB stage to next stage in workflow.
    """
    
    # Get templating record
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Get associated FAB
    fab_result = await db.execute(select(Fab).where(Fab.id == templating.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Associated FAB not found", 404)
    
    # Update templating record
    if request_data.actual_sqft:
        templating.total_sqft = request_data.actual_sqft
    if request_data.actual_start_date:
        templating.actual_start_date = request_data.actual_start_date
    if request_data.duration is not None:
        templating.duration = request_data.duration
    if request_data.notes:
        # Append new notes to existing notes array
        existing_notes = templating.notes or []
        templating.notes = existing_notes + request_data.notes
    
    # Mark templating as completed (status_id = 2 for completed)
    templating.status_id = 2
    templating.updated_at = datetime.now()
    templating.updated_by = current_user.id
    
    # Update FAB stage: Move to next stage based on current stage
    # Import get_next_stage from fabs router
    from src.app.routers.fabs import get_next_stage
    
    if fab.current_stage:
        fab.next_stage = get_next_stage(fab.current_stage)
        # Move to next stage
        if fab.next_stage:
            fab.current_stage = fab.next_stage
            fab.next_stage = get_next_stage(fab.current_stage)
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(templating)
    await db.refresh(fab)
    
    # Fetch technician and status details for enriched response
    technician = await db.get(User, templating.technician_id) if templating.technician_id else None
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date,
        schedule_due_date=templating.schedule_due_date,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        current_stage=fab.current_stage,
        next_stage=fab.next_stage,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating marked as complete")


@router.post("/templating/{templating_id}/mark-received", response_model=SuccessResponse[None])
async def mark_templating_received(
    templating_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark templating as received, which automatically moves the fab to predraft review state
    """
    
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Get the fab
    fab_result = await db.execute(select(Fab).where(Fab.id == templating.fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if not fab:
        raise error_response("Associated fab not found", 404)
    
    # Update templating status to received (assuming status_id 2 is "received")
    templating.status_id = 2
    templating.updated_at = datetime.now()
    templating.updated_by = current_user.id
    
    # Move fab to predraft review stage and set next stage to drafting
    fab.current_stage = "pre_draft_review"
    fab.next_stage = "drafting"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Templating marked as received and moved to pre-draft review")


@router.get("/templating/{templating_id}", response_model=SuccessResponse[TemplatingResponse])
async def get_templating(
    templating_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get templating details by ID"""
    
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Fetch technician and status details
    technician = await db.get(User, templating.technician_id) if templating.technician_id else None
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date,
        schedule_due_date=templating.schedule_due_date,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating fetched successfully")


@router.get("/templating/fab/{fab_id}", response_model=SuccessResponse[TemplatingResponse])
async def get_templating_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get templating details by fab ID"""
    
    result = await db.execute(select(Templating).where(Templating.fab_id == fab_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found for this fab", 404)
    
    # Fetch technician and status details
    technician = await db.get(User, templating.technician_id) if templating.technician_id else None
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date,
        schedule_due_date=templating.schedule_due_date,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating fetched successfully")
