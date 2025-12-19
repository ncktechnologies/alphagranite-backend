from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy import select
import logging

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.drafting import Drafting
from src.app.database.pre_draft_review import PreDraftReview
from src.app.interface.business_schemas import (
    DraftingCreate,
    DraftingUpdate,
    DraftingSubmitUpdate,
    DraftingResponse,
    PreDraftReviewCreate,
    PreDraftReviewUpdate,
    PreDraftReviewResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response, strip_timezone

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ DRAFTING ENDPOINTS ============

@router.post("/drafting", response_model=SuccessResponse[DraftingResponse], status_code=201)
async def create_drafting(
    drafting_data: DraftingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new drafting entry"""
    
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == drafting_data.fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)
    
    # Validate drafter exists
    drafter_result = await db.execute(select(User).where(User.id == drafting_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)
    
    # Create drafting
    drafting = Drafting(
        fab_id=drafting_data.fab_id,
        drafter_id=drafting_data.drafter_id,
        scheduled_start_date=strip_timezone(drafting_data.scheduled_start_date),
        scheduled_end_date=strip_timezone(drafting_data.scheduled_end_date),
        total_sqft_required_to_draft=drafting_data.total_sqft_required_to_draft,
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
        created_at=datetime.now(),
        updated_at=None,
        updated_by=None
    )
    
    db.add(drafting)
    await db.commit()
    await db.refresh(drafting)
    
    return success_response(drafting, "Drafting created successfully")


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
            drafting.drafter_end_date = datetime.now()
        
        # IMPORTANT: Add fab to session explicitly
        db.add(fab)
        
        # Update fab stages and mark draft as completed
        fab.current_stage = fab.next_stage
        fab.draft_completed = True
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    drafting.updated_at = datetime.now()
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
        drafting.drafter_end_date = datetime.now()
        
        # Update fab stage to next step
        fab_result = await db.execute(select(Fab).where(Fab.id == drafting.fab_id))
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "sales_check"  # Move to sales check after drafting
            fab.next_stage = "cut_list"  # Next will be cut_list (or revision if needed)
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id
    
    drafting.updated_at = datetime.now()
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
    
    drafting.updated_at = datetime.now()
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
    
    drafting.updated_at = datetime.now()
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
    
    # Handle draft_notes - convert to int or set to 0 if it's a text note
    # If draft_notes is numeric string, convert it; otherwise store 0
    draft_notes_value = 0
    if review_data.draft_notes:
        if isinstance(review_data.draft_notes, int):
            draft_notes_value = review_data.draft_notes
        elif isinstance(review_data.draft_notes, str):
            # Try to convert to int, if it fails, just use 0
            try:
                draft_notes_value = int(review_data.draft_notes)
            except ValueError:
                # If draft_notes contains text, you might want to store it elsewhere
                # For now, we'll just set it to 0
                draft_notes_value = 0
    
    # Create pre-draft review
    review = PreDraftReview(
        fab_id=review_data.fab_id,
        draft_notes=draft_notes_value,
        is_redrafting_needed=1 if not review_data.is_completed else 0,
        is_completed=review_data.is_completed if hasattr(review_data, 'is_completed') else False,
        status_id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        updated_by=current_user.id
    )
    
    db.add(review)
    
    # If review is completed, move fab to next stage
    if review_data.is_completed:
        db.add(fab)
        fab.current_stage = "drafting"
        fab.next_stage = "sales_ct"
        fab.updated_at = datetime.now()
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
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    if notes:
        review.draft_notes = int(notes) if notes.isdigit() else 0  # Model expects int
    
    review.updated_at = datetime.now()
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
    review.draft_notes = int(redraft_notes) if redraft_notes.isdigit() else 0
    review.updated_at = datetime.now()
    review.updated_by = current_user.id
    
    # Get the fab and move back to templating stage
    fab_result = await db.execute(select(Fab).where(Fab.id == review.fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if fab:
        fab.current_stage = "templating"
        fab.next_stage = "pre_draft_review"
        fab.updated_at = datetime.now()
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
