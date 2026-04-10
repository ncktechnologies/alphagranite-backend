from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.cnc import CNCDrafting
from src.app.database.fab_notes import FabNotes
from src.app.database.user import User
from src.app.interface.business_schemas import (
    CutListScheduleUpdate,
    CutListUpdate,
    FabResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter(
    prefix="/cut-list",
    tags=["Cut List"]
)


async def _has_completed_cnc_submission(
    db: AsyncSession,
    fab_id: int,
) -> bool:
    latest_cnc_result = await db.execute(
        select(CNCDrafting)
        .where(CNCDrafting.fab_id == fab_id)
        .order_by(CNCDrafting.created_at.desc(), CNCDrafting.id.desc())
        .limit(1)
    )
    latest_cnc = latest_cnc_result.scalar_one_or_none()
    return bool(latest_cnc and latest_cnc.is_completed)


def _requires_cnc_programming(fab: Fab) -> bool:
    return fab.cnc_linft is not None and fab.cnc_linft > 0


async def _transition_to_shop_if_cutlist_complete(
    db: AsyncSession,
    fab: Fab,
    user_id: Optional[int],
) -> bool:
    if not fab:
        return False

    if fab.current_stage != "cut_list":
        return False

    if not fab.cutlist_complete:
        return False

    if _requires_cnc_programming(fab):
        if not await _has_completed_cnc_submission(db, fab.id):
            return False

    fab.current_stage = "shop"
    fab.next_stage = None
    fab.updated_at = datetime.now()
    fab.updated_by = user_id
    return True


@router.patch("/{fab_id}/schedule", response_model=dict)
async def schedule_shop_date(
    fab_id: int,
    schedule_data: CutListScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Production Coordinator: Schedule cut list shop date
    """
    try:
        result = await db.execute(select(Fab).where(Fab.id == fab_id))
        fab = result.scalar_one_or_none()

        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAB with ID {fab_id} not found"
            )

        # Normalize timezone-aware datetimes -> naive
        fab.shop_date_schedule = _to_naive_dt(schedule_data.shop_date_schedule)
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id

        if schedule_data.installation_date is not None:
            fab.installation_date = _to_naive_dt(schedule_data.installation_date)

        if schedule_data.no_of_pieces is not None:
            fab.no_of_pieces = schedule_data.no_of_pieces

        if schedule_data.total_sqft is not None:
            fab.total_sqft = schedule_data.total_sqft

        if schedule_data.wj_linft is not None:
            fab.wj_linft = schedule_data.wj_linft

        if schedule_data.edging_linft is not None:
            fab.edging_linft = schedule_data.edging_linft

        if schedule_data.cnc_linft is not None:
            fab.cnc_linft = schedule_data.cnc_linft

        if schedule_data.miter_linft is not None:
            fab.miter_linft = schedule_data.miter_linft

        if schedule_data.revision_complete is not None:
            fab.revised = not schedule_data.revision_complete

        await _transition_to_shop_if_cutlist_complete(db, fab, current_user.id)

        fab_type = (fab.fab_type or "").strip().lower()
        is_resurface = fab_type in {"resurface_scheduling", "resurface"}

        if fab.current_stage == "shop":
            fab.next_stage = None
        elif is_resurface:
            fab.next_stage = "install_scheduling"
        else:
            fab.current_stage = "cut_list"
            fab.next_stage = "final_programming"

        fab_note = FabNotes(
            fab_id=fab_id,
            note=f"Shop date scheduled for {fab.shop_date_schedule.strftime('%Y-%m-%d')}",
            stage="cut_list",
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
                "current_stage": fab.current_stage,
                "next_stage": fab.next_stage
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule shop date: {str(e)}"
        )


@router.patch("/{fab_id}/update", response_model=dict)
async def update_cut_list(
    fab_id: int,
    update_data: CutListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Production Coordinator: Update cut list information
    """
    try:
        # Get FAB
        result = await db.execute(select(Fab).where(Fab.id == fab_id))
        fab = result.scalar_one_or_none()
        
        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAB with ID {fab_id} not found"
            )
        
        # Update fields if provided
        if update_data.slab_smith_used is not None:
            fab.slab_smith_used = update_data.slab_smith_used
        
        if update_data.fp_not_needed is not None:
            fab.fp_not_needed = update_data.fp_not_needed
        
        if update_data.shop_date_schedule is not None:
            fab.shop_date_schedule = _to_naive_dt(update_data.shop_date_schedule)
        
        # Handle cutlist_complete — triggers move to shop stage
        if update_data.cutlist_complete is not None:
            fab.cutlist_complete = update_data.cutlist_complete
            if update_data.cutlist_complete is True:
                fab.current_stage = "cut_list"
                fab.next_stage = "shop"
        
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
        
        # Add notes if provided
        if update_data.notes:
            fab_note = FabNotes(
                fab_id=fab_id,
                note=update_data.notes,
                stage="cut_list",
                created_by=current_user.id,
                created_at=datetime.now()
            )
            db.add(fab_note)
        
        await db.commit()
        await db.refresh(fab)
        
        return {
            "success": True,
            "message": "Cut list updated successfully",
            "data": {
                "fab_id": fab.id,
                "slab_smith_used": fab.slab_smith_used,
                "fp_not_needed": fab.fp_not_needed,
                "shop_date_schedule": fab.shop_date_schedule.isoformat() if fab.shop_date_schedule else None,
                "cutlist_complete": fab.cutlist_complete,
                "updated_at": fab.updated_at.isoformat()
            }
        }
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cut list: {str(e)}"
        )


@router.get("/{fab_id}", response_model=dict)
async def get_cut_list_details(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Production Coordinator: Get cut list details for a FAB
    """
    # Get FAB with related data
    from ..database.business_job import BusinessJob
    from ..database.account import Account
    from ..database.stone_type import StoneType
    from ..database.stone_color import StoneColor
    from ..database.stone_thickness import StoneThickness
    from ..database.edge import Edge
    
    result = await db.execute(
        select(Fab, BusinessJob, Account, User, StoneType, StoneColor, StoneThickness, Edge)
        .join(BusinessJob, Fab.job_id == BusinessJob.id)
        .join(Account, BusinessJob.account_id == Account.id)
        .join(User, Fab.sales_person_id == User.id)
        .join(StoneType, Fab.stone_type_id == StoneType.id)
        .join(StoneColor, Fab.stone_color_id == StoneColor.id)
        .join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id)
        .join(Edge, Fab.edge_id == Edge.id)
        .where(Fab.id == fab_id)
    )
    
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAB with ID {fab_id} not found"
        )
    
    fab, job, account, sales_person, stone_type, stone_color, stone_thickness, edge = row

    if await _transition_to_shop_if_cutlist_complete(db, fab, current_user.id):
        await db.commit()
        await db.refresh(fab)
    
    # Get drafting notes
    drafting_notes_result = await db.execute(
        select(FabNotes)
        .where(FabNotes.fab_id == fab_id)
        .where(FabNotes.stage == "drafting")
        .order_by(FabNotes.created_at.desc())
        .limit(5)
    )
    drafting_notes = [note.note for note in drafting_notes_result.scalars()]
    
    return {
        "success": True,
        "message": "Cut list details retrieved successfully",
        "data": {
            "fab_id": fab.id,
            "fab_type": fab.fab_type,
            "job_name": job.name,
            "job_number": job.job_number,
            "account_name": account.name,
            "area": fab.input_area,
            "sales_person": f"{sales_person.first_name} {sales_person.last_name}",
            "stone_type": stone_type.name,
            "stone_color": stone_color.name,
            "stone_thickness": stone_thickness.thickness,
            "edge": edge.name,
            "no_of_pieces": fab.no_of_pieces,
            "total_sqft": fab.total_sqft,
            "revenue": fab.revenue,
            "gp": fab.gp,
            "shop_date_schedule": fab.shop_date_schedule.isoformat() if fab.shop_date_schedule else None,
            "installation_date": fab.installation_date.isoformat() if fab.installation_date else None,
            "final_programming_complete": fab.final_programming_complete,
            "confirmed_date": fab.confirmed_date.isoformat() if fab.confirmed_date else None,
            "slab_smith_used": fab.slab_smith_used,
            "fp_not_needed": fab.fp_not_needed,
            "cutlist_complete": fab.cutlist_complete,
            "wj_linft": fab.wj_linft,
            "edging_linft": fab.edging_linft,
            "cnc_linft": fab.cnc_linft,
            "miter_linft": fab.miter_linft,
            "drafting_notes": drafting_notes,
            "current_stage": fab.current_stage,
            "next_stage": fab.next_stage
        }
    }

def _to_naive_dt(value):
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value
