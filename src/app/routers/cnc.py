from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, File as FileUpload, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
import logging
from datetime import datetime, timezone

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.cnc import CNCDrafting, CNCDraftingSession, CNCDraftingSessionNote
from src.app.database.file import File
from src.app.interface.business_schemas import (
    CNCDraftingCreate,
    CNCDraftingUpdate,
    CNCDraftingSubmitUpdate,
    CNCDraftingResponse,
    CNCDraftingSessionAction,
    CNCDraftingSessionResponse,
    CNCDraftingSessionNoteResponse,
    CNCDraftingSessionHistoryResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.service.file import FileService
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response, strip_timezone, utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ CNC SESSION ENDPOINTS ============

@router.post("/CNC/{fab_id}/session", response_model=SuccessResponse[CNCDraftingSessionResponse])
async def manage_cnc_session(
    fab_id: int,
    session_data: CNCDraftingSessionAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manage CNC drafting session: start, pause, resume, on_hold, or end"""

    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)

    drafter_result = await db.execute(select(User).where(User.id == session_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)

    action = session_data.action.lower()
    timestamp = session_data.timestamp or strip_timezone(utc_now())

    # Get active session for this fab
    active_session_result = await db.execute(
        select(CNCDraftingSession)
        .where(CNCDraftingSession.fab_id == fab_id)
        .where(CNCDraftingSession.status.in_(["drafting", "paused", "on_hold"]))
        .order_by(CNCDraftingSession.created_at.desc())
        .limit(1)
    )
    active_session = active_session_result.scalars().first()

    if action == "start":
        is_revision = getattr(session_data, "is_revision", False)
        if active_session and not is_revision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active CNC session already exists for this fab. Complete it first or mark as revision.",
            )

        session = CNCDraftingSession(
            fab_id=fab_id,
            drafter_id=session_data.drafter_id,
            status="drafting",
            session_start_time=strip_timezone(session_data.session_start_time) if session_data.session_start_time else strip_timezone(timestamp),
            cumulative_sqft_drafted=session_data.sqft_drafted or "0",
            work_percentage_done=session_data.work_percentage_done or 0,
            created_at=strip_timezone(utc_now()),
        )
        db.add(session)
        await db.flush()

        note = CNCDraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="start",
            timestamp=strip_timezone(timestamp),
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=strip_timezone(utc_now()),
        )
        db.add(note)
        message = "CNC session started"

    elif action == "pause":
        if not active_session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active CNC session found to pause")
        if active_session.status != "drafting":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Session is already {active_session.status}")

        if active_session.current_pause_start_time is None:
            naive_ts = strip_timezone(timestamp)
            naive_start = strip_timezone(active_session.session_start_time)
            active_session.total_time_spent += int((naive_ts - naive_start).total_seconds()) - active_session.total_pause_duration

        active_session.status = "paused"
        active_session.current_pause_start_time = strip_timezone(timestamp)
        active_session.updated_at = strip_timezone(utc_now())

        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done

        session = active_session

        note = CNCDraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="pause",
            timestamp=strip_timezone(timestamp),
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=strip_timezone(utc_now()),
        )
        db.add(note)
        message = "CNC session paused"

    elif action == "resume":
        if not active_session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No CNC session found to resume")
        if active_session.status not in ["paused", "on_hold"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not paused or on hold")

        if active_session.current_pause_start_time:
            pause_start = strip_timezone(active_session.current_pause_start_time)
            if pause_start.tzinfo is None:
                pause_start = pause_start.replace(tzinfo=timezone.utc)
            ts = timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            active_session.total_pause_duration += int((ts - pause_start).total_seconds())

        active_session.status = "drafting"
        active_session.current_pause_start_time = None
        active_session.updated_at = strip_timezone(utc_now())

        session = active_session

        note = CNCDraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="resume",
            timestamp=strip_timezone(timestamp),
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=strip_timezone(utc_now()),
        )
        db.add(note)
        message = "CNC session resumed"

    elif action == "on_hold":
        if not active_session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active CNC session found to put on hold")

        if active_session.current_pause_start_time is None and active_session.status == "drafting":
            active_session.current_pause_start_time = strip_timezone(timestamp)

        active_session.status = "on_hold"
        active_session.updated_at = strip_timezone(utc_now())

        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done

        session = active_session

        note = CNCDraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="on_hold",
            timestamp=strip_timezone(timestamp),
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=strip_timezone(utc_now()),
        )
        db.add(note)
        message = "CNC session put on hold"

    elif action == "end":
        if not active_session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active CNC session found to end")

        end_time = session_data.session_end_time or timestamp

        if active_session.current_pause_start_time:
            pause_duration = int((end_time - strip_timezone(active_session.current_pause_start_time)).total_seconds())
            active_session.total_pause_duration += pause_duration

        total_elapsed = int((end_time - strip_timezone(active_session.session_start_time)).total_seconds())
        active_session.total_time_spent = total_elapsed - active_session.total_pause_duration

        active_session.status = "completed"
        active_session.session_end_time = end_time
        active_session.current_pause_start_time = None
        active_session.updated_at = strip_timezone(utc_now())

        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done

        session = active_session

        note = CNCDraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="end",
            timestamp=strip_timezone(timestamp),
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=strip_timezone(utc_now()),
        )
        db.add(note)
        message = f"CNC session ended. Total time: {active_session.total_time_spent} seconds"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Must be 'start', 'pause', 'resume', 'on_hold', or 'end'",
        )

    await db.commit()
    await db.refresh(session)

    notes_result = await db.execute(
        select(CNCDraftingSessionNote)
        .where(CNCDraftingSessionNote.session_id == session.id)
        .order_by(CNCDraftingSessionNote.timestamp.asc())
    )
    notes = notes_result.scalars().all()

    response_data = CNCDraftingSessionResponse(
        session_id=session.id,
        fab_id=session.fab_id,
        drafter_id=session.drafter_id,
        status=session.status,
        current_session_start_time=session.session_start_time,
        last_action_time=timestamp,
        total_time_spent=session.total_time_spent,
        cumulative_sqft_drafted=session.cumulative_sqft_drafted or "0",
        work_percentage_done=session.work_percentage_done,
        current_pause_start_time=session.current_pause_start_time,
        total_pause_duration=session.total_pause_duration,
        notes=[
            CNCDraftingSessionNoteResponse(
                timestamp=strip_timezone(n.timestamp),
                action=n.action,
                note=n.note,
                sqft_drafted=n.sqft_drafted,
                work_percentage_done=n.work_percentage_done,
            )
            for n in notes
        ],
    )

    return success_response(response_data, message)


@router.get("/CNC/{fab_id}/session", response_model=SuccessResponse[CNCDraftingSessionResponse])
async def get_current_cnc_session(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current active CNC drafting session for a fab"""

    session_result = await db.execute(
        select(CNCDraftingSession)
        .where(CNCDraftingSession.fab_id == fab_id)
        .order_by(CNCDraftingSession.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise error_response("No CNC session found for this fab", 404)

    notes_result = await db.execute(
        select(CNCDraftingSessionNote)
        .where(CNCDraftingSessionNote.session_id == session.id)
        .order_by(CNCDraftingSessionNote.timestamp.asc())
    )
    notes = notes_result.scalars().all()

    total_time = session.total_time_spent
    if session.status == "drafting":
        current_elapsed = int((utc_now() - session.session_start_time).total_seconds())
        total_time = current_elapsed - session.total_pause_duration

    last_action_time = notes[-1].timestamp if notes else session.session_start_time

    response_data = CNCDraftingSessionResponse(
        session_id=session.id,
        fab_id=session.fab_id,
        drafter_id=session.drafter_id,
        status=session.status,
        current_session_start_time=session.session_start_time,
        last_action_time=last_action_time,
        total_time_spent=total_time,
        cumulative_sqft_drafted=session.cumulative_sqft_drafted or "0",
        work_percentage_done=session.work_percentage_done,
        current_pause_start_time=session.current_pause_start_time,
        total_pause_duration=session.total_pause_duration,
        notes=[
            CNCDraftingSessionNoteResponse(
                timestamp=strip_timezone(n.timestamp),
                action=n.action,
                note=n.note,
                sqft_drafted=n.sqft_drafted,
                work_percentage_done=n.work_percentage_done,
            )
            for n in notes
        ],
    )

    return success_response(response_data, "CNC session fetched successfully")


@router.get("/CNC/{fab_id}/session/history", response_model=SuccessResponse[CNCDraftingSessionHistoryResponse])
async def get_cnc_session_history(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all CNC session history for a fab"""

    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)

    sessions_result = await db.execute(
        select(CNCDraftingSession)
        .where(CNCDraftingSession.fab_id == fab_id)
        .order_by(CNCDraftingSession.created_at.desc())
    )
    sessions = sessions_result.scalars().all()

    session_responses = []
    for session in sessions:
        notes_result = await db.execute(
            select(CNCDraftingSessionNote)
            .where(CNCDraftingSessionNote.session_id == session.id)
            .order_by(CNCDraftingSessionNote.timestamp.asc())
        )
        notes = notes_result.scalars().all()

        last_action_time = notes[-1].timestamp if notes else session.session_start_time

        session_responses.append(
            CNCDraftingSessionResponse(
                session_id=session.id,
                fab_id=session.fab_id,
                drafter_id=session.drafter_id,
                status=session.status,
                current_session_start_time=session.session_start_time,
                last_action_time=last_action_time,
                total_time_spent=session.total_time_spent,
                cumulative_sqft_drafted=session.cumulative_sqft_drafted or "0",
                work_percentage_done=session.work_percentage_done,
                current_pause_start_time=session.current_pause_start_time,
                total_pause_duration=session.total_pause_duration,
                notes=[
                    CNCDraftingSessionNoteResponse(
                        timestamp=strip_timezone(n.timestamp),
                        action=n.action,
                        note=n.note,
                        sqft_drafted=n.sqft_drafted,
                        work_percentage_done=n.work_percentage_done,
                    )
                    for n in notes
                ],
            )
        )

    response_data = CNCDraftingSessionHistoryResponse(
        fab_id=fab_id,
        sessions=session_responses,
        total_sessions=len(session_responses),
    )

    return success_response(response_data, f"Found {len(session_responses)} CNC sessions")


# ============ CNC DRAFTING CRUD ENDPOINTS ============

@router.post("/CNC", response_model=SuccessResponse[List[CNCDraftingResponse]], status_code=201)
async def create_cnc_drafting(
    drafting_data: CNCDraftingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create CNC drafting entries for multiple fabs"""

    drafter_result = await db.execute(select(User).where(User.id == drafting_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)

    fab_ids = [item.fab_id for item in drafting_data.items]
    fabs_result = await db.execute(select(Fab).where(Fab.id.in_(fab_ids)))
    fabs = fabs_result.scalars().all()

    if len(fabs) != len(fab_ids):
        raise error_response("One or more fab IDs not found", 404)

    entries = []
    for item in drafting_data.items:
        cnc = CNCDrafting(
            fab_id=item.fab_id,
            drafter_id=drafting_data.drafter_id,
            scheduled_start_date=strip_timezone(item.scheduled_start_date),
            scheduled_end_date=strip_timezone(item.scheduled_end_date),
            total_sqft_required_to_draft=str(item.total_sqft_required_to_draft),
            status_id=1,
            is_completed=False,
            created_at=strip_timezone(utc_now()),
        )
        entries.append(cnc)
        db.add(cnc)

    await db.commit()

    for cnc in entries:
        await db.refresh(cnc)

    return success_response(entries, f"CNC drafting created successfully for {len(entries)} fabs")


@router.put("/CNC/{cnc_id}", response_model=SuccessResponse[CNCDraftingResponse])
async def update_cnc_drafting(
    cnc_id: int,
    drafting_data: CNCDraftingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update CNC drafting entry"""

    result = await db.execute(
        select(CNCDrafting, Fab)
        .join(Fab, CNCDrafting.fab_id == Fab.id)
        .where(CNCDrafting.id == cnc_id)
    )
    row = result.first()

    if not row:
        raise error_response("CNC drafting not found", 404)

    cnc, fab = row

    update_data = drafting_data.model_dump(exclude_unset=True)
    is_complete = update_data.get("is_completed", False)

    field_mapping = {
        "total_sqft": "total_sqft",
        "no_of_pieces": "no_of_pieces",
        "notes": "notes",
        "cad_review_complete": "cad_review_complete",
        "draft_completed": "draft_completed",
        "current_stage": "current_stage",
        "drafter_start_date": "drafter_start_date",
        "drafter_end_date": "drafter_end_date",
        "total_sqft_drafted": "total_sqft_drafted",
        "no_of_piece_drafted": "no_of_piece_drafted",
        "draft_note": "draft_note",
        "mentions": "mentions",
        "total_hours_drafted": "total_hours_drafted",
        "status_id": "status_id",
    }

    for field, value in update_data.items():
        if field == "is_completed":
            continue
        db_field = field_mapping.get(field, field)
        if hasattr(cnc, db_field):
            setattr(cnc, db_field, value)

    if is_complete:
        cnc.is_completed = True
        cnc.status_id = 3
        if "drafter_end_date" not in update_data:
            cnc.drafter_end_date = strip_timezone(utc_now())

    cnc.updated_at = strip_timezone(utc_now())
    cnc.updated_by = current_user.id

    await db.commit()
    await db.refresh(cnc)

    return success_response(cnc, "CNC drafting updated successfully")


@router.post("/CNC/{fab_id}/submit", response_model=SuccessResponse[CNCDraftingResponse])
async def submit_cnc_draft(
    fab_id: int,
    submit_data: CNCDraftingSubmitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit CNC draft for review"""

    result = await db.execute(
        select(CNCDrafting)
        .where(CNCDrafting.fab_id == fab_id)
        .order_by(CNCDrafting.created_at.desc())
        .limit(1)
    )
    cnc = result.scalar_one_or_none()

    if not cnc:
        raise error_response("CNC drafting not found for this fab", 404)

    if submit_data.total_sqft is not None:
        cnc.total_sqft_drafted = submit_data.total_sqft
    if submit_data.no_of_piece is not None:
        cnc.no_of_piece_drafted = submit_data.no_of_piece
    if submit_data.note is not None:
        cnc.draft_note = submit_data.note
    if submit_data.mentions is not None:
        cnc.mentions = submit_data.mentions

    if submit_data.is_completed:
        cnc.is_completed = True
        cnc.status_id = 3
        cnc.drafter_end_date = strip_timezone(utc_now())

    cnc.updated_at = strip_timezone(utc_now())
    cnc.updated_by = current_user.id

    await db.commit()
    await db.refresh(cnc)

    return success_response(cnc, "CNC draft submitted successfully")


@router.get("/CNC/fab/{fab_id}", response_model=SuccessResponse[CNCDraftingResponse])
async def get_cnc_drafting_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent CNC drafting entry by fab ID"""

    result = await db.execute(
        select(CNCDrafting)
        .where(CNCDrafting.fab_id == fab_id)
        .order_by(CNCDrafting.created_at.desc())
        .limit(1)
    )
    cnc = result.scalar_one_or_none()

    if not cnc:
        raise error_response("CNC drafting not found for this fab", 404)

    return success_response(cnc, "CNC drafting fetched successfully")


@router.post("/CNC/{cnc_id}/add-file", response_model=SuccessResponse[None])
async def add_file_to_cnc_drafting(
    cnc_id: int,
    request: Request,
    file: UploadFile = FileUpload(...),
    file_design: Optional[str] = Form(None),
    stage_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file and attach it to a CNC drafting entry"""

    result = await db.execute(select(CNCDrafting).where(CNCDrafting.id == cnc_id))
    cnc = result.scalar_one_or_none()

    if not cnc:
        raise error_response("CNC drafting not found", 404)

    file_data = await FileService.upload_file(
        db=db,
        file=file,
        user_id=current_user.id,
        directory="uploads",
        file_design=file_design,
        stage_name=stage_name,
        fab_id=cnc.fab_id,
        request=request,
    )
    file_id = file_data["id"]

    if cnc.file_ids:
        file_ids_list = cnc.file_ids.split(",")
        if str(file_id) not in file_ids_list:
            file_ids_list.append(str(file_id))
            cnc.file_ids = ",".join(file_ids_list)
    else:
        cnc.file_ids = str(file_id)

    cnc.updated_at = strip_timezone(utc_now())
    cnc.updated_by = current_user.id

    await db.commit()

    return success_response(
        {"file_id": file_id, "file_design": file_design, "stage_name": stage_name},
        "File added to CNC drafting successfully",
    )
