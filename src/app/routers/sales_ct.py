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
    SalesCTReviewUpdate,
    SalesCTSendToDrafting,
    SalesCTApprove,
    FabResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter(
    prefix="/sales-ct",
    tags=["SalesCT"]
)


@router.patch("/{fab_id}/review", response_model=dict)
async def update_sct_review(
    fab_id: int,
    review_data: SalesCTReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sales CT: Mark SCT review as complete and update revenue
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Update SCT completion status
    fab.sct_completed = review_data.sct_completed
    
    # Update revenue if provided
    if review_data.revenue is not None:
        fab.revenue = float(review_data.revenue)
    
    # Update slab_smith_used if provided
    if review_data.slab_smith_used is not None:
        fab.slab_smith_used = review_data.slab_smith_used
    
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Add notes if provided
    if review_data.notes:
        fab_note = FabNotes(
            fab_id=fab_id,
            note=review_data.notes,
            stage="sales_ct",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
    
    # If SCT completed, check if SlabSmith is needed to determine next stage
    if review_data.sct_completed:
        fab.sct_completed_date = datetime.now()
        fab.current_stage = "cut_list"
        fab.next_stage = "final_programming"
    
    await db.commit()
    await db.refresh(fab)
    
    return {
        "success": True,
        "message": f"SCT review {'completed' if review_data.sct_completed else 'updated'} successfully",
        "data": {
            "fab_id": fab.id,
            "sct_completed": fab.sct_completed,
            "sct_completed_date": fab.sct_completed_date.isoformat() if fab.sct_completed_date else None,
            "revenue": fab.revenue,
            "slab_smith_used": fab.slab_smith_used,
            "slab_smith_ag_needed": fab.slab_smith_ag_needed,
            "current_stage": fab.current_stage,
            "next_stage": fab.next_stage
        }
    }


@router.post("/{fab_id}/send-to-drafting", response_model=dict)
async def send_to_drafting(
    fab_id: int,
    revision_data: SalesCTSendToDrafting,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sales CT: Send FAB back to drafting for revisions
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Mark as revised and send back to drafting
    fab.revised = True
    fab.sct_completed = False
    fab.current_stage = "revision"
    fab.next_stage = "sales_ct"  # After drafting, comes back to sales_ct
    fab.revision_completed_date = datetime.now()
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Add revision notes
    fab_note = FabNotes(
        fab_id=fab_id,
        note=f"[REVISION REQUEST] {revision_data.notes}",
        stage="sales_ct",
        created_by=current_user.id,
        created_at=datetime.now()
    )
    db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    return {
        "success": True,
        "message": "FAB sent back to drafting for revisions",
        "data": {
            "fab_id": fab.id,
            "revised": fab.revised,
            "current_stage": fab.current_stage,
            "next_stage": fab.next_stage,
            "revision_completed_date": fab.revision_completed_date.isoformat() if fab.revision_completed_date else None
        }
    }


@router.post("/{fab_id}/approve", response_model=dict)
async def approve_and_send_to_slabsmith(
    fab_id: int,
    approval_data: SalesCTApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sales CT: Approve FAB and send to next stage based on SlabSmith requirement
    """
    # Get FAB
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Mark SCT as completed
    fab.sct_completed = approval_data.sct_completed
    
    # Update revenue if provided
    if approval_data.revenue is not None:
        fab.revenue = float(approval_data.revenue)
    
    # Update slab_smith_used if provided
    if approval_data.slab_smith_used is not None:
        fab.slab_smith_used = approval_data.slab_smith_used
    
    # Check if SlabSmith is needed to determine next stage
    if fab.slab_smith_ag_needed:  # ← Check if SlabSmith is needed
        fab.current_stage = "slab_smith_request"
        fab.next_stage = "cut_list"
        message_suffix = "sent to SlabSmith"
    else:
        fab.current_stage = "cut_list"
        fab.next_stage = "final_programming"
        message_suffix = "sent to Cut List"
    
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Add approval notes if provided
    if approval_data.notes:
        fab_note = FabNotes(
            fab_id=fab_id,
            note=f"[APPROVED] {approval_data.notes}",
            stage="sales_ct",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    return {
        "success": True,
        "message": f"FAB approved and {message_suffix}",  # ← Dynamic message
        "data": {
            "fab_id": fab.id,
            "sct_completed": fab.sct_completed,
            "sct_completed_date": fab.sct_completed_date.isoformat() if fab.sct_completed_date else None,
            "revenue": fab.revenue,
            "slab_smith_used": fab.slab_smith_used,
            "slab_smith_ag_needed": fab.slab_smith_ag_needed,
            "current_stage": fab.current_stage,
            "next_stage": fab.next_stage
        }
    }


@router.get("/{fab_id}/revision-history", response_model=dict)
async def get_revision_history(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sales CT: Get revision history for a FAB
    """
    # Get FAB to verify it exists
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    # Get all notes related to revisions
    notes_result = await db.execute(
        select(FabNotes, User)
        .join(User, FabNotes.created_by == User.id)
        .where(FabNotes.fab_id == fab_id)
        .where(FabNotes.note.like("%REVISION%"))
        .order_by(FabNotes.created_at.desc())
    )
    
    revision_history = []
    for note, user in notes_result:
        revision_history.append({
            "id": note.id,
            "note": note.note,
            "stage": note.stage,
            "created_by": f"{user.first_name} {user.last_name}",
            "created_at": note.created_at.isoformat() if note.created_at else None
        })
    
    return {
        "success": True,
        "message": "Revision history retrieved successfully",
        "data": {
            "fab_id": fab.id,
            "revised": fab.revised,
            "revision_count": len(revision_history),
            "revisions": revision_history
        }
    }
