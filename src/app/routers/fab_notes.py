from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.fab_notes import FabNotes
from src.app.database.fab import Fab
from src.app.database.user import User
from src.app.interface.business_schemas import (
    FabNotesCreate, FabNotesUpdate, FabNotesResponse
)
from src.app.interface.response_wrappers import SuccessResponse, error_response, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.get("/fabs/{fab_id}/notes", response_model=SuccessResponse[List[FabNotesResponse]])
async def get_fab_notes_list(
    fab_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    date_from: Optional[date] = Query(None, description="Filter notes from this date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Filter notes to this date (inclusive)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notes for a specific FAB with pagination and filters"""
    
    # Check if FAB exists
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("FAB not found", 404)
    
    # Use aliased User for creator and updater
    CreatorUser = aliased(User)
    UpdaterUser = aliased(User)
    
    # Build query with joins
    query = select(
        FabNotes,
        CreatorUser.first_name.label("creator_first_name"),
        CreatorUser.last_name.label("creator_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(FabNotes.fab_id == fab_id)
    
    query = query.join(CreatorUser, FabNotes.created_by == CreatorUser.id, isouter=True)
    query = query.join(UpdaterUser, FabNotes.updated_by == UpdaterUser.id, isouter=True)
    
    # Apply filters
    if stage:
        query = query.where(FabNotes.stage == stage)
    if created_by is not None:
        query = query.where(FabNotes.created_by == created_by)
    if date_from:
        query = query.where(FabNotes.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.where(FabNotes.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    # Apply pagination and ordering
    query = query.order_by(FabNotes.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Process results
    notes = []
    for row in rows:
        fab_note = row[0]
        creator_first = row[1]
        creator_last = row[2]
        updater_first = row[3]
        updater_last = row[4]
        
        note_dict = {
            "id": fab_note.id,
            "fab_id": fab_note.fab_id,
            "stage": fab_note.stage,
            "note": fab_note.note,
            "created_by": fab_note.created_by,
            "created_by_name": f"{creator_first} {creator_last}" if creator_first else None,
            "created_at": fab_note.created_at,
            "updated_at": fab_note.updated_at,
            "updated_by": fab_note.updated_by,
            "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
        }
        notes.append(note_dict)
    
    return success_response(notes, f"Found {len(notes)} notes for FAB {fab_id}")


@router.post("/fab_notes", response_model=SuccessResponse[FabNotesResponse])
async def create_fab_note(
    note_data: FabNotesCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new FAB note"""
    
    # Validate FAB exists
    fab_result = await db.execute(select(Fab).where(Fab.id == note_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("FAB not found", 404)
    
    # Use FAB's current_stage if stage not provided
    stage = note_data.stage if note_data.stage else fab.current_stage
    
    # Create the note
    fab_note = FabNotes(
        fab_id=note_data.fab_id,
        stage=stage,
        note=note_data.note,
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(fab_note)
    await db.commit()
    await db.refresh(fab_note)
    
    # Fetch creator name
    creator = await db.get(User, current_user.id)
    
    note_response = {
        "id": fab_note.id,
        "fab_id": fab_note.fab_id,
        "stage": fab_note.stage,
        "note": fab_note.note,
        "created_by": fab_note.created_by,
        "created_by_name": f"{creator.first_name} {creator.last_name}" if creator else None,
        "created_at": fab_note.created_at,
        "updated_at": fab_note.updated_at,
        "updated_by": fab_note.updated_by,
        "updated_by_name": None
    }
    
    return success_response(note_response, "FAB note created successfully")


@router.put("/fab_notes/{note_id}", response_model=SuccessResponse[FabNotesResponse])
async def update_fab_note(
    note_id: int,
    note_data: FabNotesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing FAB note"""
    
    # Get the note
    fab_note_result = await db.execute(select(FabNotes).where(FabNotes.id == note_id))
    fab_note = fab_note_result.scalar_one_or_none()
    
    if not fab_note:
        raise error_response("FAB note not found", 404)
    
    # Update fields
    if note_data.note:
        fab_note.note = note_data.note
    if note_data.stage:
        fab_note.stage = note_data.stage
    
    fab_note.updated_at = datetime.now()
    fab_note.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(fab_note)
    
    # Fetch creator and updater names
    creator = await db.get(User, fab_note.created_by)
    updater = await db.get(User, current_user.id)
    
    note_response = {
        "id": fab_note.id,
        "fab_id": fab_note.fab_id,
        "stage": fab_note.stage,
        "note": fab_note.note,
        "created_by": fab_note.created_by,
        "created_by_name": f"{creator.first_name} {creator.last_name}" if creator else None,
        "created_at": fab_note.created_at,
        "updated_at": fab_note.updated_at,
        "updated_by": fab_note.updated_by,
        "updated_by_name": f"{updater.first_name} {updater.last_name}" if updater else None
    }
    
    return success_response(note_response, "FAB note updated successfully")


@router.delete("/fab_notes/{note_id}", status_code=204)
async def delete_fab_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a FAB note"""
    
    # Get the note
    fab_note_result = await db.execute(select(FabNotes).where(FabNotes.id == note_id))
    fab_note = fab_note_result.scalar_one_or_none()
    
    if not fab_note:
        raise error_response("FAB note not found", 404)
    
    # Delete the note
    await db.delete(fab_note)
    await db.commit()
    
    return None
