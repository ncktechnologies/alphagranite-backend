from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.fab_notes import FabNotes
from src.app.database.final_programming import FinalProgrammingSession, FinalProgrammingSessionNote
from src.app.database.user import User
from src.app.interface.generated_schemas import FinalProgramming
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
    
    action = session_data.action.lower()
    note_value = (session_data.note or "").strip() or None
    now = datetime.now()

    active_session_result = await db.execute(
        select(FinalProgrammingSession)
        .where(
            FinalProgrammingSession.fab_id == fab_id,
            FinalProgrammingSession.user_id == current_user.id,
            FinalProgrammingSession.status.in_(["active", "paused"]),
        )
        .order_by(FinalProgrammingSession.created_at.desc())
        .limit(1)
    )
    active_session = active_session_result.scalar_one_or_none()

    session = None
    
    if action == "start":
        # Prevent starting if any running timer exists across all session types
        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an open Final Programming session for this FAB. End it first before starting a new one."
            )

        session = FinalProgrammingSession(
            fab_id=fab_id,
            user_id=current_user.id,
            status="active",
            session_start_time=now,
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        await db.flush()

        db.add(
            FinalProgrammingSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="start",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                created_at=now,
            )
        )
        
        message = "Final programming session started"
    
    elif action == "pause":
        # Pause session
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to pause"
            )

        if active_session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )

        active_session.status = "paused"
        active_session.current_pause_start_time = now
        active_session.updated_at = now
        session = active_session

        db.add(
            FinalProgrammingSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="pause",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                created_at=now,
            )
        )
        
        message = "Final programming session paused"
    
    elif action == "resume":
        # Resume session
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to resume"
            )

        if active_session.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused"
            )

        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        if active_session.current_pause_start_time:
            paused_seconds = int((now - active_session.current_pause_start_time).total_seconds())
            active_session.total_pause_duration += max(paused_seconds, 0)

        active_session.current_pause_start_time = None
        active_session.status = "active"
        active_session.updated_at = now
        session = active_session

        db.add(
            FinalProgrammingSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="resume",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                created_at=now,
            )
        )
        
        message = "Final programming session resumed"
    
    elif action == "end":
        # End session
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to end"
            )

        if active_session.current_pause_start_time:
            paused_seconds = int((now - active_session.current_pause_start_time).total_seconds())
            active_session.total_pause_duration += max(paused_seconds, 0)
            active_session.current_pause_start_time = None

        total_seconds = int((now - active_session.session_start_time).total_seconds())
        total_spent_seconds = max(total_seconds - active_session.total_pause_duration, 0)

        active_session.total_time_spent = total_spent_seconds
        active_session.status = "completed"
        active_session.session_end_time = now
        active_session.updated_at = now
        session = active_session

        total_minutes = total_spent_seconds / 60
        
        # Store WJ time in FAB
        fab.wj_time_minutes = int(total_minutes)
        fab.updated_at = now
        fab.updated_by = current_user.id

        db.add(
            FinalProgrammingSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="end",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                created_at=now,
            )
        )
        
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
            "session_active": session is not None and session.status in ["active", "paused"],
            "note": note_value,
            "sqft_completed": session_data.sqft_completed,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Final Programming: Get current session status
    """
    session_result = await db.execute(
        select(FinalProgrammingSession)
        .where(
            FinalProgrammingSession.fab_id == fab_id,
            FinalProgrammingSession.user_id == current_user.id,
            FinalProgrammingSession.status.in_(["active", "paused"]),
        )
        .order_by(FinalProgrammingSession.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        return {
            "success": True,
            "message": "No active session",
            "data": {
                "fab_id": fab_id,
                "has_active_session": False
            }
        }
    
    # Calculate current duration in seconds (but keep variable name for backward compatibility)
    current_time = datetime.now()
    if session.status == "active":
        duration_seconds = int((current_time - session.session_start_time).total_seconds()) - session.total_pause_duration
    else:  # paused
        pause_anchor = session.current_pause_start_time or current_time
        duration_seconds = int((pause_anchor - session.session_start_time).total_seconds()) - session.total_pause_duration

    duration_minutes = max(duration_seconds, 0)
    
    return {
        "success": True,
        "message": "Session status retrieved",
        "data": {
            "fab_id": fab_id,
            "has_active_session": True,
            "status": session.status,
            "start_time": session.session_start_time.isoformat(),
            "paused_at": session.current_pause_start_time.isoformat() if session.current_pause_start_time else None,
            "duration_minutes": int(duration_minutes)
        }
    }


@router.get("/{fab_id}/session-history", response_model=dict)
async def get_final_programming_session_history(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Final Programming: Return full session history for a FAB."""
    _ = current_user

    fab = (await db.execute(select(Fab).where(Fab.id == fab_id))).scalar_one_or_none()
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found",
        )

    sessions = (
        await db.execute(
            select(FinalProgrammingSession)
            .where(FinalProgrammingSession.fab_id == fab_id)
            .order_by(FinalProgrammingSession.created_at.desc(), FinalProgrammingSession.id.desc())
        )
    ).scalars().all()

    if not sessions:
        return {
            "success": True,
            "message": "No session history found",
            "data": {
                "fab_id": fab_id,
                "total_sessions": 0,
                "sessions": [],
            },
        }

    session_ids = [session.id for session in sessions if session.id is not None]
    notes = (
        await db.execute(
            select(FinalProgrammingSessionNote)
            .where(FinalProgrammingSessionNote.session_id.in_(session_ids))
            .order_by(FinalProgrammingSessionNote.timestamp.asc(), FinalProgrammingSessionNote.id.asc())
        )
    ).scalars().all()

    notes_by_session_id: dict[int, list[dict]] = {}
    for n in notes:
        notes_by_session_id.setdefault(n.session_id, []).append(
            {
                "id": n.id,
                "action": n.action,
                "timestamp": n.timestamp.isoformat() if n.timestamp else None,
                "note": n.note,
                "sqft_completed": n.sqft_completed,
                "user_id": n.user_id,
            }
        )

    now = datetime.now()
    session_rows: list[dict] = []
    for session in sessions:
        duration_seconds = int(session.total_time_spent or 0)
        if session.status in ["active", "paused"]:
            anchor = now if session.status == "active" else (session.current_pause_start_time or now)
            duration_seconds = max(
                int((anchor - session.session_start_time).total_seconds()) - int(session.total_pause_duration or 0),
                0,
            )

        session_rows.append(
            {
                "session_id": session.id,
                "fab_id": session.fab_id,
                "user_id": session.user_id,
                "status": session.status,
                "session_start_time": session.session_start_time.isoformat() if session.session_start_time else None,
                "session_end_time": session.session_end_time.isoformat() if session.session_end_time else None,
                "current_pause_start_time": session.current_pause_start_time.isoformat() if session.current_pause_start_time else None,
                "total_pause_duration": int(session.total_pause_duration or 0),
                "total_time_spent": int(session.total_time_spent or 0),
                "duration_seconds": int(duration_seconds),
                "duration_minutes": round(duration_seconds / 60, 2),
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "notes": notes_by_session_id.get(session.id, []),
            }
        )

    return {
        "success": True,
        "message": f"Found {len(session_rows)} final programming sessions",
        "data": {
            "fab_id": fab_id,
            "total_sessions": len(session_rows),
            "sessions": session_rows,
        },
    }
