from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.fab_notes import FabNotes
from src.app.database.user import User
from src.app.interface.business_schemas import SlabSmithSessionUpdate
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.timer_guards import assert_no_active_timer_session

router = APIRouter(
    prefix="/slabsmith",
    tags=["SlabSmith"]
)

# In-memory storage for session tracking
slabsmith_sessions = {}


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
    
    session_key = f"{fab_id}_{current_user.id}"
    action = session_data.action.lower()
    
    if action == "start":
        # Prevent starting if any running timer exists across all session types
        if not getattr(current_user, "is_super_admin", False):
            await assert_no_active_timer_session(db, current_user.id)

        # Start new session
        slabsmith_sessions[session_key] = {
            "fab_id": fab_id,
            "user_id": current_user.id,
            "start_time": datetime.now(),
            "paused_at": None,
            "total_paused_minutes": 0,
            "status": "active"
        }
        
        # Add note
        note_text = f"SlabSmith session started by {current_user.first_name} {current_user.last_name}"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="slabsmith",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "SlabSmith session started"
    
    elif action == "pause":
        # Pause session
        if session_key not in slabsmith_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to pause"
            )
        
        session = slabsmith_sessions[session_key]
        if session["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        session["paused_at"] = datetime.now()
        session["status"] = "paused"
        
        # Add note
        note_text = "SlabSmith session paused"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="slabsmith",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "SlabSmith session paused"
    
    elif action == "resume":
        # Resume session
        if session_key not in slabsmith_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to resume"
            )
        
        session = slabsmith_sessions[session_key]
        if session["status"] != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused"
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
        note_text = "SlabSmith session resumed"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="slabsmith",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        message = "SlabSmith session resumed"
    
    elif action == "end":
        # End session
        if session_key not in slabsmith_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to end"
            )
        
        session = slabsmith_sessions[session_key]
        
        # Calculate total time
        end_time = datetime.now()
        total_minutes = (end_time - session["start_time"]).total_seconds() / 60
        total_minutes -= session["total_paused_minutes"]
        
        # Store SlabSmith time in FAB (you may need to add this field to FAB model)
        fab.slabsmith_time_minutes = int(total_minutes)
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
        
        # Add note
        note_text = f"SlabSmith session ended. Total time: {int(total_minutes)} minutes"
        if session_data.notes:
            note_text += f" - {session_data.notes}"
        
        fab_note = FabNotes(
            fab_id=fab_id,
            note=note_text,
            stage="slabsmith",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
        
        # Remove session
        del slabsmith_sessions[session_key]
        
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
            "session_active": session_key in slabsmith_sessions
        }
    }


@router.get("/{fab_id}/session-status", response_model=dict)
async def get_slabsmith_session_status(
    fab_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    SlabSmith: Get current session status
    """
    session_key = f"{fab_id}_{current_user.id}"
    
    if session_key not in slabsmith_sessions:
        return {
            "success": True,
            "message": "No active session",
            "data": {
                "fab_id": fab_id,
                "has_active_session": False
            }
        }
    
    session = slabsmith_sessions[session_key]
    
    # Calculate current duration
    current_time = datetime.now()
    if session["status"] == "active":
        duration_minutes = (current_time - session["start_time"]).total_seconds() / 60
        duration_minutes -= session["total_paused_minutes"]
    else:  # paused
        duration_minutes = (session["paused_at"] - session["start_time"]).total_seconds() / 60
        duration_minutes -= session["total_paused_minutes"]
    
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