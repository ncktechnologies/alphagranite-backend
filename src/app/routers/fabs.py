from datetime import datetime, date, timedelta
from typing import List, Optional
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
import os

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.fab_notes import FabNotes
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.database.user import User
from src.app.database.edge import Edge
from src.app.database.stone_type import StoneType
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.templating import Templating
from src.app.database.sales_ct import SalesCT  # ← Add this import
from src.app.interface.business_schemas import (
    FabCreate, FabUpdate, FabResponse,
)
from src.app.interface.response_wrappers import SuccessResponse, error_response, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()

# Define the fab workflow stages in order (based on client workflow)
FAB_STAGES = [
    "templating",               # Stage 1: Templating
    "pre_draft_review",         # Stage 2: Pre-Draft Review
    "drafting",                 # Stage 3: Drafting
    "sales_ct",                 # Stage 4: SalesCT (SCT)
    "slab_smith_request",       # Stage 5: SlabSmith Request
    "final_programming",        # Stage 6: Final Programming
    "wj_programming",           # Stage 7: WJ Programming
    "cut_list",                 # Stage 8: Cut List
    "wj_scheduling",            # Stage 9: WJ Scheduling
    "resurface_scheduling",     # Stage 10: Resurface Scheduling
    "revisions",                # Stage 11: Revisions
    "cost_of_stone",            # Stage 12: Cost of Stone
    "install_scheduling",       # Stage 13: Install Scheduling
    "install_completion"        # Stage 14: Install Completion (final stage)
]

BASE_URL = os.getenv("BASE_URL", "https://api.ag.easybusiness.ng")

def get_next_stage(current_stage: str) -> Optional[str]:
    """
    Get the next stage in the fab workflow.
    Returns None if current stage is the last stage (shop_production).
    """
    if not current_stage:
        return "templating"  # Default to templating if no stage
    
    try:
        current_index = FAB_STAGES.index(current_stage)
        next_index = current_index + 1
        
        if next_index < len(FAB_STAGES):
            return FAB_STAGES[next_index]
        
        return None  # Last stage, no next stage
    except ValueError:
        # Current stage not in list, default to templating
        return "templating"


async def get_stage_completion_data(db: AsyncSession, fab_id: int, current_stage: Optional[str]) -> dict:
    """
    Check if current stage is complete and return stage-specific data.
    
    Stage completion rules:
    - templating: Complete when templating schedule exists with is_completed=True
    - pre_draft_review: Complete when pre-draft review is approved
    - drafting: Complete when drafting is completed
    - sales_ct: Complete when SCT is done
    - slab_smith_request: Complete when SlabSmith request is processed
    - final_programming: Complete when final programming is done
    - wj_programming: Complete when WJ programming is done
    - cut_list: Complete when cut list is generated
    - wj_scheduling: Complete when WJ is scheduled
    - resurface_scheduling: Complete when resurfacing is scheduled
    - revisions: Complete when revisions are done
    - cost_of_stone: Complete when cost is calculated
    - install_scheduling: Complete when installation is scheduled
    - install_completion: Complete when installation is done (final stage)
    """
    stage_info = {
        "is_complete": False,
        "stage_data": None
    }
    
    if not current_stage:
        return stage_info
    
    # Check templating stage completion
    if current_stage == "templating":
        query = select(Templating).where(
            Templating.fab_id == fab_id,
            Templating.is_templating_schedule == True
        ).order_by(Templating.id.desc()).limit(1)
        result = await db.execute(query)
        templating = result.scalar_one_or_none()
        
        if templating:
            stage_info["is_complete"] = templating.is_completed
            stage_info["stage_data"] = {
                "templating_id": templating.id,
                "technician_id": templating.technician_id,
                "schedule_start_date": templating.schedule_start_date.isoformat() if templating.schedule_start_date else None,
                "schedule_due_date": templating.schedule_due_date.isoformat() if templating.schedule_due_date else None,
                "actual_start_date": templating.actual_start_date.isoformat() if templating.actual_start_date else None,
                "duration": templating.duration,
                "total_sqft": templating.total_sqft,
                "is_completed": templating.is_completed,
                "notes": templating.notes
            }
    
    # Add more stage completion checks as needed for other stages
    # For now, other stages default to is_complete=False
    
    return stage_info


async def get_fab_notes(db: AsyncSession, fab_id: int) -> List[dict]:
    """Get last 10 fab notes for a given FAB"""
    from sqlalchemy.orm import aliased
    
    CreatorUser = aliased(User)
    UpdaterUser = aliased(User)
    
    query = select(
        FabNotes,
        CreatorUser.first_name.label("creator_first_name"),
        CreatorUser.last_name.label("creator_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(FabNotes.fab_id == fab_id)
    
    query = query.join(CreatorUser, FabNotes.created_by == CreatorUser.id, isouter=True)
    query = query.join(UpdaterUser, FabNotes.updated_by == UpdaterUser.id, isouter=True)
    query = query.order_by(FabNotes.created_at.desc()).limit(10)
    
    result = await db.execute(query)
    rows = result.all()
    
    notes = []
    for row in rows:
        fab_note = row[0]
        creator_first = row[1]
        creator_last = row[2]
        updater_first = row[3]
        updater_last = row[4]
        
        note_dict = {
            "id": fab_note.id,
            "fab_id": fab_note.fab_id,
            "stage": fab_note.stage,
            "note": fab_note.note,
            "created_by": fab_note.created_by,
            "created_by_name": f"{creator_first} {creator_last}" if creator_first else None,
            "created_at": fab_note.created_at.isoformat() if fab_note.created_at else None,
            "updated_at": fab_note.updated_at.isoformat() if fab_note.updated_at else None,
            "updated_by": fab_note.updated_by,
            "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
        }
        notes.append(note_dict)
    
    return notes


@router.post("/fabs", response_model=SuccessResponse[FabResponse], status_code=201)
async def create_fab(
    fab_data: FabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new fab with validation"""
    
    # Validate all foreign key relationships
    # Job validation
    job = await db.get(BusinessJob, fab_data.job_id)
    if not job:
        return error_response("Job not found", 404)
    
    # Sales person validation
    sales_person = await db.get(User, fab_data.sales_person_id)
    if not sales_person:
        return error_response("Sales person not found", 404)
    
    # Stone type validation
    stone_type = await db.get(StoneType, fab_data.stone_type_id)
    if not stone_type:
        return error_response("Stone type not found", 404)
    
    # Stone color validation
    stone_color = await db.get(StoneColor, fab_data.stone_color_id)
    if not stone_color:
        return error_response("Stone color not found", 404)
    
    # Stone thickness validation
    stone_thickness = await db.get(StoneThickness, fab_data.stone_thickness_id)
    if not stone_thickness:
        return error_response("Stone thickness not found", 404)
    
    # Edge validation
    edge = await db.get(Edge, fab_data.edge_id)
    if not edge:
        return error_response("Edge not found", 404)
    
    # Create the fab and start it at templating stage
    fab_dict = fab_data.model_dump()
    
    # Set default total_sqft to 1 if not provided (as per client requirement)
    if "total_sqft" not in fab_dict or fab_dict["total_sqft"] is None:
        fab_dict["total_sqft"] = 1.0
    
    fab = Fab(
        **fab_dict,
        current_stage="templating",
        next_stage="pre_draft_review",  # Next stage after templating
        status_id=1,  # Active/Created status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(fab)
    await db.commit()
    await db.refresh(fab)
    
    # Get the created fab with related data
    return await get_fab(fab.id, db, current_user)


@router.get("/fabs")
async def get_fabs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    fab_type: Optional[str] = Query(None, description="Filter by fab type"),
    sales_person_id: Optional[int] = Query(None, description="Filter by sales person ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
    next_stage: Optional[str] = Query(None, description="Filter by next stage"),
    schedule_start_date: Optional[date] = Query(None, description="Filter FABs scheduled on or after this date (YYYY-MM-DD)"),
    schedule_due_date: Optional[date] = Query(None, description="Filter FABs scheduled on or before this date (YYYY-MM-DD)"),
    date_filter: Optional[str] = Query(None, description="Predefined date filter: today, this_week, this_month, next_week, next_month, scheduled, unscheduled"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fabs with optional filtering and pagination"""
    
    # Use aliased User for sales_person, technician, drafter, and drafter_assigned_by to avoid conflicts
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_
    TechnicianUser = aliased(User)
    DrafterUser = aliased(User)
    DrafterAssignedByUser = aliased(User)
    
    # Subquery to get the latest templating record for each FAB
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )
    
    # Build query with joins to get related data including templating and drafter
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        latest_templating.c.schedule_start_date.label("templating_schedule_start_date"),
        latest_templating.c.schedule_due_date.label("templating_schedule_due_date"),
        latest_templating.c.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name"),
        BusinessJob,  # Include full BusinessJob object
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone"),
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        DrafterAssignedByUser.first_name.label("drafter_assigned_by_first_name"),
        DrafterAssignedByUser.last_name.label("drafter_assigned_by_last_name")
    ).select_from(Fab)
    
    # Join with related tables
    query = query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
    query = query.join(Account, BusinessJob.account_id == Account.id, isouter=True)
    query = query.join(User, Fab.sales_person_id == User.id, isouter=True)
    query = query.join(StoneType, Fab.stone_type_id == StoneType.id, isouter=True)
    query = query.join(StoneColor, Fab.stone_color_id == StoneColor.id, isouter=True)
    query = query.join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id, isouter=True)
    query = query.join(Edge, Fab.edge_id == Edge.id, isouter=True)
    query = query.outerjoin(latest_templating, sa.literal(True))
    query = query.join(TechnicianUser, latest_templating.c.technician_id == TechnicianUser.id, isouter=True)
    query = query.join(DrafterUser, Fab.drafter_id == DrafterUser.id, isouter=True)
    query = query.join(DrafterAssignedByUser, Fab.drafter_assigned_by == DrafterAssignedByUser.id, isouter=True)
    
    # Apply filters
    if job_id is not None:
        query = query.where(Fab.job_id == job_id)
    if fab_type:
        query = query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        query = query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        query = query.where(Fab.status_id == status_id)
    if current_stage:
        query = query.where(Fab.current_stage == current_stage)
    if next_stage:
        query = query.where(Fab.next_stage == next_stage)
    
    # Apply predefined date filters
    if date_filter:
        today = date.today()
        
        if date_filter == "today":
            query = query.where(latest_templating.c.schedule_start_date == today)
        
        elif date_filter == "this_week":
            # Get start of week (Monday) and end of week (Sunday)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            query = query.where(
                latest_templating.c.schedule_start_date >= start_of_week,
                latest_templating.c.schedule_start_date <= end_of_week
            )
        
        elif date_filter == "this_month":
            # Get first day and last day of current month
            start_of_month = today.replace(day=1)
            if today.month == 12:
                end_of_month = today.replace(day=31)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
                end_of_month = next_month - timedelta(days=1)
            query = query.where(
                latest_templating.c.schedule_start_date >= start_of_month,
                latest_templating.c.schedule_start_date <= end_of_month
            )
        
        elif date_filter == "next_week":
            # Get start of next week (next Monday) and end of next week (next Sunday)
            start_of_next_week = today + timedelta(days=(7 - today.weekday()))
            end_of_next_week = start_of_next_week + timedelta(days=6)
            query = query.where(
                latest_templating.c.schedule_start_date >= start_of_next_week,
                latest_templating.c.schedule_start_date <= end_of_next_week
            )
        
        elif date_filter == "next_month":
            # Get first day and last day of next month
            if today.month == 12:
                start_of_next_month = date(today.year + 1, 1, 1)
                end_of_next_month = date(today.year + 1, 1, 31)
            else:
                start_of_next_month = date(today.year, today.month + 1, 1)
                if today.month == 11:
                    end_of_next_month = date(today.year, 12, 31)
                else:
                    following_month = date(today.year, today.month + 2, 1)
                    end_of_next_month = following_month - timedelta(days=1)
            query = query.where(
                latest_templating.c.schedule_start_date >= start_of_next_month,
                latest_templating.c.schedule_start_date <= end_of_next_month
            )
        
        elif date_filter == "scheduled":
            # Return FABs that have a schedule_start_date
            query = query.where(latest_templating.c.schedule_start_date.isnot(None))
        
        elif date_filter == "unscheduled":
            # Return FABs with no schedule_start_date
            query = query.where(latest_templating.c.schedule_start_date.is_(None))
    
    # Apply custom date range filters (if provided, override date_filter)
    if schedule_start_date is not None:
        query = query.where(latest_templating.c.schedule_start_date >= schedule_start_date)
    if schedule_due_date is not None:
        query = query.where(latest_templating.c.schedule_due_date <= schedule_due_date)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Fab.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Process the results to include related names
    fabs = []
    for row in rows:
        fab = row[0]
        sales_person_first_name = row[1]
        sales_person_last_name = row[2]
        stone_type_name = row[3]
        stone_color_name = row[4]
        stone_thickness_value = row[5]
        edge_name = row[6]
        templating_schedule_start_date = row[7]
        templating_schedule_due_date = row[8]
        templating_notes = row[9]
        technician_first_name = row[10]
        technician_last_name = row[11]
        business_job = row[12]  # BusinessJob object
        account_name = row[13]
        account_number = row[14]
        account_contact_person = row[15]
        account_email = row[16]
        account_phone = row[17]
        drafter_first_name = row[18]
        drafter_last_name = row[19]
        drafter_assigned_by_first_name = row[20]
        drafter_assigned_by_last_name = row[21]
        
        # Convert to dict and serialize datetime/date/Decimal objects
        fab_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                    for k, v in fab.__dict__.items() if not k.startswith('_')}
        
        # Ensure notes is always a list
        if fab_dict.get("notes") and not isinstance(fab_dict["notes"], list):
            fab_dict["notes"] = [fab_dict["notes"]] if fab_dict["notes"] else None
        
        fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
        fab_dict["stone_type_name"] = stone_type_name
        fab_dict["stone_color_name"] = stone_color_name
        fab_dict["stone_thickness_value"] = stone_thickness_value
        fab_dict["edge_name"] = edge_name
        
        # Add job details as a dictionary
        if business_job:
            job_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                       for k, v in business_job.__dict__.items() if not k.startswith('_')}
            fab_dict["job_details"] = job_dict
            fab_dict["account_id"] = business_job.account_id
        else:
            fab_dict["job_details"] = None
            fab_dict["account_id"] = None

        # Add account data
        fab_dict["account_name"] = account_name
        fab_dict["account_number"] = account_number
        fab_dict["account_contact_person"] = account_contact_person
        fab_dict["account_email"] = account_email
        fab_dict["account_phone"] = account_phone
        
        # Add templating data
        fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
        fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
        fab_dict["templating_notes"] = templating_notes
        fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
        
        # Add drafter information
        fab_dict["drafter_name"] = f"{drafter_first_name} {drafter_last_name}" if drafter_first_name else None
        fab_dict["drafter_assigned_by_name"] = f"{drafter_assigned_by_first_name} {drafter_assigned_by_last_name}" if drafter_assigned_by_first_name else None
        
        # Add next stage
        fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
        
        fabs.append(fab_dict)
    
    # Fetch fab_notes and stage data for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
        
        # Fetch draft data
        draft_data = await get_draft_data(db, fab_dict["id"])
        fab_dict["draft_data"] = draft_data
        
        # Fetch Sales CT data
        sales_ct_data = await get_sales_ct_data(db, fab_dict["id"])
        fab_dict["sales_ct_data"] = sales_ct_data
        
        # Add stage completion status and stage-specific data
        stage_info = await get_stage_completion_data(db, fab_dict["id"], fab_dict.get("current_stage"))
        fab_dict["is_complete"] = stage_info["is_complete"]
        fab_dict["stage_data"] = stage_info["stage_data"]
    
    # Count total FABs with same filters (without pagination)
    count_query = select(func.count(Fab.id)).select_from(Fab)
    count_query = count_query.outerjoin(latest_templating, sa.literal(True))
    
    if job_id is not None:
        count_query = count_query.where(Fab.job_id == job_id)
    if fab_type:
        count_query = count_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        count_query = count_query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        count_query = count_query.where(Fab.status_id == status_id)
    if current_stage:
        count_query = count_query.where(Fab.current_stage == current_stage)
    if next_stage:
        count_query = count_query.where(Fab.next_stage == next_stage)
    
    # Apply predefined date filters to count query
    if date_filter:
        today = date.today()
        
        if date_filter == "today":
            count_query = count_query.where(latest_templating.c.schedule_start_date == today)
        elif date_filter == "this_week":
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            count_query = count_query.where(
                latest_templating.c.schedule_start_date >= start_of_week,
                latest_templating.c.schedule_start_date <= end_of_week
            )
        elif date_filter == "this_month":
            start_of_month = today.replace(day=1)
            if today.month == 12:
                end_of_month = today.replace(day=31)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
                end_of_month = next_month - timedelta(days=1)
            count_query = count_query.where(
                latest_templating.c.schedule_start_date >= start_of_month,
                latest_templating.c.schedule_start_date <= end_of_month
            )
        elif date_filter == "next_week":
            start_of_next_week = today + timedelta(days=(7 - today.weekday()))
            end_of_next_week = start_of_next_week + timedelta(days=6)
            count_query = count_query.where(
                latest_templating.c.schedule_start_date >= start_of_next_week,
                latest_templating.c.schedule_start_date <= end_of_next_week
            )
        elif date_filter == "next_month":
            if today.month == 12:
                start_of_next_month = date(today.year + 1, 1, 1)
                end_of_next_month = date(today.year + 1, 1, 31)
            else:
                start_of_next_month = date(today.year, today.month + 1, 1)
                if today.month == 11:
                    end_of_next_month = date(today.year, 12, 31)
                else:
                    following_month = date(today.year, today.month + 2, 1)
                    end_of_next_month = following_month - timedelta(days=1)
            count_query = count_query.where(
                latest_templating.c.schedule_start_date >= start_of_next_month,
                latest_templating.c.schedule_start_date <= end_of_next_month
            )
        elif date_filter == "scheduled":
            count_query = count_query.where(latest_templating.c.schedule_start_date.isnot(None))
        elif date_filter == "unscheduled":
            count_query = count_query.where(latest_templating.c.schedule_start_date.is_(None))
    
    if schedule_start_date is not None:
        count_query = count_query.where(latest_templating.c.schedule_start_date >= schedule_start_date)
    if schedule_due_date is not None:
        count_query = count_query.where(latest_templating.c.schedule_due_date <= schedule_due_date)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Calculate aggregated totals when current_stage filter is present
    stage_totals = None
    if current_stage:
        # Build aggregation query with same filters (no pagination)
        totals_query = select(
            func.sum(Fab.total_sqft).label("total_sqft"),
            func.sum(Fab.wj_linft).label("wj_linft"),
            func.sum(Fab.edging_linft).label("edging_linft"),
            func.sum(Fab.cnc_linft).label("cnc_linft"),
            func.sum(Fab.miter_linft).label("miter_linft"),
            func.sum(Fab.no_of_pieces).label("no_of_pieces")
        ).select_from(Fab)
        
        totals_query = totals_query.outerjoin(latest_templating, sa.literal(True))
        
        # Apply same filters as count query
        if job_id is not None:
            totals_query = totals_query.where(Fab.job_id == job_id)
        if fab_type:
            totals_query = totals_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
        if sales_person_id is not None:
            totals_query = totals_query.where(Fab.sales_person_id == sales_person_id)
        if status_id is not None:
            totals_query = totals_query.where(Fab.status_id == status_id)
        totals_query = totals_query.where(Fab.current_stage == current_stage)
        if next_stage:
            totals_query = totals_query.where(Fab.next_stage == next_stage)
        
        # Apply predefined date filters to totals query
        if date_filter:
            today = date.today()
            
            if date_filter == "today":
                totals_query = totals_query.where(latest_templating.c.schedule_start_date == today)
            elif date_filter == "this_week":
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                totals_query = totals_query.where(
                    latest_templating.c.schedule_start_date >= start_of_week,
                    latest_templating.c.schedule_start_date <= end_of_week
                )
            elif date_filter == "this_month":
                start_of_month = today.replace(day=1)
                if today.month == 12:
                    end_of_month = today.replace(day=31)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                    end_of_month = next_month - timedelta(days=1)
                totals_query = totals_query.where(
                    latest_templating.c.schedule_start_date >= start_of_month,
                    latest_templating.c.schedule_start_date <= end_of_month
                )
            elif date_filter == "next_week":
                start_of_next_week = today + timedelta(days=(7 - today.weekday()))
                end_of_next_week = start_of_next_week + timedelta(days=6)
                totals_query = totals_query.where(
                    latest_templating.c.schedule_start_date >= start_of_next_week,
                    latest_templating.c.schedule_start_date <= end_of_next_week
                )
            elif date_filter == "next_month":
                if today.month == 12:
                    start_of_next_month = date(today.year + 1, 1, 1)
                    end_of_next_month = date(today.year + 1, 1, 31)
                else:
                    start_of_next_month = date(today.year, today.month + 1, 1)
                    if today.month == 11:
                        end_of_next_month = date(today.year, 12, 31)
                    else:
                        following_month = date(today.year, today.month + 2, 1)
                        end_of_next_month = following_month - timedelta(days=1)
                totals_query = totals_query.where(
                    latest_templating.c.schedule_start_date >= start_of_next_month,
                    latest_templating.c.schedule_start_date <= end_of_next_month
                )
            elif date_filter == "scheduled":
                totals_query = totals_query.where(latest_templating.c.schedule_start_date.isnot(None))
            elif date_filter == "unscheduled":
                totals_query = totals_query.where(latest_templating.c.schedule_start_date.is_(None))
        
        if schedule_start_date is not None:
            totals_query = totals_query.where(latest_templating.c.schedule_start_date >= schedule_start_date)
        if schedule_due_date is not None:
            totals_query = totals_query.where(latest_templating.c.schedule_due_date <= schedule_due_date)
        
        totals_result = await db.execute(totals_query)
        totals_row = totals_result.first()
        
        if totals_row:
            stage_totals = {
                "stage": current_stage,
                "total_sqft": float(totals_row[0]) if totals_row[0] else 0.0,
                "wj_linft": float(totals_row[1]) if totals_row[1] else 0.0,
                "edging_linft": float(totals_row[2]) if totals_row[2] else 0.0,
                "cnc_linft": float(totals_row[3]) if totals_row[3] else 0.0,
                "miter_linft": float(totals_row[4]) if totals_row[4] else 0.0,
                "no_of_pieces": int(totals_row[5]) if totals_row[5] else 0
            }
    
    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "data": fabs
    }
    
    # Add stage totals if present
    if stage_totals:
        response_data["stage_totals"] = stage_totals
    
    return {
        "success": True,
        "message": "FABs retrieved successfully",
        "data": response_data
    }


@router.get("/fabs/{fab_id}", response_model=SuccessResponse[FabResponse])
async def get_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific fab by ID with related data"""
    # Use a join query to get all related data in one go
    # Use aliased User for sales_person, technician, drafter, and drafter_assigned_by to avoid conflicts
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_
    TechnicianUser = aliased(User)
    DrafterUser = aliased(User)
    DrafterAssignedByUser = aliased(User)
    
    # Subquery to get the latest templating record for this FAB
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )
    
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        latest_templating.c.schedule_start_date.label("templating_schedule_start_date"),
        latest_templating.c.schedule_due_date.label("templating_schedule_due_date"),
        latest_templating.c.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name"),
        BusinessJob,  # Include full BusinessJob object
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone"),
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        DrafterAssignedByUser.first_name.label("drafter_assigned_by_first_name"),
        DrafterAssignedByUser.last_name.label("drafter_assigned_by_last_name")
    ).select_from(Fab).where(Fab.id == fab_id)
    
    # Join with related tables
    query = query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
    query = query.join(Account, BusinessJob.account_id == Account.id, isouter=True)
    query = query.join(User, Fab.sales_person_id == User.id, isouter=True)
    query = query.join(StoneType, Fab.stone_type_id == StoneType.id, isouter=True)
    query = query.join(StoneColor, Fab.stone_color_id == StoneColor.id, isouter=True)
    query = query.join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id, isouter=True)
    query = query.join(Edge, Fab.edge_id == Edge.id, isouter=True)
    query = query.outerjoin(latest_templating, sa.literal(True))
    query = query.join(TechnicianUser, latest_templating.c.technician_id == TechnicianUser.id, isouter=True)
    query = query.join(DrafterUser, Fab.drafter_id == DrafterUser.id, isouter=True)
    query = query.join(DrafterAssignedByUser, Fab.drafter_assigned_by == DrafterAssignedByUser.id, isouter=True)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return error_response("Fab not found", 404)
    
    # Unpack the row
    fab = row[0]
    sales_person_first_name = row[1]
    sales_person_last_name = row[2]
    stone_type_name = row[3]
    stone_color_name = row[4]
    stone_thickness_value = row[5]
    edge_name = row[6]
    templating_schedule_start_date = row[7]
    templating_schedule_due_date = row[8]
    templating_notes = row[9]
    technician_first_name = row[10]
    technician_last_name = row[11]
    business_job = row[12]
    account_name = row[13]
    account_number = row[14]
    account_contact_person = row[15]
    account_email = row[16]
    account_phone = row[17]
    drafter_first_name = row[18]
    drafter_last_name = row[19]
    drafter_assigned_by_first_name = row[20]
    drafter_assigned_by_last_name = row[21]
    
    # Convert to dict and add related names (handle datetime, date, and Decimal serialization)
    fab_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                for k, v in fab.__dict__.items() if not k.startswith('_')}
    
    # Ensure notes is always a list
    if fab_dict.get("notes") and not isinstance(fab_dict["notes"], list):
        fab_dict["notes"] = [fab_dict["notes"]] if fab_dict["notes"] else None
    
    fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
    fab_dict["stone_type_name"] = stone_type_name
    fab_dict["stone_color_name"] = stone_color_name
    fab_dict["stone_thickness_value"] = stone_thickness_value
    fab_dict["edge_name"] = edge_name
    
    # Add job details as a dictionary
    if business_job:
        job_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                   for k, v in business_job.__dict__.items() if not k.startswith('_')}
        fab_dict["job_details"] = job_dict
        fab_dict["account_id"] = business_job.account_id
    else:
        fab_dict["job_details"] = None
        fab_dict["account_id"] = None

    # Add account data
    fab_dict["account_name"] = account_name
    fab_dict["account_number"] = account_number
    fab_dict["account_contact_person"] = account_contact_person
    fab_dict["account_email"] = account_email
    fab_dict["account_phone"] = account_phone
    
    # Add templating data
    fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
    fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
    fab_dict["templating_notes"] = templating_notes
    fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
    
    # Add drafter information
    fab_dict["drafter_name"] = f"{drafter_first_name} {drafter_last_name}" if drafter_first_name else None
    fab_dict["drafter_assigned_by_name"] = f"{drafter_assigned_by_first_name} {drafter_assigned_by_last_name}" if drafter_assigned_by_first_name else None
    
    # Add next stage
    fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
    
    # Fetch fab_notes
    fab_notes = await get_fab_notes(db, fab_id)
    fab_dict["fab_notes"] = fab_notes
    
    # Fetch draft data
    draft_data = await get_draft_data(db, fab_id)
    fab_dict["draft_data"] = draft_data
    
    # Add stage completion status and stage-specific data
    stage_info = await get_stage_completion_data(db, fab_id, fab_dict.get("current_stage"))
    fab_dict["is_complete"] = stage_info["is_complete"]
    fab_dict["stage_data"] = stage_info["stage_data"]
    
    # Determine success message based on stage
    message = "Fab fetched successfully"
    if fab_dict.get("current_stage") == "templating" and fab_dict.get("updated_at") is None:
        # Just created (no updates yet)
        message = f"FAB {fab_dict['id']} submitted successfully for review!"
    
    return success_response(fab_dict, message)


@router.put("/fabs/{fab_id}", response_model=SuccessResponse[FabResponse])
async def update_fab(
    fab_id: int,
    fab_data: FabUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a fab"""
    from src.app.database.fab_notes import FabNotes
    
    # Get existing fab
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(status_code=404, detail="Fab not found")
    
    # Validate foreign key relationships if being updated
    if fab_data.sales_person_id:
        sales_person_result = await db.execute(select(User).where(User.id == fab_data.sales_person_id))
        if not sales_person_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Sales person not found")
    
    if fab_data.stone_type_id:
        stone_type_result = await db.execute(select(StoneType).where(StoneType.id == fab_data.stone_type_id))
        if not stone_type_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone type not found")
    
    if fab_data.stone_color_id:
        stone_color_result = await db.execute(select(StoneColor).where(StoneColor.id == fab_data.stone_color_id))
        if not stone_color_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone color not found")
    
    if fab_data.stone_thickness_id:
        thickness_result = await db.execute(select(StoneThickness).where(StoneThickness.id == fab_data.stone_thickness_id))
        if not thickness_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Stone thickness not found")
    
    if fab_data.edge_id:
        edge_result = await db.execute(select(Edge).where(Edge.id == fab_data.edge_id))
        if not edge_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Edge not found")
    
    # Validate drafter if provided
    if fab_data.drafter_id:
        drafter_result = await db.execute(select(User).where(User.id == fab_data.drafter_id))
        if not drafter_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Drafter not found")
    
    # Extract note and stage before updating
    note_text = fab_data.notes
    note_stage = fab_data.stage if fab_data.stage else fab.current_stage
    
    # Update fields (exclude notes and stage as they're for fab_notes)
    update_data = fab_data.model_dump(exclude_unset=True, exclude={"notes", "stage"})
    
    # Track if current_stage is being updated
    stage_changed = False
    new_current_stage = None
    
    # Handle drafter assignment
    if fab_data.drafter_id and fab_data.drafter_id != fab.drafter_id:
        # New drafter assigned
        fab.drafter_id = fab_data.drafter_id
        fab.drafter_assigned_by = current_user.id
        fab.drafter_assigned_at = datetime.now()
        fab.drafting_needed = True  # Set drafting_needed to True when drafter assigned
    
    for field, value in update_data.items():
        if field == "current_stage":
            stage_changed = True
            new_current_stage = value
        setattr(fab, field, value)
    
    # If current_stage was updated, automatically update next_stage
    if stage_changed and new_current_stage:
        fab.next_stage = get_next_stage(new_current_stage)
    
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    # Create FabNotes entry if notes provided
    if note_text:
        fab_note = FabNotes(
            fab_id=fab_id,
            stage=note_stage,
            note=note_text,
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(fab_note)
    
    await db.commit()
    await db.refresh(fab)
    
    # Return the updated FAB with full context (drafter info, notes, etc.)
    return await get_fab(fab_id, db, current_user)


@router.delete("/fabs/{fab_id}", status_code=204)
async def delete_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a fab (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    
    if not fab:
        raise HTTPException(status_code=404, detail="Fab not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    fab.status_id = 3  # Deleted status
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    
    return None


@router.get("/jobs/{job_id}/fabs", response_model=SuccessResponse[List[FabResponse]])
async def get_fabs_by_job(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all fabs for a specific job"""
    
    # Check if job exists
    job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Use the same query pattern as get_fabs for consistency
    from sqlalchemy.orm import aliased
    TechnicianUser = aliased(User)
    DrafterUser = aliased(User)
    DrafterAssignedByUser = aliased(User)
    
    # Subquery to get the latest templating record for each FAB
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )
    
    # Build query with joins to get related data
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        latest_templating.c.schedule_start_date.label("templating_schedule_start_date"),
        latest_templating.c.schedule_due_date.label("templating_schedule_due_date"),
        latest_templating.c.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name"),
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone"),
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        DrafterAssignedByUser.first_name.label("drafter_assigned_by_first_name"),
        DrafterAssignedByUser.last_name.label("drafter_assigned_by_last_name")
    ).select_from(Fab).where(Fab.job_id == job_id)
    
    # Join with related tables
    query = query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
    query = query.join(Account, BusinessJob.account_id == Account.id, isouter=True)
    query = query.join(User, Fab.sales_person_id == User.id, isouter=True)
    query = query.join(StoneType, Fab.stone_type_id == StoneType.id, isouter=True)
    query = query.join(StoneColor, Fab.stone_color_id == StoneColor.id, isouter=True)
    query = query.join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id, isouter=True)
    query = query.join(Edge, Fab.edge_id == Edge.id, isouter=True)
    query = query.outerjoin(latest_templating, sa.literal(True))
    query = query.join(TechnicianUser, latest_templating.c.technician_id == TechnicianUser.id, isouter=True)
    query = query.join(DrafterUser, Fab.drafter_id == DrafterUser.id, isouter=True)
    query = query.join(DrafterAssignedByUser, Fab.drafter_assigned_by == DrafterAssignedByUser.id, isouter=True)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Fab.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Process the results
    fabs = []
    for row in rows:
        fab = row[0]
        sales_person_first_name = row[1]
        sales_person_last_name = row[2]
        stone_type_name = row[3]
        stone_color_name = row[4]
        stone_thickness_value = row[5]
        edge_name = row[6]
        templating_schedule_start_date = row[7]
        templating_schedule_due_date = row[8]
        templating_notes = row[9]
        technician_first_name = row[10]
        technician_last_name = row[11]
        business_job = row[12]
        account_name = row[13]
        account_number = row[14]
        account_contact_person = row[15]
        account_email = row[16]
        account_phone = row[17]
        drafter_first_name = row[18]
        drafter_last_name = row[19]
        drafter_assigned_by_first_name = row[20]
        drafter_assigned_by_last_name = row[21]
        
        # Convert to dict and serialize datetime/date/Decimal objects
        fab_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                    for k, v in fab.__dict__.items() if not k.startswith('_')}
        fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
        fab_dict["stone_type_name"] = stone_type_name
        fab_dict["stone_color_name"] = stone_color_name
        fab_dict["stone_thickness_value"] = stone_thickness_value
        fab_dict["edge_name"] = edge_name
        
        # Add job details
        if business_job:
            job_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                       for k, v in business_job.__dict__.items() if not k.startswith('_')}
            fab_dict["job_details"] = job_dict
            fab_dict["account_id"] = business_job.account_id
        else:
            fab_dict["job_details"] = None
            fab_dict["account_id"] = None

        # Add account data
        fab_dict["account_name"] = account_name
        fab_dict["account_number"] = account_number
        fab_dict["account_contact_person"] = account_contact_person
        fab_dict["account_email"] = account_email
        fab_dict["account_phone"] = account_phone
        
        # Add templating data
        fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
        fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
        fab_dict["templating_notes"] = templating_notes
        fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
        
        # Add drafter information
        fab_dict["drafter_name"] = f"{drafter_first_name} {drafter_last_name}" if drafter_first_name else None
        fab_dict["drafter_assigned_by_name"] = f"{drafter_assigned_by_first_name} {drafter_assigned_by_last_name}" if drafter_assigned_by_first_name else None
        
        # ALWAYS add current_stage and next_stage
        fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
        
        fabs.append(fab_dict)
    
    # Fetch fab_notes for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
        
        # Fetch draft data
        draft_data = await get_draft_data(db, fab_dict["id"])  # ← Add this if missing
        fab_dict["draft_data"] = draft_data  # ← Add this if missing
        
        # Fetch Sales CT data
        sales_ct_data = await get_sales_ct_data(db, fab_dict["id"])  # ← Add this
        fab_dict["sales_ct_data"] = sales_ct_data  # ← Add this
    
    return success_response(fabs, f"Found {len(fabs)} FABs for job {job_id}")


@router.get("/stages/{stage_name}/fabs", response_model=SuccessResponse[dict])
async def get_fabs_by_stage(
    stage_name: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of FABs in a specific stage"""
    
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_, func
    
    # Aliases for different user roles
    TechnicianUser = aliased(User)
    DrafterUser = aliased(User)
    DrafterAssignedByUser = aliased(User)
    
    # Subquery for latest templating
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )
    
    # Build base query with all joins
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        latest_templating.c.schedule_start_date.label("templating_schedule_start_date"),
        latest_templating.c.schedule_due_date.label("templating_schedule_due_date"),
        latest_templating.c.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name"),
        BusinessJob,
        Account.name.label("account_name"),
        Account.account_number.label("account_number"),
        Account.contact_person.label("account_contact_person"),
        Account.email.label("account_email"),
        Account.phone.label("account_phone"),
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        DrafterAssignedByUser.first_name.label("drafter_assigned_by_first_name"),
        DrafterAssignedByUser.last_name.label("drafter_assigned_by_last_name")
    ).select_from(Fab)\
        .outerjoin(User, Fab.sales_person_id == User.id)\
        .outerjoin(StoneType, Fab.stone_type_id == StoneType.id)\
        .outerjoin(StoneColor, Fab.stone_color_id == StoneColor.id)\
        .outerjoin(StoneThickness, Fab.stone_thickness_id == StoneThickness.id)\
        .outerjoin(Edge, Fab.edge_id == Edge.id)\
        .outerjoin(latest_templating, sa.literal(True))\
        .outerjoin(TechnicianUser, latest_templating.c.technician_id == TechnicianUser.id)\
        .outerjoin(BusinessJob, Fab.job_id == BusinessJob.id)\
        .outerjoin(Account, BusinessJob.account_id == Account.id)\
        .outerjoin(DrafterUser, Fab.drafter_id == DrafterUser.id)\
        .outerjoin(DrafterAssignedByUser, Fab.drafter_assigned_by == DrafterAssignedByUser.id)
    
    # Filter by stage (required)
    query = query.where(Fab.current_stage == stage_name)
    
    # Apply optional filters
    if job_id:
        query = query.where(Fab.job_id == job_id)
    if status_id:
        query = query.where(Fab.status_id == status_id)
    
    # Get total count before pagination
    count_query = select(func.count()).select_from(Fab).where(Fab.current_stage == stage_name)
    if job_id:
        count_query = count_query.where(Fab.job_id == job_id)
    if status_id:
        count_query = count_query.where(Fab.status_id == status_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    fabs = []
    for row in rows:
        fab = row[0]
        sales_person_first_name = row[1]
        sales_person_last_name = row[2]
        stone_type_name = row[3]
        stone_color_name = row[4]
        stone_thickness_value = row[5]
        edge_name = row[6]
        templating_schedule_start_date = row[7]
        templating_schedule_due_date = row[8]
        templating_notes = row[9]
        technician_first_name = row[10]
        technician_last_name = row[11]
        business_job = row[12]
        account_name = row[13]
        account_number = row[14]
        account_contact_person = row[15]
        account_email = row[16]
        account_phone = row[17]
        drafter_first_name = row[18]
        drafter_last_name = row[19]
        drafter_assigned_by_first_name = row[20]
        drafter_assigned_by_last_name = row[21]
        
        # Convert to dict and serialize datetime/date/Decimal objects
        fab_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                    for k, v in fab.__dict__.items() if not k.startswith('_')}
        fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
        fab_dict["stone_type_name"] = stone_type_name
        fab_dict["stone_color_name"] = stone_color_name
        fab_dict["stone_thickness_value"] = stone_thickness_value
        fab_dict["edge_name"] = edge_name
        
        # Add job details
        if business_job:
            job_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                       for k, v in business_job.__dict__.items() if not k.startswith('_')}
            fab_dict["job_details"] = job_dict
            fab_dict["account_id"] = business_job.account_id
        else:
            fab_dict["job_details"] = None
            fab_dict["account_id"] = None

        # Add account data
        fab_dict["account_name"] = account_name
        fab_dict["account_number"] = account_number
        fab_dict["account_contact_person"] = account_contact_person
        fab_dict["account_email"] = account_email
        fab_dict["account_phone"] = account_phone
        
        # Add templating data
        fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
        fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
        fab_dict["templating_notes"] = templating_notes
        fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
        
        # Add drafter information
        fab_dict["drafter_name"] = f"{drafter_first_name} {drafter_last_name}" if drafter_first_name else None
        fab_dict["drafter_assigned_by_name"] = f"{drafter_assigned_by_first_name} {drafter_assigned_by_last_name}" if drafter_assigned_by_first_name else None
        
        # Add next_stage
        fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
        
        fabs.append(fab_dict)
    
    # Fetch fab_notes for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
    
    return success_response(fabs, f"Found {len(fabs)} of {total} FABs in stage '{stage_name}'")


@router.get("/stages", response_model=SuccessResponse[List[dict]])
async def get_all_stages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workflow stages with FAB count for each stage"""
    from sqlalchemy import func, case
    
    # Get count of FABs for each stage
    stage_counts_query = select(
        Fab.current_stage,
        func.count(Fab.id).label('count')
    ).group_by(Fab.current_stage)
    
    result = await db.execute(stage_counts_query)
    stage_counts_dict = {row[0]: row[1] for row in result.all()}
    
    # Build response with all defined stages
    stages_data = []
    for idx, stage_name in enumerate(FAB_STAGES):
        fab_count = stage_counts_dict.get(stage_name, 0)
        
        # Get last 10 FAB IDs in this stage (most recent)
        fab_ids_query = select(Fab.id).where(Fab.current_stage == stage_name).order_by(Fab.id.desc()).limit(10)
        fab_ids_result = await db.execute(fab_ids_query)
        fab_ids = [row[0] for row in fab_ids_result.all()]
        
        stages_data.append({
            "stage_name": stage_name,
            "stage_order": idx + 1,
            "fab_count": fab_count,
            "last_10_fab_ids": fab_ids,
            "next_stage": get_next_stage(stage_name)
        })
    
    # Also check for FABs in stages not in FAB_STAGES list
    all_stages_query = select(
        Fab.current_stage,
        func.count(Fab.id).label('count')
    ).where(
        Fab.current_stage.notin_(FAB_STAGES)
    ).group_by(Fab.current_stage)
    
    other_result = await db.execute(all_stages_query)
    other_stages = other_result.all()
    
    for stage_name, count in other_stages:
        if stage_name:  # Skip NULL stages
            # Get last 10 FAB IDs for this stage (most recent)
            fab_ids_query = select(Fab.id).where(Fab.current_stage == stage_name).order_by(Fab.id.desc()).limit(10)
            fab_ids_result = await db.execute(fab_ids_query)
            fab_ids = [row[0] for row in fab_ids_result.all()]
            
            stages_data.append({
                "stage_name": stage_name,
                "stage_order": None,  # Not in predefined list
                "fab_count": count,
                "last_10_fab_ids": fab_ids,
                "next_stage": get_next_stage(stage_name)
            })
    
    total_fabs = sum(stage['fab_count'] for stage in stages_data)
    
    return success_response(
        stages_data,
        f"Found {len(stages_data)} stages with {total_fabs} total FABs"
    )


async def get_draft_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get draft data for a given FAB with file URLs"""
    from src.app.database.drafting import Drafting
    from src.app.database.file import File
    from sqlalchemy.orm import aliased
    
    DrafterUser = aliased(User)
    UpdaterUser = aliased(User)
    
    query = select(
        Drafting,
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(Drafting.fab_id == fab_id)
    
    query = query.join(DrafterUser, Drafting.drafter_id == DrafterUser.id, isouter=True)
    query = query.join(UpdaterUser, Drafting.updated_by == UpdaterUser.id, isouter=True)
    query = query.order_by(Drafting.id.desc()).limit(1)  # Get latest drafting record
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return None
    
    drafting = row[0]
    drafter_first = row[1]
    drafter_last = row[2]
    updater_first = row[3]
    updater_last = row[4]
    
    # Get file information if file_ids exist
    files_data = []
    if drafting.file_ids:
        file_id_list = [int(fid.strip()) for fid in drafting.file_ids.split(",") if fid.strip()]
        
        if file_id_list:
            # Fetch all files by IDs
            files_query = select(File).where(File.id.in_(file_id_list))
            files_result = await db.execute(files_query)
            files = files_result.scalars().all()
            
            for file in files:
                # Extract filename from file_path
                filename = os.path.basename(file.file_path)
                file_url = f"{BASE_URL}/api/v1/files/download/{filename}"
                
                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                })
    
    draft_dict = {
        "id": drafting.id,
        "fab_id": drafting.fab_id,
        "drafter_id": drafting.drafter_id,
        "drafter_name": f"{drafter_first} {drafter_last}" if drafter_first else None,
        "drafter_start_date": drafting.drafter_start_date.isoformat() if drafting.drafter_start_date else None,
        "drafter_end_date": drafting.drafter_end_date.isoformat() if drafting.drafter_end_date else None,
        "total_sqft_drafted": float(drafting.total_sqft_drafted) if drafting.total_sqft_drafted else None,
        "no_of_piece_drafted": drafting.no_of_piece_drafted,
        "draft_note": drafting.draft_note,
        "mentions": drafting.mentions,
        "total_hours_drafted": float(drafting.total_hours_drafted) if drafting.total_hours_drafted else None,
        "file_ids": drafting.file_ids,
        "files": files_data,  # ← Add file details with URLs
        "status_id": drafting.status_id,
        "created_at": drafting.created_at.isoformat() if drafting.created_at else None,
        "updated_at": drafting.updated_at.isoformat() if drafting.updated_at else None,
        "updated_by": drafting.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
    }
    
    return draft_dict


async def get_sales_ct_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get Sales CT data for a given FAB with revision reason and file URLs"""
    from src.app.database.sales_ct import SalesCT
    from src.app.database.file import File
    from sqlalchemy.orm import aliased
    
    DrafterUser = aliased(User)
    UpdaterUser = aliased(User)
    
    query = select(
        SalesCT,
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(SalesCT.fab_id == fab_id)
    
    query = query.join(DrafterUser, SalesCT.drafter_id == DrafterUser.id, isouter=True)
    query = query.join(UpdaterUser, SalesCT.updated_by == UpdaterUser.id, isouter=True)
    query = query.order_by(SalesCT.id.desc()).limit(1)  # Get latest Sales CT record
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return None
    
    sales_ct = row[0]
    drafter_first = row[1]
    drafter_last = row[2]
    updater_first = row[3]
    updater_last = row[4]
    
    # Get file information if file_ids exist
    files_data = []
    if sales_ct.file_ids:
        file_id_list = [int(fid.strip()) for fid in sales_ct.file_ids.split(",") if fid.strip()]
        
        if file_id_list:
            # Fetch all files by IDs
            files_query = select(File).where(File.id.in_(file_id_list))
            files_result = await db.execute(files_query)
            files = files_result.scalars().all()
            
            for file in files:
                # Extract filename from file_path
                filename = os.path.basename(file.file_path)
                file_url = f"{BASE_URL}/api/v1/files/download/{filename}"
                
                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                })
    
    sales_ct_dict = {
        "id": sales_ct.id,
        "fab_id": sales_ct.fab_id,
        "slab_smith_type": sales_ct.slab_smith_type,
        "drafter_id": sales_ct.drafter_id,
        "drafter_name": f"{drafter_first} {drafter_last}" if drafter_first else None,
        "start_date": sales_ct.start_date.isoformat() if sales_ct.start_date else None,
        "end_date": sales_ct.end_date.isoformat() if sales_ct.end_date else None,
        "total_sqft_completed": sales_ct.total_sqft_completed,
        "is_revision_needed": sales_ct.is_revision_needed,
        "is_revision_completed": sales_ct.is_revision_completed,
        "no_of_revisions": sales_ct.no_of_revisions,
        "current_revision_count": sales_ct.current_revision_count,
        "revision_reason": sales_ct.revision_reason,  # ← Include revision reason
        "file_ids": sales_ct.file_ids,
        "files": files_data,  # ← Include file details with URLs
        "status_id": sales_ct.status_id,
        "created_at": sales_ct.created_at.isoformat() if sales_ct.created_at else None,
        "updated_at": sales_ct.updated_at.isoformat() if sales_ct.updated_at else None,
        "updated_by": sales_ct.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
    }
    
    return sales_ct_dict

