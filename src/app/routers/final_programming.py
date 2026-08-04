from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.fab_notes import FabNotes
from src.app.database.user import User
from src.app.interface.generated_schemas import FinalProgramming, DraftingSession
from src.app.interface.business_schemas import (
    FinalProgrammingCreate,
    FinalProgrammingUpdate,
    FinalProgrammingSessionUpdate,
    FinalProgrammingScheduleShopDate,
    FinalProgrammingComplete,
    FabResponse
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.timer_guards import assert_no_active_timer_session

router = APIRouter(
    prefix="/final-programming",
    tags=["Final Programming"]
)


# In-memory storage for session tracking (in production, use database table)
programming_sessions = {}


def _final_programming_response_data(final_programming: FinalProgramming) -> dict:
    return {
        "id": final_programming.id,
        "drafter_id": final_programming.drafter_id,
        "fab_id": final_programming.fab_id,
        "scheduled_start_date": final_programming.scheduled_start_date.isoformat() if final_programming.scheduled_start_date else None,
        "scheduled_end_date": final_programming.scheduled_end_date.isoformat() if final_programming.scheduled_end_date else None,
        "drafter_start_date": final_programming.drafter_start_date.isoformat() if final_programming.drafter_start_date else None,
        "drafter_end_date": final_programming.drafter_end_date.isoformat() if final_programming.drafter_end_date else None,
        "is_completed": final_programming.is_completed,
        "status_id": final_programming.status_id,
        "created_at": final_programming.created_at.isoformat() if final_programming.created_at else None,
        "updated_at": final_programming.updated_at.isoformat() if final_programming.updated_at else None,
        "updated_by": final_programming.updated_by,
        "file_ids": final_programming.file_ids,
        "no_of_piece_drafted": final_programming.no_of_piece_drafted,
        "total_sqft_required_to_draft": final_programming.total_sqft_required_to_draft,
        "total_sqft_drafted": final_programming.total_sqft_drafted,
        "notes": final_programming.notes,
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_final_programming(
    payload: FinalProgrammingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a final programming record with full model data."""

    fab_result = await db.execute(select(Fab).where(Fab.id == payload.fab_id))
    if not fab_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {payload.fab_id} not found",
        )

    drafter_result = await db.execute(select(User).where(User.id == payload.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drafter with ID {payload.drafter_id} not found",
        )

    final_programming = FinalProgramming(
        drafter_id=payload.drafter_id,
        fab_id=payload.fab_id,
        scheduled_start_date=payload.scheduled_start_date,
        scheduled_end_date=payload.scheduled_end_date,
        drafter_start_date=payload.drafter_start_date,
        drafter_end_date=payload.drafter_end_date,
        is_completed=payload.is_completed,
        status_id=payload.status_id,
        created_at=datetime.now(),
        updated_at=None,
        updated_by=None,
        file_ids=payload.file_ids,
        no_of_piece_drafted=payload.no_of_piece_drafted,
        total_sqft_required_to_draft=payload.total_sqft_required_to_draft,
        total_sqft_drafted=payload.total_sqft_drafted,
        notes=payload.notes,
    )

    db.add(final_programming)
    await db.commit()
    await db.refresh(final_programming)

    return {
        "success": True,
        "message": "Final programming created successfully",
        "data": _final_programming_response_data(final_programming),
    }


@router.put("/{fp_id}", response_model=dict)
async def update_final_programming_record(
    fp_id: int,
    payload: FinalProgrammingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a final programming record with full model fields."""

    result = await db.execute(select(FinalProgramming).where(FinalProgramming.id == fp_id))
    final_programming = result.scalar_one_or_none()

    if not final_programming:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Final programming with ID {fp_id} not found",
        )

    if payload.fab_id is not None:
        fab_result = await db.execute(select(Fab).where(Fab.id == payload.fab_id))
        if not fab_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAB with ID {payload.fab_id} not found",
            )

    if payload.drafter_id is not None:
        drafter_result = await db.execute(select(User).where(User.id == payload.drafter_id))
        if not drafter_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drafter with ID {payload.drafter_id} not found",
            )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(final_programming, field, value)

    final_programming.updated_at = datetime.now()
    final_programming.updated_by = current_user.id

    await db.commit()
    await db.refresh(final_programming)

    return {
        "success": True,
        "message": "Final programming updated successfully",
        "data": _final_programming_response_data(final_programming),
    }


@router.put("/fab/{fab_id}", response_model=dict)
async def update_final_programming_by_fab_id(
    fab_id: int,
    payload: FinalProgrammingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the latest final programming record by FAB ID."""

    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    if not fab_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found",
        )

    result = await db.execute(
        select(FinalProgramming)
        .where(FinalProgramming.fab_id == fab_id)
        .order_by(FinalProgramming.created_at.desc(), FinalProgramming.id.desc())
        .limit(1)
    )
    final_programming = result.scalar_one_or_none()

    if not final_programming:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No final programming record found for FAB ID {fab_id}",
        )

    if payload.fab_id is not None and payload.fab_id != fab_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fab_id in payload must match path fab_id",
        )

    if payload.drafter_id is not None:
        drafter_result = await db.execute(select(User).where(User.id == payload.drafter_id))
        if not drafter_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drafter with ID {payload.drafter_id} not found",
            )

    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("fab_id", None)
    for field, value in update_data.items():
        setattr(final_programming, field, value)

    final_programming.updated_at = datetime.now()
    final_programming.updated_by = current_user.id

    await db.commit()
    await db.refresh(final_programming)

    return {
        "success": True,
        "message": "Final programming updated successfully by fab_id",
        "data": _final_programming_response_data(final_programming),
    }


@router.post("/{fab_id}/session", response_model=dict)
async def manage_programming_session(
    fab_id: int,
    session_data: FinalProgrammingSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Final Programming: Manage programming session (start, pause, resume, end)
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    session_key = f"{fab_id}_{current_user.id}"
    action = session_data.action.lower()

    async def get_user_open_drafting_sessions() -> list[tuple[int, int]]:
        open_drafting_result = await db.execute(
            select(DraftingSession.id, DraftingSession.fab_id)
            .where(
                DraftingSession.drafter_id == current_user.id,
                DraftingSession.status.in_(["drafting", "paused"]),
            )
        )
        return [(row[0], row[1]) for row in open_drafting_result.all()]

    def build_open_drafting_message(action_name: str, open_sessions: list[tuple[int, int]]) -> str:
        fab_ids = sorted({fab_id for _, fab_id in open_sessions if fab_id is not None})
        base_message = (
            f"Cannot {action_name} final programming yet. "
            "You still have open Drafting timer(s). "
            "Please end those Drafting timer(s) first."
        )

        if not fab_ids:
            return base_message

        fab_list = ", ".join(str(fab_id) for fab_id in fab_ids)
        return (
            f"Cannot {action_name} final programming yet. "
            f"You still have open Drafting timer(s) on FAB(s): {fab_list}. "
            "Please end those Drafting timer(s) first."
        )
    
    if action == "start":
        # Block final programming start while this user still has open drafting timers.
        open_drafting_sessions = await get_user_open_drafting_sessions()

        if open_drafting_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=build_open_drafting_message("start", open_drafting_sessions),
            )

        # Prevent starting if any running timer exists across all session types
        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        # Start new session
        programming_sessions[session_key] = {
            "fab_id": fab_id,
            "user_id": current_user.id,
            "start_time": datetime.now(),
            "paused_at": None,
            "total_paused_minutes": 0,
            "status": "active"
        }
        
        # Add note
        note_text = f"Final programming session started by {current_user.first_name} {current_user.last_name}"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="final_programming",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "Final programming session started"
    
    elif action == "pause":
        # Pause session
        if session_key not in programming_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to pause"
            )
        
        session = programming_sessions[session_key]
        if session["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        session["paused_at"] = datetime.now()
        session["status"] = "paused"
        
        # Add note
        note_text = "Final programming session paused"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="final_programming",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "Final programming session paused"
    
    elif action == "resume":
        # Resume session
        if session_key not in programming_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to resume"
            )
        
        session = programming_sessions[session_key]
        if session["status"] != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused"
            )

        open_drafting_sessions = await get_user_open_drafting_sessions()
        if open_drafting_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=build_open_drafting_message("resume", open_drafting_sessions),
            )

        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        # Calculate paused time
        if session["paused_at"]:
            paused_minutes = (datetime.now() - session["paused_at"]).total_seconds() / 60
            session["total_paused_minutes"] += paused_minutes
        
        session["paused_at"] = None
        session["status"] = "active"
        
        # Add note
        note_text = "Final programming session resumed"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="final_programming",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "Final programming session resumed"
    
    elif action == "end":
        # End session
        if session_key not in programming_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to end"
            )
        
        session = programming_sessions[session_key]
        
        # Calculate total time
        end_time = datetime.now()
        total_minutes = (end_time - session["start_time"]).total_seconds() / 60
        total_minutes -= session["total_paused_minutes"]
        
        # Store WJ time in FAB
        fab.wj_time_minutes = int(total_minutes)
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
        
        # Add note
        note_text = f"Final programming session ended. Total time: {int(total_minutes)} minutes"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="final_programming",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        # Remove session
        del programming_sessions[session_key]
        
        message = f"Final programming session ended. Total time: {int(total_minutes)} minutes"
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Must be 'start', 'pause', 'resume', or 'end'"
        )
    
    await db.commit()
    
    return {
        "success": True,
        "message": message,
        "data": {
            "fab_id": fab_id,
            "action": action,
            "session_active": session_key in programming_sessions
        }
    }


@router.post("/{fab_id}/schedule-shop-date", response_model=dict)
async def schedule_shop_date(
    fab_id: int,
    schedule_data: FinalProgrammingScheduleShopDate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Final Programming: Schedule shop date (writes to Cut List stage)
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Update shop date and related fields
    fab.shop_date_schedule = schedule_data.shop_date_schedule
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Update optional fields if provided
    if schedule_data.installation_date:
        fab.installation_date = schedule_data.installation_date
    
    if schedule_data.no_of_pieces:
        fab.no_of_pieces = schedule_data.no_of_pieces
    
    if schedule_data.total_sqft:
        fab.total_sqft = schedule_data.total_sqft
    
    if schedule_data.wj_linft is not None:
        fab.wj_linft = schedule_data.wj_linft
    
    if schedule_data.edging_linft is not None:
        fab.edging_linft = schedule_data.edging_linft
    
    if schedule_data.cnc_linft is not None:
        fab.cnc_linft = schedule_data.cnc_linft
    
    if schedule_data.miter_linft is not None:
        fab.miter_linft = schedule_data.miter_linft
    
    if schedule_data.confirmed is not None and schedule_data.confirmed:
        fab.confirmed_date = datetime.now()
    
    # Add note
    fab_note = FabNotes(
        fab_id=fab_id,
        note=f"Shop date scheduled from Final Programming for {schedule_data.shop_date_schedule.strftime('%Y-%m-%d')}",
        stage="final_programming",
        created_by=current_user.id,
        created_at=datetime.now()
    )
    db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    return {
        "success": True,
        "message": "Shop date scheduled successfully",
        "data": {
            "fab_id": fab.id,
            "shop_date_schedule": fab.shop_date_schedule.isoformat() if fab.shop_date_schedule else None,
            "installation_date": fab.installation_date.isoformat() if fab.installation_date else None,
            "confirmed_date": fab.confirmed_date.isoformat() if fab.confirmed_date else None
        }
    }


@router.post("/{fab_id}/complete", response_model=dict)
async def complete_final_programming(
    fab_id: int,
    completion_data: FinalProgrammingComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Final Programming: Mark final programming as complete
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Mark as complete
    fab.final_programming_complete = completion_data.final_programming_complete

    # Save actual completion date when marked complete; clear when un-completed
    if completion_data.final_programming_complete:
        fab.final_programming_completed_date = datetime.now()
    else:
        fab.final_programming_completed_date = None

    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Update optional fields
    if completion_data.wj_time_minutes:
        fab.wj_time_minutes = completion_data.wj_time_minutes
    
    if completion_data.drafter_id:
        fab.drafter_id = completion_data.drafter_id
        fab.drafter_assigned_by = current_user.id
        fab.drafter_assigned_at = datetime.now()
    
    # ❌ REMOVED: Do NOT change current_stage
    # if completion_data.final_programming_complete:
    #     fab.current_stage = "wj_programming"
    #     fab.next_stage = "cut_list"
    
    # ✅ Keep current_stage at "cut_list" (don't change it)
    # The stage remains "cut_list" after final programming is complete
    
    # Add completion notes
    note_text = f"Final programming {'completed' if completion_data.final_programming_complete else 'updated'}"
    if completion_data.notes:
        note_text += f" - {completion_data.notes}"
    
    fab_note = FabNotes(
        fab_id=fab_id,
        note=note_text,
        stage="final_programming",
        created_by=current_user.id,
        created_at=datetime.now()
    )
    db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    return {
        "success": True,
        "message": f"Final programming {'completed' if completion_data.final_programming_complete else 'updated'} successfully",
        "data": {
            "fab_id": fab.id,
            "final_programming_complete": fab.final_programming_complete,
            "final_programming_completed_date": (
                fab.final_programming_completed_date.isoformat()
                if fab.final_programming_completed_date else None
            ),
            "wj_time_minutes": fab.wj_time_minutes,
            "current_stage": fab.current_stage,
            "next_stage": fab.next_stage
        }
    }


@router.get("/{fab_id}/session-status", response_model=dict)
async def get_session_status(
    fab_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Final Programming: Get current session status
    """
    session_key = f"{fab_id}_{current_user.id}"
    
    if session_key not in programming_sessions:
        return {
            "success": True,
            "message": "No active session",
            "data": {
                "fab_id": fab_id,
                "has_active_session": False
            }
        }
    
    session = programming_sessions[session_key]
    
    # Calculate current duration in seconds (but keep variable name for backward compatibility)
    current_time = datetime.now()
    if session["status"] == "active":
        duration_minutes = (current_time - session["start_time"]).total_seconds()
        duration_minutes -= (session["total_paused_minutes"] * 60)
    else:  # paused
        duration_minutes = (session["paused_at"] - session["start_time"]).total_seconds()
        duration_minutes -= (session["total_paused_minutes"] * 60)
    
    return {
        "success": True,
        "message": "Session status retrieved",
        "data": {
            "fab_id": fab_id,
            "has_active_session": True,
            "status": session["status"],
            "start_time": session["start_time"].isoformat(),
            "paused_at": session["paused_at"].isoformat() if session["paused_at"] else None,
            "duration_minutes": int(duration_minutes)
        }
    }
