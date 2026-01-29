from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.fab_notes import FabNotes
from src.app.database.user import User
from src.app.interface.business_schemas import (
    FinalProgrammingSessionUpdate,
    FinalProgrammingScheduleShopDate,
    FinalProgrammingComplete,
    FabResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter(
    prefix="/final-programming",
    tags=["Final Programming"]
)


# In-memory storage for session tracking (in production, use database table)
programming_sessions = {}


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
    
    if action == "start":
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
            "wj_time_minutes": fab.wj_time_minutes,
            "current_stage": fab.current_stage,  # Remains "cut_list"
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
