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
from src.app.interface.generated_schemas import InstallScheduling
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
from src.app.utils.timer_guards import assert_no_active_timer_session

router = APIRouter(
    prefix="/job-timers",
    tags=["Job Timers"],
)

INSTALLER_ROLE_LEAD = "lead"
INSTALLER_ROLE_EXTRA_CREW = "extra_crew"


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


async def _resolve_installer_role_for_fab(
    db: AsyncSession,
    fab_id: int,
    installer_id: int,
) -> str:
    result = await db.execute(
        select(InstallScheduling)
        .where(InstallScheduling.fab_id == fab_id)
        .order_by(InstallScheduling.id.desc())
        .limit(1)
    )
    install_scheduling = result.scalar_one_or_none()
    if not install_scheduling:
        raise error_response("Install Scheduling not found for this fab", 404)

    if installer_id == install_scheduling.installer_id:
        return INSTALLER_ROLE_LEAD

    if installer_id in {
        install_scheduling.extra_crew_1_id,
        install_scheduling.extra_crew_2_id,
        install_scheduling.extra_crew_3_id,
    }:
        return INSTALLER_ROLE_EXTRA_CREW

    raise error_response("Installer is not assigned to this fab install crew", 403)


def _payload_has_sqft(payload: Optional[InstallerJobTimerCommandRequest]) -> bool:
    return bool(
        payload
        and (
            payload.sqft_installed is not None
            or payload.sqft_not_installed is not None
        )
    )


def _enforce_lead_only_sqft(payload: Optional[InstallerJobTimerCommandRequest], installer_role: str) -> None:
    if installer_role != INSTALLER_ROLE_LEAD and _payload_has_sqft(payload):
        raise error_response(
            "Only lead installer can input sqft_installed or sqft_not_installed",
            403,
        )


async def _resolve_role_for_timer_session(
    db: AsyncSession,
    session: InstallerJobTimerSession,
    installer_id: int,
    requested_fab_id: Optional[int],
) -> str:
    if session.fab_id and requested_fab_id and session.fab_id != requested_fab_id:
        raise error_response("fab_id does not match the timer session fab_id", 400)

    resolved_fab_id = session.fab_id or requested_fab_id
    if not resolved_fab_id:
        # No FAB context means we cannot verify crew assignment; preserve existing role
        # (or default to lead for backward compatibility).
        return session.installer_role or INSTALLER_ROLE_LEAD

    installer_role = await _resolve_installer_role_for_fab(db, resolved_fab_id, installer_id)
    session.installer_role = installer_role
    return installer_role


def _serialize_installer_job_timer_session(session: InstallerJobTimerSession) -> dict:
    return {
        "id": session.id,
        "job_id": session.job_id,
        "fab_id": session.fab_id,
        "installer_id": session.installer_id,
        "installer_role": session.installer_role,
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
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an installer timer for a job"""
    installer_id = current_user.id
    
    # Verify job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        raise error_response("Job not found", 404)
    
    # Verify fab if provided
    installer_role = INSTALLER_ROLE_LEAD
    if fab_id:
        fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
        if not fab_result.scalar_one_or_none():
            raise error_response("Fab not found", 404)
        installer_role = await _resolve_installer_role_for_fab(db, fab_id, installer_id)

    _enforce_lead_only_sqft(payload, installer_role)
    
    # Check if there's already a running timer for this installer at this stage
    conflict_result = await db.execute(
        select(InstallerJobTimerSession, BusinessJob)
        .join(BusinessJob, BusinessJob.id == InstallerJobTimerSession.job_id)
        .where(
            InstallerJobTimerSession.installer_id == installer_id,
            InstallerJobTimerSession.job_id == job_id,
            InstallerJobTimerSession.status == "running",
        )
        .limit(1)
    )
    conflict_row = conflict_result.first()
    if conflict_row:
        conflict_session, conflict_job = conflict_row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Timer on Job #{conflict_job.job_number} and Fab_id {conflict_session.fab_id} is already running. Stop or pause it before starting another.",
        )

    # Create new session
    now = datetime.now()
    new_session = InstallerJobTimerSession(
        job_id=job_id,
        fab_id=fab_id,
        installer_id=installer_id,
        installer_role=installer_role,
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
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause an installer timer"""
    installer_id = current_user.id
    
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

    installer_role = await _resolve_role_for_timer_session(db, session, installer_id, fab_id)
    _enforce_lead_only_sqft(payload, installer_role)
    
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
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused installer timer"""
    installer_id = current_user.id
    
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

    installer_role = await _resolve_role_for_timer_session(db, session, installer_id, fab_id)
    _enforce_lead_only_sqft(payload, installer_role)
    
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
    payload: InstallerJobTimerCommandRequest = None,
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop an installer timer"""
    installer_id = current_user.id

    stop_query = select(InstallerJobTimerSession).where(
        InstallerJobTimerSession.job_id == job_id,
        InstallerJobTimerSession.installer_id == installer_id,
        InstallerJobTimerSession.status.in_(["running", "paused"]),
    )
    if fab_id is not None:
        stop_query = stop_query.where(InstallerJobTimerSession.fab_id == fab_id)

    # Defensive ordering ensures we stop only one concrete active session,
    # even if legacy data accidentally contains duplicates.
    stop_query = stop_query.order_by(InstallerJobTimerSession.created_at.desc()).limit(1)

    result = await db.execute(stop_query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise error_response("No active timer found for this installer and job", 404)

    installer_role = await _resolve_role_for_timer_session(db, session, installer_id, fab_id)
    _enforce_lead_only_sqft(payload, installer_role)
    
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
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current installer timer state for a job"""
    installer_id = current_user.id
    
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
    
    # Calculate total time from latest session only so each new session starts at zero.
    total_seconds = int(latest.total_work_seconds or 0) if latest else 0
    
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
    fab_id: Optional[int] = Query(None, description="Optional FAB ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timer history for an installer on a job"""
    installer_id = current_user.id
    
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
    
    # Check if there's already a running timer for this templater at this stage
    conflict_result = await db.execute(
        select(TemplaterJobTimerSession, BusinessJob)
        .join(BusinessJob, BusinessJob.id == TemplaterJobTimerSession.job_id)
        .where(
            TemplaterJobTimerSession.templater_id == templater_id,
            TemplaterJobTimerSession.status == "running",
        )
        .limit(1)
    )
    conflict_row = conflict_result.first()
    if conflict_row:
        conflict_session, conflict_job = conflict_row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Timer on Job #{conflict_job.job_number} and Fab_id {conflict_session.fab_id} is already running. Stop or pause it before starting another.",
        )

    # Prevent starting if any running timer exists across all session types
    if not getattr(current_user, "is_super_admin", False):
        await assert_no_active_timer_session(db, templater_id)

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
    
    # Calculate total time from latest session only so each new session starts at zero.
    total_seconds = int(latest.total_work_seconds or 0) if latest else 0
    
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

    # Resolve descriptive names
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    job = job_result.scalar_one_or_none()

    templater_result = await db.execute(select(User).where(User.id == templater_id))
    templater = templater_result.scalar_one_or_none()

    templater_name = None
    if templater is not None:
        templater_name = f"{(templater.first_name or '').strip()} {(templater.last_name or '').strip()}".strip()
        if not templater_name:
            templater_name = templater.username
    
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

    latest_session = sessions[-1] if sessions else None
    is_complete = bool(latest_session and latest_session.status == "stopped")
    
    return success_response(
        {
            "job_id": job_id,
            "job_name": job.name if job else None,
            "templater_id": templater_id,
            "templater_name": templater_name,
            "fab_id": fab_id,
            "is_complete": is_complete,
            "sessions": [_serialize_templater_job_timer_session(s) for s in sessions],
            "events": [_serialize_templater_job_timer_event(e) for e in events],
        },
        "Templater timer history retrieved"
    )
