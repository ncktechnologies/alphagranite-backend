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
from src.app.database.department import Department
from src.app.interface.business_schemas import (
    TemplatingScheduleCreate,
    TemplatingScheduleUpdate,
    TemplatingCompleteRequest,
    TemplatingResponse,
    TemplatingReviewUpdate,
    TemplateReviewCompleteUpdate,
    TemplatingTechnicianUpdate,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response, utc_now
from src.app.database.fab_notes import FabNotes

router = APIRouter()


# helper to keep Fab.total_sqft in sync with Templating
async def _sync_fab_total_sqft(db: AsyncSession, fab_id: int, total_sqft, user_id: int):
    if total_sqft is None:
        return
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = fab_result.scalar_one_or_none()
    if fab:
        # Convert to float if it's a string
        if isinstance(total_sqft, str):
            total_sqft = float(total_sqft) if total_sqft else None
        fab.total_sqft = total_sqft
        fab.updated_at = utc_now()
        fab.updated_by = user_id


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
    
    # Check if templating already exists for this fab
    existing_result = await db.execute(
        select(Templating).where(Templating.fab_id == templating_data.fab_id)
    )
    existing_templating = existing_result.scalar_one_or_none()

    # If templating exists and is already scheduled, return error
    if existing_templating and existing_templating.is_templating_schedule:
        raise error_response("Templating already scheduled for this fab", 400)

    # Strip timezone info from datetime fields
    schedule_start = templating_data.schedule_start_date.replace(tzinfo=None) if templating_data.schedule_start_date else None
    schedule_due = templating_data.schedule_due_date.replace(tzinfo=None) if templating_data.schedule_due_date else None

    # If templating exists but was unscheduled, update it instead of creating new
    if existing_templating:
        # Re-schedule the existing templating
        existing_templating.is_templating_schedule = True
        existing_templating.schedule_start_date = schedule_start
        existing_templating.schedule_due_date = schedule_due
        existing_templating.total_sqft = templating_data.total_sqft
        existing_templating.notes = templating_data.notes
        existing_templating.updated_at = utc_now()
        existing_templating.updated_by = current_user.id
        templating = existing_templating
    else:
        # Create new templating schedule
        templating = Templating(
            fab_id=templating_data.fab_id,
            technician_id=templating_data.technician_id,
            schedule_start_date=schedule_start,
            schedule_due_date=schedule_due,
            total_sqft=templating_data.total_sqft,
            notes=templating_data.notes,
            is_templating_schedule=True,
            status_id=1,
            created_at=utc_now(),
            updated_at=None,
            updated_by=None
        )
        db.add(templating)
    
    # Update fab: move to templating stage and set next stage to pre_draft_review
    fab.current_stage = "templating"
    fab.next_stage = "pre_draft_review"
    fab.updated_at = utc_now()
    fab.updated_by = current_user.id
    
    # After creating/updating templating, keep Fab in sync
    await _sync_fab_total_sqft(db, templating.fab_id, templating_data.total_sqft, current_user.id)
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
        schedule_start_date=templating.schedule_start_date.date() if templating.schedule_start_date else None,
        schedule_due_date=templating.schedule_due_date.date() if templating.schedule_due_date else None,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        is_completed=templating.is_completed,
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
    templating.updated_at = utc_now()
    templating.updated_by = current_user.id
    
    # Reset fab stage - keep it at templating with next_stage as pre_draft_review
    fab_result = await db.execute(select(Fab).where(Fab.id == templating.fab_id))
    fab = fab_result.scalar_one_or_none()
    if fab and fab.current_stage == "templating":
        fab.next_stage = "pre_draft_review"
        fab.updated_at = utc_now()
        fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Templating unscheduled successfully")


@router.put("/templating/{templating_id}", response_model=SuccessResponse[TemplatingResponse])
async def update_templating(
    templating_id: int,
    update_data: TemplatingScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update templating schedule details"""
    
    result = await db.execute(select(Templating).where(Templating.id == templating_id))
    templating = result.scalar_one_or_none()
    
    if not templating:
        raise error_response("Templating not found", 404)
    
    # Update fields - explicitly handle all fields including total_sqft
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if hasattr(templating, field):  # Only set if field exists on model
            # Convert total_sqft to string if it's a float/int (database expects VARCHAR)
            if field == "total_sqft" and value is not None:
                setattr(templating, field, str(value))
            else:
                setattr(templating, field, value)
    
    templating.updated_at = utc_now()
    templating.updated_by = current_user.id

    # Sync Fab.total_sqft so GET /fabs/{id} reflects the change
    await _sync_fab_total_sqft(db, templating.fab_id, update_data.total_sqft, current_user.id)

    await db.commit()
    await db.refresh(templating)
    
    # Fetch technician and status details for enriched response
    technician = await db.get(User, templating.technician_id) if templating.technician_id else None
    status = await db.get(Status, templating.status_id)
    
    # Build enriched response - keep total_sqft as string (no conversion needed)
    response_data = TemplatingResponse(
        id=templating.id,
        fab_id=templating.fab_id,
        technician_id=templating.technician_id,
        technician_name=f"{technician.first_name} {technician.last_name}" if technician else None,
        schedule_start_date=templating.schedule_start_date.date() if templating.schedule_start_date else None,
        schedule_due_date=templating.schedule_due_date.date() if templating.schedule_due_date else None,
        total_sqft=templating.total_sqft,  # Already a string from database
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        is_completed=templating.is_completed,
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
    templating.updated_at = utc_now()  # changed
    templating.updated_by = current_user.id

    # Update FAB stage: Move to next stage based on current stage
    from src.app.routers.fabs import get_next_stage
    
    if fab.current_stage:
        fab.next_stage = get_next_stage(fab.current_stage)
        if fab.next_stage:
            fab.current_stage = fab.next_stage
            fab.next_stage = get_next_stage(fab.current_stage)
        fab.updated_at = utc_now()  # changed
        fab.updated_by = current_user.id

    # Set template_review_complete to True on successful completion
    fab.template_review_complete = True  # NEW

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
        schedule_start_date=templating.schedule_start_date.date() if templating.schedule_start_date else None,
        schedule_due_date=templating.schedule_due_date.date() if templating.schedule_due_date else None,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        is_completed=templating.is_completed,
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
    and sets template_received to True
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
    
    # Update templating status to received
    templating.status_id = 2
    templating.updated_at = utc_now()
    templating.updated_by = current_user.id
    
    # ✅ Set template_received to True
    fab.template_received = True
    
    # Move fab to predraft review stage and set next stage to drafting
    fab.current_stage = "pre_draft_review"
    fab.next_stage = "drafting"
    fab.updated_at = utc_now()
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
        schedule_start_date=templating.schedule_start_date.date() if templating.schedule_start_date else None,
        schedule_due_date=templating.schedule_due_date.date() if templating.schedule_due_date else None,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        is_completed=templating.is_completed,
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
        schedule_start_date=templating.schedule_start_date.date() if templating.schedule_start_date else None,
        schedule_due_date=templating.schedule_due_date.date() if templating.schedule_due_date else None,
        total_sqft=templating.total_sqft,
        actual_start_date=templating.actual_start_date,
        duration=templating.duration,
        notes=templating.notes,
        is_templating_schedule=templating.is_templating_schedule,
        is_completed=templating.is_completed,
        status_id=templating.status_id,
        status_name=status.name if status else None,
        created_at=templating.created_at,
        updated_at=templating.updated_at,
        updated_by=templating.updated_by
    )
    
    return success_response(response_data, "Templating fetched successfully")


# Templating Coordinator Endpoints
@router.patch("/templating/coordinator/review/{fab_id}")
async def update_template_review(
    fab_id: int,
    review_data: TemplatingReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Templating Coordinator: Update template received status and square footage
    """
    fab = await db.get(Fab, fab_id)
    if not fab:
        return error_response("FAB not found", 404)
    
    # Update FAB template received status
    fab.template_received = review_data.template_received
    if review_data.total_sqft is not None:
        fab.total_sqft = review_data.total_sqft
    fab.updated_at = utc_now()
    fab.updated_by = current_user.id
    
    # Add note if provided
    if review_data.notes:
        fab_note = FabNotes(
            fab_id=fab_id,
            stage=fab.current_stage or "templating",
            note=review_data.notes,
            created_by=current_user.id,
            created_at=utc_now()
        )
        db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    return success_response(
        {
            "fab_id": fab.id,
            "template_received": fab.template_received,
            "total_sqft": fab.total_sqft
        },
        "Template review updated successfully"
    )


@router.patch("/templating/coordinator/review-complete/{fab_id}")
async def mark_template_review_complete(
    fab_id: int,
    review_data: TemplateReviewCompleteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Templating Coordinator: Mark template review as complete
    """
    fab = await db.get(Fab, fab_id)
    if not fab:
        return error_response("FAB not found", 404)
    
    # Update template review complete status
    fab.template_review_complete = review_data.template_review_complete
    if review_data.total_sqft is not None:
        fab.total_sqft = review_data.total_sqft
    fab.updated_at = utc_now()
    fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(fab)
    
    return success_response(
        {
            "fab_id": fab.id,
            "template_review_complete": fab.template_review_complete,
            "total_sqft": fab.total_sqft
        },
        "Template review marked as complete" if review_data.template_review_complete else "Template review marked as incomplete"
    )


# Templating Technician Endpoints
@router.patch("/templating/technician/update/{fab_id}")
async def update_templating_work(
    fab_id: int,
    work_data: TemplatingTechnicianUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Templating Technician: Update templating work status, start time, duration, sqft, notes
    """
    # Get the templating record for this FAB
    result = await db.execute(
        select(Templating).where(Templating.fab_id == fab_id)
    )
    templating = result.scalar_one_or_none()
    
    if not templating:
        return error_response("Templating not found for this FAB", 404)
    
    # Verify the technician is assigned to this templating
    if templating.technician_id != current_user.id:
        return error_response("You are not assigned to this templating task", 403)
    
    # Update templating fields
    templating.is_completed = work_data.is_completed
    if work_data.actual_start_date is not None:
        templating.actual_start_date = work_data.actual_start_date
    if work_data.duration is not None:
        templating.duration = work_data.duration
    if work_data.total_sqft is not None:
        templating.total_sqft = work_data.total_sqft
    if work_data.notes is not None:
        # Append notes to existing notes
        existing_notes = templating.notes or []
        templating.notes = existing_notes + work_data.notes
    
    templating.updated_at = utc_now()
    templating.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(templating)
    
    return success_response(
        {
            "templating_id": templating.id,
            "fab_id": templating.fab_id,
            "is_completed": templating.is_completed,
            "actual_start_date": templating.actual_start_date,
            "duration": templating.duration,
            "total_sqft": templating.total_sqft
        },
        "Templating work updated successfully"
    )


@router.get("/templaters", response_model=SuccessResponse[List[dict]])
async def get_templaters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all templaters (users in TEMPLATE department)"""
    
    # Get the TEMPLATE department
    dept_result = await db.execute(
        select(Department).where(Department.name.ilike("TEMPLATE"))
    )
    department = dept_result.scalar_one_or_none()
    
    if not department:
        return success_response([], "No TEMPLATE department found")
    
    # Get all users in TEMPLATE department
    users_result = await db.execute(
        select(User)
        .where(User.department == department.id)
        .order_by(User.first_name, User.last_name)
    )
    users = users_result.scalars().all()
    
    # Format response
    templaters = [
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "department_id": user.department
        }
        for user in users
    ]
    
    return success_response(templaters, "Templaters retrieved successfully")
