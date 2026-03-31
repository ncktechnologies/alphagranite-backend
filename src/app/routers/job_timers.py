from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.installer_job_timer_event import InstallerJobTimerEvent
from src.app.database.installer_job_timer_session import InstallerJobTimerSession
from src.app.database.templater_job_timer_event import TemplaterJobTimerEvent
from src.app.database.templater_job_timer_session import TemplaterJobTimerSession
from src.app.database.user import User
from src.app.interface.business_schemas import (
    InstallerJobTimerActionRequest,
    InstallerJobTimerCommandRequest,
    InstallerJobTimerEventResponse,
    InstallerJobTimerHistoryResponse,
    InstallerJobTimerSessionResponse,
    InstallerJobTimerStateResponse,
    TemplaterJobTimerActionRequest,
    TemplaterJobTimerCommandRequest,
    TemplaterJobTimerEventResponse,
    TemplaterJobTimerHistoryResponse,
    TemplaterJobTimerSessionResponse,
    TemplaterJobTimerStateResponse,
)
from src.app.interface.response_wrappers import SuccessResponse
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response

router = APIRouter(
    prefix="/job-timers",
    tags=["Job Timers"],
)


async def _get_fab_and_job_id(db: AsyncSession, fab_id: int) -> tuple[Fab, int]:
    """Helper to get fab and its job_id"""
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    return fab, fab.job_id


def _format_duration_hms(total_seconds: int) -> str:
    """Format seconds as HH:MM:SS"""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _serialize_installer_job_timer_session(session: InstallerJobTimerSession) -> dict:
    return {
        "id": session.id,
        "job_id": session.job_id,
        "fab_id": session.fab_id,
        "installer_id": session.installer_id,
        "status": session.status,
        "session_start_at": session.session_start_at.isoformat() if session.session_start_at else None,
        "current_run_start_at": session.current_run_start_at.isoformat() if session.current_run_start_at else None,
        "current_pause_start_at": session.current_pause_start_at.isoformat() if session.current_pause_start_at else None,
        "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
        "total_work_seconds": session.total_work_seconds,
        "total_pause_seconds": session.total_pause_seconds,
        "sqft_installed": session.sqft_installed,
        "sqft_not_installed": session.sqft_not_installed,
    }


def _serialize_installer_job_timer_event(event: InstallerJobTimerEvent) -> dict:
    return {
        "id": event.id,
        "session_id": event.session_id,
        "action": event.action,
        "event_at": event.event_at.isoformat() if event.event_at else None,
        "note": event.note,
    }


def _serialize_templater_job_timer_session(session: TemplaterJobTimerSession) -> dict:
    return {
        "id": session.id,
        "job_id": session.job_id,
        "fab_id": session.fab_id,
        "templater_id": session.templater_id,
        "status": session.status,
        "session_start_at": session.session_start_at.isoformat() if session.session_start_at else None,
        "current_run_start_at": session.current_run_start_at.isoformat() if session.current_run_start_at else None,
        "current_pause_start_at": session.current_pause_start_at.isoformat() if session.current_pause_start_at else None,
        "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
        "total_work_seconds": session.total_work_seconds,
        "total_pause_seconds": session.total_pause_seconds,
        "sqft_templated": session.sqft_templated,
        "sqft_not_templated": session.sqft_not_templated,
    }


def _serialize_templater_job_timer_event(event: TemplaterJobTimerEvent) -> dict:
    return {
        "id": event.id,
        "session_id": event.session_id,
        "action": event.action,
        "event_at": event.event_at.isoformat() if event.event_at else None,
        "note": event.note,
    }


# ===========================
# Installer Timer Endpoints
# ===========================

@router.post("/installer/jobs/{job_id}/timer/start", response_model=SuccessResponse[dict])
async def start_installer_job_timer(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an installer timer for a job"""
    
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        raise error_response("Job not found", 404)
    
    # Verify installer user exists
    installer_result = await db.execute(select(User).where(User.id == installer_id))
    if not installer_result.scalar_one_or_none():
        raise error_response("Installer not found", 404)
    
    # Verify fab if provided
    if fab_id:
        fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
        if not fab_result.scalar_one_or_none():
            raise error_response("Fab not found", 404)
    
    # Check if there's already an active timer
    active_result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
            InstallerJobTimerSession.status.in_(["running", "paused"]),
        )
    )
    active_session = active_result.scalar_one_or_none()
    
    if active_session:
        raise error_response("An active timer already exists for this installer and job", 400)
    
    # Create new session
    now = datetime.now()
    new_session = InstallerJobTimerSession(
        job_id=job_id,
        fab_id=fab_id,
        installer_id=installer_id,
        status="running",
        session_start_at=now,
        current_run_start_at=now,
        created_at=now,
        created_by=current_user.id,
        sqft_installed=payload.sqft_installed if payload else None,
        sqft_not_installed=payload.sqft_not_installed if payload else None,
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Create event
    event = InstallerJobTimerEvent(
        session_id=new_session.id,
        job_id=job_id,
        fab_id=fab_id,
        installer_id=installer_id,
        action="start",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_installer_job_timer_session(new_session),
        "Installer timer started"
    )


@router.post("/installer/jobs/{job_id}/timer/pause", response_model=SuccessResponse[dict])
async def pause_installer_job_timer(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause an installer timer"""
    
    result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
            InstallerJobTimerSession.status == "running",
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No active timer found for this installer and job", 404)
    
    now = datetime.now()
    
    # Calculate time for current run segment
    if session.current_run_start_at:
        run_time = (now - session.current_run_start_at).total_seconds()
        session.total_work_seconds += int(run_time)
        session.current_run_start_at = None
    
    session.status = "paused"
    session.current_pause_start_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_installed is not None:
        session.sqft_installed = payload.sqft_installed
    if payload and payload.sqft_not_installed is not None:
        session.sqft_not_installed = payload.sqft_not_installed
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = InstallerJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        installer_id=installer_id,
        action="pause",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_installer_job_timer_session(session),
        "Installer timer paused"
    )


@router.post("/installer/jobs/{job_id}/timer/resume", response_model=SuccessResponse[dict])
async def resume_installer_job_timer(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused installer timer"""
    
    result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
            InstallerJobTimerSession.status == "paused",
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No paused timer found for this installer and job", 404)
    
    now = datetime.now()
    
    # Calculate pause time
    if session.current_pause_start_at:
        pause_time = (now - session.current_pause_start_at).total_seconds()
        session.total_pause_seconds += int(pause_time)
        session.current_pause_start_at = None
    
    session.status = "running"
    session.current_run_start_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_installed is not None:
        session.sqft_installed = payload.sqft_installed
    if payload and payload.sqft_not_installed is not None:
        session.sqft_not_installed = payload.sqft_not_installed
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = InstallerJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        installer_id=installer_id,
        action="resume",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_installer_job_timer_session(session),
        "Installer timer resumed"
    )


@router.post("/installer/jobs/{job_id}/timer/stop", response_model=SuccessResponse[dict])
async def stop_installer_job_timer(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop an installer timer"""
    
    result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
            InstallerJobTimerSession.status.in_(["running", "paused"]),
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No active timer found for this installer and job", 404)
    
    now = datetime.now()
    
    # Calculate remaining time
    if session.current_run_start_at:
        run_time = (now - session.current_run_start_at).total_seconds()
        session.total_work_seconds += int(run_time)
        session.current_run_start_at = None
    
    if session.current_pause_start_at:
        pause_time = (now - session.current_pause_start_at).total_seconds()
        session.total_pause_seconds += int(pause_time)
        session.current_pause_start_at = None
    
    session.status = "stopped"
    session.stopped_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_installed is not None:
        session.sqft_installed = payload.sqft_installed
    if payload and payload.sqft_not_installed is not None:
        session.sqft_not_installed = payload.sqft_not_installed
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = InstallerJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        installer_id=installer_id,
        action="stop",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_installer_job_timer_session(session),
        "Installer timer stopped"
    )


@router.get("/installer/jobs/{job_id}/timer", response_model=SuccessResponse[dict])
async def get_installer_job_timer_state(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current installer timer state for a job"""
    
    # Get latest session
    result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
        )
        .order_by(InstallerJobTimerSession.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    
    # Calculate total time
    total_seconds = 0
    sessions_result = await db.execute(
        select(func.coalesce(func.sum(InstallerJobTimerSession.total_work_seconds), 0)).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
        )
    )
    total_seconds = sessions_result.scalar()
    
    # Add current running time
    if latest and latest.status == "running" and latest.current_run_start_at:
        run_time = (datetime.now() - latest.current_run_start_at).total_seconds()
        total_seconds += int(run_time)
    
    total_hours = total_seconds / 3600.0
    
    return success_response(
        {
            "job_id": job_id,
            "installer_id": installer_id,
            "fab_id": fab_id,
            "session": _serialize_installer_job_timer_session(latest) if latest else None,
            "total_actual_seconds": int(total_seconds),
            "total_actual_hours": round(total_hours, 2),
        },
        "Installer timer state retrieved"
    )


@router.get("/installer/jobs/{job_id}/timer/history", response_model=SuccessResponse[dict])
async def get_installer_job_timer_history(
    job_id: int,
    installer_id: int = Query(..., gt=0, description="Installer user ID"),
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timer history for an installer on a job"""
    
    # Get all sessions
    sessions_result = await db.execute(
        select(InstallerJobTimerSession).where(
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.installer_id == installer_id,
        )
        .order_by(InstallerJobTimerSession.created_at)
    )
    sessions = sessions_result.scalars().all()
    
    # Get all events
    events_result = await db.execute(
        select(InstallerJobTimerEvent).where(
            InstallerJobTimerEvent.job_id == job_id,
            InstallerJobTimerEvent.installer_id == installer_id,
        )
        .order_by(InstallerJobTimerEvent.event_at)
    )
    events = events_result.scalars().all()
    
    return success_response(
        {
            "job_id": job_id,
            "installer_id": installer_id,
            "fab_id": fab_id,
            "sessions": [_serialize_installer_job_timer_session(s) for s in sessions],
            "events": [_serialize_installer_job_timer_event(e) for e in events],
        },
        "Installer timer history retrieved"
    )


# ===========================
# Templater Timer Endpoints
# ===========================

@router.post("/templater/jobs/{job_id}/timer/start", response_model=SuccessResponse[dict])
async def start_templater_job_timer(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    payload: TemplaterJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a templater timer for a job"""
    
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        raise error_response("Job not found", 404)
    
    # Verify templater user exists
    templater_result = await db.execute(select(User).where(User.id == templater_id))
    if not templater_result.scalar_one_or_none():
        raise error_response("Templater not found", 404)
    
    # Verify fab if provided
    if fab_id:
        fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
        if not fab_result.scalar_one_or_none():
            raise error_response("Fab not found", 404)
    
    # Check if there's already an active timer
    active_result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
            TemplaterJobTimerSession.status.in_(["running", "paused"]),
        )
    )
    active_session = active_result.scalar_one_or_none()
    
    if active_session:
        raise error_response("An active timer already exists for this templater and job", 400)
    
    # Create new session
    now = datetime.now()
    new_session = TemplaterJobTimerSession(
        job_id=job_id,
        fab_id=fab_id,
        templater_id=templater_id,
        status="running",
        session_start_at=now,
        current_run_start_at=now,
        created_at=now,
        created_by=current_user.id,
        sqft_templated=payload.sqft_templated if payload else None,
        sqft_not_templated=payload.sqft_not_templated if payload else None,
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Create event
    event = TemplaterJobTimerEvent(
        session_id=new_session.id,
        job_id=job_id,
        fab_id=fab_id,
        templater_id=templater_id,
        action="start",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_templater_job_timer_session(new_session),
        "Templater timer started"
    )


@router.post("/templater/jobs/{job_id}/timer/pause", response_model=SuccessResponse[dict])
async def pause_templater_job_timer(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    payload: TemplaterJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a templater timer"""
    
    result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
            TemplaterJobTimerSession.status == "running",
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No active timer found for this templater and job", 404)
    
    now = datetime.now()
    
    # Calculate time for current run segment
    if session.current_run_start_at:
        run_time = (now - session.current_run_start_at).total_seconds()
        session.total_work_seconds += int(run_time)
        session.current_run_start_at = None
    
    session.status = "paused"
    session.current_pause_start_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_templated is not None:
        session.sqft_templated = payload.sqft_templated
    if payload and payload.sqft_not_templated is not None:
        session.sqft_not_templated = payload.sqft_not_templated
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = TemplaterJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        templater_id=templater_id,
        action="pause",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_templater_job_timer_session(session),
        "Templater timer paused"
    )


@router.post("/templater/jobs/{job_id}/timer/resume", response_model=SuccessResponse[dict])
async def resume_templater_job_timer(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    payload: TemplaterJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused templater timer"""
    
    result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
            TemplaterJobTimerSession.status == "paused",
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No paused timer found for this templater and job", 404)
    
    now = datetime.now()
    
    # Calculate pause time
    if session.current_pause_start_at:
        pause_time = (now - session.current_pause_start_at).total_seconds()
        session.total_pause_seconds += int(pause_time)
        session.current_pause_start_at = None
    
    session.status = "running"
    session.current_run_start_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_templated is not None:
        session.sqft_templated = payload.sqft_templated
    if payload and payload.sqft_not_templated is not None:
        session.sqft_not_templated = payload.sqft_not_templated
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = TemplaterJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        templater_id=templater_id,
        action="resume",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_templater_job_timer_session(session),
        "Templater timer resumed"
    )


@router.post("/templater/jobs/{job_id}/timer/stop", response_model=SuccessResponse[dict])
async def stop_templater_job_timer(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    payload: TemplaterJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop a templater timer"""
    
    result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
            TemplaterJobTimerSession.status.in_(["running", "paused"]),
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No active timer found for this templater and job", 404)
    
    now = datetime.now()
    
    # Calculate remaining time
    if session.current_run_start_at:
        run_time = (now - session.current_run_start_at).total_seconds()
        session.total_work_seconds += int(run_time)
        session.current_run_start_at = None
    
    if session.current_pause_start_at:
        pause_time = (now - session.current_pause_start_at).total_seconds()
        session.total_pause_seconds += int(pause_time)
        session.current_pause_start_at = None
    
    session.status = "stopped"
    session.stopped_at = now
    session.updated_at = now
    session.updated_by = current_user.id
    if payload and payload.sqft_templated is not None:
        session.sqft_templated = payload.sqft_templated
    if payload and payload.sqft_not_templated is not None:
        session.sqft_not_templated = payload.sqft_not_templated
    
    await db.commit()
    await db.refresh(session)
    
    # Create event
    event = TemplaterJobTimerEvent(
        session_id=session.id,
        job_id=job_id,
        fab_id=session.fab_id,
        templater_id=templater_id,
        action="stop",
        event_at=now,
        note=payload.note if payload else None,
    )
    db.add(event)
    await db.commit()
    
    return success_response(
        _serialize_templater_job_timer_session(session),
        "Templater timer stopped"
    )


@router.get("/templater/jobs/{job_id}/timer", response_model=SuccessResponse[dict])
async def get_templater_job_timer_state(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current templater timer state for a job"""
    
    # Get latest session
    result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
        )
        .order_by(TemplaterJobTimerSession.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    
    # Calculate total time
    total_seconds = 0
    sessions_result = await db.execute(
        select(func.coalesce(func.sum(TemplaterJobTimerSession.total_work_seconds), 0)).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
        )
    )
    total_seconds = sessions_result.scalar()
    
    # Add current running time
    if latest and latest.status == "running" and latest.current_run_start_at:
        run_time = (datetime.now() - latest.current_run_start_at).total_seconds()
        total_seconds += int(run_time)
    
    total_hours = total_seconds / 3600.0
    
    return success_response(
        {
            "job_id": job_id,
            "templater_id": templater_id,
            "fab_id": fab_id,
            "session": _serialize_templater_job_timer_session(latest) if latest else None,
            "total_actual_seconds": int(total_seconds),
            "total_actual_hours": round(total_hours, 2),
        },
        "Templater timer state retrieved"
    )


@router.get("/templater/jobs/{job_id}/timer/history", response_model=SuccessResponse[dict])
async def get_templater_job_timer_history(
    job_id: int,
    templater_id: int = Query(..., gt=0, description="Templater user ID"),
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timer history for a templater on a job"""
    
    # Get all sessions
    sessions_result = await db.execute(
        select(TemplaterJobTimerSession).where(
            TemplaterJobTimerSession.job_id == job_id,
            TemplaterJobTimerSession.templater_id == templater_id,
        )
        .order_by(TemplaterJobTimerSession.created_at)
    )
    sessions = sessions_result.scalars().all()
    
    # Get all events
    events_result = await db.execute(
        select(TemplaterJobTimerEvent).where(
            TemplaterJobTimerEvent.job_id == job_id,
            TemplaterJobTimerEvent.templater_id == templater_id,
        )
        .order_by(TemplaterJobTimerEvent.event_at)
    )
    events = events_result.scalars().all()
    
    return success_response(
        {
            "job_id": job_id,
            "templater_id": templater_id,
            "fab_id": fab_id,
            "sessions": [_serialize_templater_job_timer_session(s) for s in sessions],
            "events": [_serialize_templater_job_timer_event(e) for e in events],
        },
        "Templater timer history retrieved"
    )
