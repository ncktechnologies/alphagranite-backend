from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.slab_smith import SlabSmithSession, SlabSmithSessionNote
from src.app.database.user import User
from src.app.interface.business_schemas import SlabSmithSessionUpdate
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.timer_guards import assert_no_active_timer_session

router = APIRouter(
    prefix="/slabsmith",
    tags=["SlabSmith"]
)

@router.post("/{fab_id}/session", response_model=dict)
async def manage_slabsmith_session(
    fab_id: int,
    session_data: SlabSmithSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SlabSmith: Manage slabsmith session (start, pause, resume, end)
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
        select(SlabSmithSession)
        .where(
            SlabSmithSession.fab_id == fab_id,
            SlabSmithSession.user_id == current_user.id,
            SlabSmithSession.status.in_(["active", "paused"]),
        )
        .order_by(SlabSmithSession.created_at.desc())
        .limit(1)
    )
    active_session = active_session_result.scalar_one_or_none()

    session = None
    
    if action == "start":
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an open SlabSmith session for this FAB. End it first before starting a new one."
            )

        # Prevent starting if any running timer exists across all session types
        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        session = SlabSmithSession(
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
            SlabSmithSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="start",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                work_percentage_done=session_data.work_percentage_done,
                created_at=now,
            )
        )
        
        message = "SlabSmith session started"
    
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
            SlabSmithSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="pause",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                work_percentage_done=session_data.work_percentage_done,
                created_at=now,
            )
        )
        
        message = "SlabSmith session paused"
    
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
            SlabSmithSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="resume",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                work_percentage_done=session_data.work_percentage_done,
                created_at=now,
            )
        )
        
        message = "SlabSmith session resumed"
    
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
        
        # Calculate total time
        total_minutes = total_spent_seconds / 60
        
        # Store SlabSmith time in FAB
        fab.slabsmith_time_minutes = int(total_minutes)
        fab.updated_at = now
        fab.updated_by = current_user.id

        db.add(
            SlabSmithSessionNote(
                session_id=session.id,
                fab_id=fab_id,
                user_id=current_user.id,
                action="end",
                timestamp=now,
                note=note_value,
                sqft_completed=session_data.sqft_completed,
                work_percentage_done=session_data.work_percentage_done,
                created_at=now,
            )
        )
        
        message = f"SlabSmith session ended. Total time: {int(total_minutes)} minutes"
    
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
            "work_percentage_done": session_data.work_percentage_done,
        }
    }


@router.get("/{fab_id}/session-status", response_model=dict)
async def get_slabsmith_session_status(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SlabSmith: Get current session status
    """
    session_result = await db.execute(
        select(SlabSmithSession)
        .where(
            SlabSmithSession.fab_id == fab_id,
            SlabSmithSession.user_id == current_user.id,
            SlabSmithSession.status.in_(["active", "paused"]),
        )
        .order_by(SlabSmithSession.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        return {
            "success": True,
            "message": "No active session",
            "data": {
                "fab_id": fab_id,
                "has_active_session": False,
                "sqft_completed": None,
                "work_percentage_done": None,
            }
        }

    notes_result = await db.execute(
        select(SlabSmithSessionNote)
        .where(SlabSmithSessionNote.session_id == session.id)
        .order_by(SlabSmithSessionNote.timestamp.desc(), SlabSmithSessionNote.id.desc())
    )
    sqft_completed = None
    work_percentage_done = None
    for session_note in notes_result.scalars().all():
        if sqft_completed is None and session_note.sqft_completed is not None:
            sqft_completed = session_note.sqft_completed
        if work_percentage_done is None and session_note.work_percentage_done is not None:
            work_percentage_done = session_note.work_percentage_done
        if sqft_completed is not None and work_percentage_done is not None:
            break
    
    # Calculate current duration
    current_time = datetime.now()
    if session.status == "active":
        total_seconds = int((current_time - session.session_start_time).total_seconds()) - session.total_pause_duration
        duration_minutes = max(total_seconds, 0) / 60
    else:  # paused
        pause_anchor = session.current_pause_start_time or current_time
        total_seconds = int((pause_anchor - session.session_start_time).total_seconds()) - session.total_pause_duration
        duration_minutes = max(total_seconds, 0) / 60
    
    return {
        "success": True,
        "message": "Session status retrieved",
        "data": {
            "fab_id": fab_id,
            "has_active_session": True,
            "status": session.status,
            "start_time": session.session_start_time.isoformat(),
            "paused_at": session.current_pause_start_time.isoformat() if session.current_pause_start_time else None,
            "duration_minutes": int(duration_minutes),
            "sqft_completed": sqft_completed,
            "work_percentage_done": work_percentage_done,
        }
    }


@router.get("/{fab_id}/session-history", response_model=dict)
async def get_slabsmith_session_history(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SlabSmith: Return full session history for a FAB."""
    _ = current_user

    fab = (await db.execute(select(Fab).where(Fab.id == fab_id))).scalar_one_or_none()
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found",
        )

    sessions = (
        await db.execute(
            select(SlabSmithSession)
            .where(SlabSmithSession.fab_id == fab_id)
            .order_by(SlabSmithSession.created_at.desc(), SlabSmithSession.id.desc())
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
            select(SlabSmithSessionNote)
            .where(SlabSmithSessionNote.session_id.in_(session_ids))
            .order_by(SlabSmithSessionNote.timestamp.asc(), SlabSmithSessionNote.id.asc())
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
                "work_percentage_done": n.work_percentage_done,
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
        "message": f"Found {len(session_rows)} slabsmith sessions",
        "data": {
            "fab_id": fab_id,
            "total_sessions": len(session_rows),
            "sessions": session_rows,
        },
    }