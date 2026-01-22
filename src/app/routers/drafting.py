from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status
from sqlalchemy import select
import logging
from datetime import datetime, timedelta

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.drafting import Drafting
from src.app.database.pre_draft_review import PreDraftReview
from src.app.database.drafting import DraftingSession, DraftingSessionNote
from src.app.interface.business_schemas import (
    DraftingCreate,
    DraftingUpdate,
    DraftingSubmitUpdate,
    DraftingResponse,
    PreDraftReviewCreate,
    PreDraftReviewUpdate,
    PreDraftReviewResponse,
    DraftingSessionAction,
    DraftingSessionResponse,
    DraftingSessionNoteResponse,
    DraftingSessionHistoryResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response, strip_timezone, utc_now, datetime_to_iso

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ DRAFTING SESSION ENDPOINTS ============

@router.post("/drafting/{fab_id}/session", response_model=SuccessResponse[DraftingSessionResponse])
async def manage_drafting_session(
    fab_id: int,
    session_data: DraftingSessionAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manage drafting session: start, pause, resume, on_hold, or end
    """
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Validate drafter exists
    drafter_result = await db.execute(select(User).where(User.id == session_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)
    
    action = session_data.action.lower()
    timestamp = session_data.timestamp or utc_now()
    
    # Get active session for this fab
    active_session_result = await db.execute(
        select(DraftingSession)
        .where(DraftingSession.fab_id == fab_id)
        .where(DraftingSession.status.in_(["drafting", "paused", "on_hold"]))
        .order_by(DraftingSession.created_at.desc())
    )
    active_session = active_session_result.scalar_one_or_none()
    
    if action == "start":
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active session already exists for this fab"
            )
        
        # Create new session
        session = DraftingSession(
            fab_id=fab_id,
            drafter_id=session_data.drafter_id,
            status="drafting",
            session_start_time=session_data.session_start_time or timestamp,
            cumulative_sqft_drafted=session_data.sqft_drafted or "0",
            work_percentage_done=session_data.work_percentage_done or 0,
            created_at=utc_now()
        )
        db.add(session)
        await db.flush()
        
        # Create session note
        note = DraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="start",
            timestamp=timestamp,
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=utc_now()
        )
        db.add(note)
        
        message = "Drafting session started"
    
    elif action == "pause":
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to pause"
            )
        if active_session.status != "drafting":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already {active_session.status}"
            )
        
        # Update time spent before pausing
        if active_session.current_pause_start_time is None:
            # Calculate time since last resume or start
            active_session.total_time_spent += int((timestamp - active_session.session_start_time).total_seconds()) - active_session.total_pause_duration
        
        active_session.status = "paused"
        active_session.current_pause_start_time = timestamp
        active_session.updated_at = utc_now()
        
        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done
        
        session = active_session
        
        # Create session note
        note = DraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="pause",
            timestamp=timestamp,
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=utc_now()
        )
        db.add(note)
        
        message = "Drafting session paused"
    
    elif action == "resume":
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session found to resume"
            )
        if active_session.status not in ["paused", "on_hold"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not paused or on hold"
            )
        
        # Calculate pause duration
        if active_session.current_pause_start_time:
            pause_duration = int((timestamp - active_session.current_pause_start_time).total_seconds())
            active_session.total_pause_duration += pause_duration
        
        active_session.status = "drafting"
        active_session.current_pause_start_time = None
        active_session.updated_at = utc_now()
        
        session = active_session
        
        # Create session note
        note = DraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="resume",
            timestamp=timestamp,
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=utc_now()
        )
        db.add(note)
        
        message = "Drafting session resumed"
    
    elif action == "on_hold":
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to put on hold"
            )
        
        # Similar to pause but with different status
        if active_session.current_pause_start_time is None and active_session.status == "drafting":
            active_session.current_pause_start_time = timestamp
        
        active_session.status = "on_hold"
        active_session.updated_at = utc_now()
        
        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done
        
        session = active_session
        
        # Create session note
        note = DraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="on_hold",
            timestamp=timestamp,
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=utc_now()
        )
        db.add(note)
        
        message = "Drafting session put on hold"
    
    elif action == "end":
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session found to end"
            )
        
        # Calculate final time
        end_time = session_data.session_end_time or timestamp
        
        if active_session.current_pause_start_time:
            # Was paused, add pause duration
            pause_duration = int((end_time - active_session.current_pause_start_time).total_seconds())
            active_session.total_pause_duration += pause_duration
        
        total_elapsed = int((end_time - active_session.session_start_time).total_seconds())
        active_session.total_time_spent = total_elapsed - active_session.total_pause_duration
        
        active_session.status = "completed"
        active_session.session_end_time = end_time
        active_session.current_pause_start_time = None
        active_session.updated_at = utc_now()
        
        if session_data.sqft_drafted:
            active_session.cumulative_sqft_drafted = session_data.sqft_drafted
        if session_data.work_percentage_done is not None:
            active_session.work_percentage_done = session_data.work_percentage_done
        
        session = active_session
        
        # Create session note
        note = DraftingSessionNote(
            session_id=session.id,
            fab_id=fab_id,
            action="end",
            timestamp=timestamp,
            note=session_data.note,
            sqft_drafted=session_data.sqft_drafted,
            work_percentage_done=session_data.work_percentage_done,
            created_at=utc_now()
        )
        db.add(note)
        
        message = f"Drafting session ended. Total time: {active_session.total_time_spent} seconds"
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Must be 'start', 'pause', 'resume', 'on_hold', or 'end'"
        )
    
    await db.commit()
    await db.refresh(session)
    
    # Fetch notes for response
    notes_result = await db.execute(
        select(DraftingSessionNote)
        .where(DraftingSessionNote.session_id == session.id)
        .order_by(DraftingSessionNote.timestamp.asc())
    )
    notes = notes_result.scalars().all()
    
    response_data = DraftingSessionResponse(
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
            DraftingSessionNoteResponse(
                timestamp=n.timestamp,
                action=n.action,
                note=n.note,
                sqft_drafted=n.sqft_drafted,
                work_percentage_done=n.work_percentage_done
            ) for n in notes
        ]
    )
    
    return success_response(response_data, message)


@router.get("/drafting/{fab_id}/session", response_model=SuccessResponse[DraftingSessionResponse])
async def get_current_drafting_session(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current active drafting session for a fab
    """
    # Get active or most recent session
    session_result = await db.execute(
        select(DraftingSession)
        .where(DraftingSession.fab_id == fab_id)
        .order_by(DraftingSession.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise error_response("No drafting session found for this fab", 404)
    
    # Fetch notes
    notes_result = await db.execute(
        select(DraftingSessionNote)
        .where(DraftingSessionNote.session_id == session.id)
        .order_by(DraftingSessionNote.timestamp.asc())
    )
    notes = notes_result.scalars().all()
    
    # Calculate current time spent if session is active
    total_time = session.total_time_spent
    if session.status == "drafting":
        # Session is active, calculate current elapsed time
        current_elapsed = int((utc_now() - session.session_start_time).total_seconds())
        total_time = current_elapsed - session.total_pause_duration
    
    # Get last action time from notes
    last_action_time = notes[-1].timestamp if notes else session.session_start_time
    
    response_data = DraftingSessionResponse(
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
            DraftingSessionNoteResponse(
                timestamp=n.timestamp,
                action=n.action,
                note=n.note,
                sqft_drafted=n.sqft_drafted,
                work_percentage_done=n.work_percentage_done
            ) for n in notes
        ]
    )
    
    return success_response(response_data, "Drafting session fetched successfully")


@router.get("/drafting/{fab_id}/session/history", response_model=SuccessResponse[DraftingSessionHistoryResponse])
async def get_drafting_session_history(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all drafting sessions history for a fab
    """
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)
    
    # Get all sessions for this fab
    sessions_result = await db.execute(
        select(DraftingSession)
        .where(DraftingSession.fab_id == fab_id)
        .order_by(DraftingSession.created_at.desc())
    )
    sessions = sessions_result.scalars().all()
    
    session_responses = []
    for session in sessions:
        # Fetch notes for each session
        notes_result = await db.execute(
            select(DraftingSessionNote)
            .where(DraftingSessionNote.session_id == session.id)
            .order_by(DraftingSessionNote.timestamp.asc())
        )
        notes = notes_result.scalars().all()
        
        last_action_time = notes[-1].timestamp if notes else session.session_start_time
        
        session_responses.append(
            DraftingSessionResponse(
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
                    DraftingSessionNoteResponse(
                        timestamp=n.timestamp,
                        action=n.action,
                        note=n.note,
                        sqft_drafted=n.sqft_drafted,
                        work_percentage_done=n.work_percentage_done
                    ) for n in notes
                ]
            )
        )
    
    response_data = DraftingSessionHistoryResponse(
        fab_id=fab_id,
        sessions=session_responses,
        total_sessions=len(session_responses)
    )
    
    return success_response(response_data, f"Found {len(session_responses)} drafting sessions")


# ============ DRAFTING ENDPOINTS ============

from pydantic import BaseModel
from typing import List

# Add this new schema for bulk drafting creation
class DraftingCreateBulk(BaseModel):
    fab_ids: List[int]
    drafter_id: int
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    total_sqft_required_to_draft: float

@router.post("/drafting", response_model=SuccessResponse[List[DraftingResponse]], status_code=201)
async def create_drafting(
    drafting_data: DraftingCreateBulk,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create drafting entries for multiple fabs"""
    
    # Validate drafter exists
    drafter_result = await db.execute(select(User).where(User.id == drafting_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)
    
    # Validate all fabs exist
    fabs_result = await db.execute(select(Fab).where(Fab.id.in_(drafting_data.fab_ids)))
    fabs = fabs_result.scalars().all()
    
    if len(fabs) != len(drafting_data.fab_ids):
        raise error_response("One or more fab IDs not found", 404)
    
    # Create drafting entries for all fabs
    drafting_entries = []
    for fab_id in drafting_data.fab_ids:
        drafting = Drafting(
            fab_id=fab_id,
            drafter_id=drafting_data.drafter_id,
            scheduled_start_date=strip_timezone(drafting_data.scheduled_start_date),
            scheduled_end_date=strip_timezone(drafting_data.scheduled_end_date),
            total_sqft_required_to_draft=str(drafting_data.total_sqft_required_to_draft),  # Convert to string
            drafter_start_date=None,
            drafter_end_date=None,
            total_sqft_drafted=None,
            no_of_piece_drafted=None,
            total_hours_drafted=None,
            draft_note=None,
            mentions=None,
            file_ids=None,
            is_redrafting=False,
            status_id=1,
            created_at=utc_now(),
            updated_at=None,
            updated_by=None
        )
        drafting_entries.append(drafting)
        db.add(drafting)
    
    await db.commit()
    
    # Refresh all entries
    for drafting in drafting_entries:
        await db.refresh(drafting)
    
    return success_response(drafting_entries, f"Drafting created successfully for {len(drafting_entries)} fabs")


@router.put("/drafting/{drafting_id}", response_model=SuccessResponse[DraftingResponse])
async def update_drafting(
    drafting_id: int,
    drafting_data: DraftingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update drafting entry"""
    
    # Fetch drafting AND fab in one query using join
    result = await db.execute(
        select(Drafting, Fab)
        .join(Fab, Drafting.fab_id == Fab.id)
        .where(Drafting.id == drafting_id)
    )
    row = result.first()
    
    if not row:
        raise error_response("Drafting not found", 404)
    
    drafting, fab = row
    
    # Get update data
    update_data = drafting_data.model_dump(exclude_unset=True)
    
    is_complete = update_data.get('is_completed', False)
    
    # Map frontend fields to database fields
    field_mapping = {
        'total_sqft': 'total_sqft_drafted',
        'no_of_pieces': 'no_of_piece_drafted',
        'notes': 'draft_note',
        'total_sqft_drafted': 'total_sqft_drafted',
        'no_of_piece_drafted': 'no_of_piece_drafted',
        'draft_note': 'draft_note',
        'mentions': 'mentions',
        'drafter_start_date': 'drafter_start_date',
        'drafter_end_date': 'drafter_end_date',
    }
    
    for field, value in update_data.items():
        if field in ['is_complete', 'is_completed']:
            continue
            
        db_field = field_mapping.get(field, field)
        
        if hasattr(drafting, db_field):
            setattr(drafting, db_field, value)
    
    # Handle completion
    if is_complete:
        drafting.status_id = 3
        
        # Only set drafter_end_date to now if not provided in request
        if 'drafter_end_date' not in update_data:
            drafting.drafter_end_date = utc_now()
        
        # IMPORTANT: Add fab to session explicitly
        db.add(fab)
        
        # Update fab stages and mark draft as completed
        fab.current_stage = fab.next_stage
        fab.draft_completed = True
        fab.draft_completed_date = utc_now()  # NEW - Add completion timestamp
        fab.updated_at = utc_now()
        fab.updated_by = current_user.id
    
    drafting.updated_at = utc_now()
    drafting.updated_by = current_user.id
    
    await db.commit()
    
    await db.refresh(drafting)
    
    # Also refresh fab to ensure we have latest state
    await db.refresh(fab)
    
    return success_response(drafting, "Drafting updated successfully")


@router.post("/drafting/{drafting_id}/submit", response_model=SuccessResponse[DraftingResponse])
async def submit_draft_for_review(
    drafting_id: int,
    total_sqft_drafted: float = Form(...),
    no_of_piece_drafted: int = Form(...),
    is_drafting_completed: bool = Form(False),
    draft_note: Optional[str] = Form(None),
    mentions: Optional[str] = Form(None, description="Comma-separated list of user IDs to notify"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit draft for review using form data.
    Includes: Total sqft done, Number of pieces drafted, draft notes, 
    is drafting completed, mentions (people to notify about this submission)
    """
    
    result = await db.execute(select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    # Update drafting with submission data
    drafting.total_sqft_drafted = total_sqft_drafted
    drafting.no_of_piece_drafted = no_of_piece_drafted
    drafting.draft_note = draft_note
    drafting.mentions = mentions
    
    if is_drafting_completed:
        drafting.status_id = 3  # Completed status
        drafting.drafter_end_date = utc_now()
        
        # Update fab stage to next step
        fab_result = await db.execute(select(Fab).where(Fab.id == drafting.fab_id))
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "sales_check"  # Move to sales check after drafting
            fab.next_stage = "cut_list"  # Next will be cut_list (or revision if needed)
            fab.updated_at = utc_now()
            fab.updated_by = current_user.id
    
    drafting.updated_at = utc_now()
    drafting.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(drafting)
    
    return success_response(drafting, "Draft submitted for review successfully")


@router.get("/drafting/{drafting_id}", response_model=SuccessResponse[DraftingResponse])
async def get_drafting(
    drafting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get drafting details by ID"""
    
    result = await db.execute(select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    return success_response(drafting, "Drafting fetched successfully")


@router.get("/drafting/fab/{fab_id}", response_model=SuccessResponse[DraftingResponse])
async def get_drafting_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get drafting details by fab ID"""
    
    result = await db.execute(select(Drafting).where(Drafting.fab_id == fab_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found for this fab", 404)
    
    return success_response(drafting, "Drafting fetched successfully")


@router.post("/drafting/{drafting_id}/add-file", response_model=SuccessResponse[None])
async def add_file_to_drafting(
    drafting_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add file to drafting section"""
    
    result = await db.execute(select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    # Add file ID to comma-separated list
    if drafting.file_ids:
        file_ids_list = drafting.file_ids.split(',')
        if str(file_id) not in file_ids_list:
            file_ids_list.append(str(file_id))
            drafting.file_ids = ','.join(file_ids_list)
    else:
        drafting.file_ids = str(file_id)
    
    drafting.updated_at = utc_now()
    drafting.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "File added to drafting successfully")


@router.delete("/drafting/{drafting_id}/file/{file_id}", response_model=SuccessResponse[None])
async def delete_file_from_drafting(
    drafting_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file from drafting section"""
    
    result = await db.execute(select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    # Remove file ID from comma-separated list
    if drafting.file_ids:
        file_ids_list = drafting.file_ids.split(',')
        if str(file_id) in file_ids_list:
            file_ids_list.remove(str(file_id))
            drafting.file_ids = ','.join(file_ids_list) if file_ids_list else None
    
    drafting.updated_at = utc_now()
    drafting.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "File removed from drafting successfully")


# ============ PRE-DRAFT REVIEW ENDPOINTS ============

@router.post("/pre-draft-review", response_model=SuccessResponse[PreDraftReviewResponse], status_code=201)
async def create_pre_draft_review(
    review_data: PreDraftReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a pre-draft review entry"""
    
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == review_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Handle draft_notes - keep as string or convert to empty string
    draft_notes_value = ""
    if review_data.draft_notes:
        if isinstance(review_data.draft_notes, str):
            draft_notes_value = review_data.draft_notes
        elif isinstance(review_data.draft_notes, int):
            draft_notes_value = str(review_data.draft_notes)
    
    # Create pre-draft review
    review = PreDraftReview(
        fab_id=review_data.fab_id,
        draft_notes=draft_notes_value,  # Now stores as string
        is_redrafting_needed=1 if not review_data.is_completed else 0,
        is_completed=review_data.is_completed if hasattr(review_data, 'is_completed') else False,
        status_id=1,
        created_at=utc_now(),
        updated_at=utc_now(),
        updated_by=current_user.id
    )
    
    db.add(review)
    
    # If review is completed, move fab to next stage
    if review_data.is_completed:
        db.add(fab)
        fab.current_stage = "drafting"
        fab.next_stage = "sales_ct"
        fab.updated_at = utc_now()
        fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(review)
    
    return success_response(review, "Pre-draft review created successfully")


@router.post("/pre-draft-review/{review_id}/complete", response_model=SuccessResponse[None])
async def mark_predraft_review_completed(
    review_id: int,
    is_completed: bool = True,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark pre-draft review as completed or not, which auto sets the fab to drafting status.
    Takes fab_id and notes (optional)
    """
    
    result = await db.execute(select(PreDraftReview).where(PreDraftReview.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise error_response("Pre-draft review not found", 404)
    
    # Get the fab
    fab_result = await db.execute(select(Fab).where(Fab.id == review.fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if not fab:
        raise error_response("Associated fab not found", 404)
    
    if is_completed:
        review.is_redrafting_needed = 0
        review.status_id = 2  # Completed status
        
        # Move fab to drafting stage
        fab.current_stage = "drafting"
        fab.next_stage = "sales_check"
        fab.updated_at = utc_now()
        fab.updated_by = current_user.id
        fab.predraft_completed_date = utc_now()
    
    if notes:
        review.draft_notes = notes  # Store as string
    
    review.updated_at = utc_now()
    review.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Pre-draft review marked as completed and fab moved to drafting")


@router.post("/pre-draft-review/{review_id}/set-redraft", response_model=SuccessResponse[None])
async def set_predraft_to_redraft(
    review_id: int,
    redraft_notes: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set pre-draft review to redraft and add redraft notes.
    This triggers a template redrafting.
    """
    
    result = await db.execute(select(PreDraftReview).where(PreDraftReview.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise error_response("Pre-draft review not found", 404)
    
    # Mark as needs redrafting
    review.is_redrafting_needed = 1
    review.draft_notes = redraft_notes  # Store as string
    review.updated_at = utc_now()
    review.updated_by = current_user.id
    
    # Get the fab and move back to templating stage
    fab_result = await db.execute(select(Fab).where(Fab.id == review.fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if fab:
        fab.current_stage = "templating"
        fab.next_stage = "pre_draft_review"
        fab.updated_at = utc_now()
        fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Pre-draft review set to redraft successfully")


@router.get("/pre-draft-review/fab/{fab_id}", response_model=SuccessResponse[PreDraftReviewResponse])
async def get_predraft_review_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pre-draft review by fab ID"""
    
    result = await db.execute(select(PreDraftReview).where(PreDraftReview.fab_id == fab_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise error_response("Pre-draft review not found for this fab", 404)
    
    return success_response(review, "Pre-draft review fetched successfully")
