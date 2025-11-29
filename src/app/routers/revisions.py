from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import Revision
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    RevisionCreate,
    RevisionUpdate,
    RevisionResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/revisions", response_model=SuccessResponse[RevisionResponse], status_code=201)
async def create_revision(
    revision_data: RevisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a revision for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == revision_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if requesting user exists
    requester_result = await db.execute(select(User).where(User.id == revision_data.requested_by))
    if not requester_result.scalar_one_or_none():
        raise error_response("Requesting user not found", 404)
    
    # Create revision
    revision = Revision(
        fab_id=revision_data.fab_id,
        revision_type=revision_data.revision_type,
        requested_by=revision_data.requested_by,
        assigned_to=revision_data.assigned_to,
        scheduled_start_date=revision_data.scheduled_start_date,
        scheduled_end_date=revision_data.scheduled_end_date,
        revision_notes=revision_data.revision_notes,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "revisions"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(revision)
    await db.commit()
    await db.refresh(revision)
    
    return success_response(
        RevisionResponse(
            id=revision.id,
            fab_id=revision.fab_id,
            revision_type=revision.revision_type,
            requested_by=revision.requested_by,
            assigned_to=revision.assigned_to,
            scheduled_start_date=revision.scheduled_start_date,
            scheduled_end_date=revision.scheduled_end_date,
            actual_start_date=revision.actual_start_date,
            actual_end_date=revision.actual_end_date,
            revision_notes=revision.revision_notes,
            is_completed=revision.is_completed,
            status_id=revision.status_id,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
            updated_by=revision.updated_by
        ),
        "Revision created successfully"
    )


@router.put("/revisions/{revision_id}", response_model=SuccessResponse[RevisionResponse])
async def update_revision(
    revision_id: int,
    update_data: RevisionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a revision"""
    
    result = await db.execute(select(Revision).where(Revision.id == revision_id))
    revision = result.scalar_one_or_none()
    
    if not revision:
        raise error_response("Revision not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(revision, key, value)
    
    revision.updated_at = datetime.now()
    revision.updated_by = current_user.id
    
    # If revision is completed, update fab stage to sales_ct
    if update_data.is_completed:
        fab_result = await db.execute(select(Fab).where(Fab.id == revision.fab_id))
        fab = fab_result.scalar_one_or_none()
        
        if fab:
            fab.current_stage = "sales_ct"
            fab.next_stage = "cut_list"
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(revision)
    
    return success_response(
        RevisionResponse(
            id=revision.id,
            fab_id=revision.fab_id,
            revision_type=revision.revision_type,
            requested_by=revision.requested_by,
            assigned_to=revision.assigned_to,
            scheduled_start_date=revision.scheduled_start_date,
            scheduled_end_date=revision.scheduled_end_date,
            actual_start_date=revision.actual_start_date,
            actual_end_date=revision.actual_end_date,
            revision_notes=revision.revision_notes,
            is_completed=revision.is_completed,
            status_id=revision.status_id,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
            updated_by=revision.updated_by
        ),
        "Revision updated successfully"
    )


@router.get("/revisions/fab/{fab_id}", response_model=SuccessResponse[list[RevisionResponse]])
async def get_revisions_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all revisions for a fab"""
    
    result = await db.execute(select(Revision).where(Revision.fab_id == fab_id))
    revisions = result.scalars().all()
    
    if not revisions:
        return success_response([], "No revisions found for this fab")
    
    response_data = [
        RevisionResponse(
            id=revision.id,
            fab_id=revision.fab_id,
            revision_type=revision.revision_type,
            requested_by=revision.requested_by,
            assigned_to=revision.assigned_to,
            scheduled_start_date=revision.scheduled_start_date,
            scheduled_end_date=revision.scheduled_end_date,
            actual_start_date=revision.actual_start_date,
            actual_end_date=revision.actual_end_date,
            revision_notes=revision.revision_notes,
            is_completed=revision.is_completed,
            status_id=revision.status_id,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
            updated_by=revision.updated_by
        )
        for revision in revisions
    ]
    
    return success_response(response_data, "Revisions retrieved successfully")
