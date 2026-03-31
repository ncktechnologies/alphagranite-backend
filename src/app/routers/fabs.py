from datetime import datetime, date, timedelta
from typing import List, Optional
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.work_station import WorkStation
from src.app.database.planning_section import PlanningSection
from collections import defaultdict
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
from src.app.database.sales_ct import SalesCT
from src.app.database.status import Status
from src.app.interface.generated_schemas import ResurfaceScheduling, InstallScheduling

from src.app.interface.business_schemas import (
    FabCreate, FabUpdate, FabResponse, FabStageUpdate, ResurfaceSchedulingResponse, InstallSchedulingResponse
)
from src.app.interface.response_wrappers import SuccessResponse, error_response, success_response
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import utc_now



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
    "revision",                # Stage 11: Revisions
    "cost_of_stone",            # Stage 12: Cost of Stone
    "install_scheduling",       # Stage 13: Install Scheduling
    "install_completion"        # Stage 14: Install Completion (final stage)
]

BASE_URL = os.getenv("BASE_URL", "https://api.ag.easybusiness.ng")
PUNCHOUT_REDIRECT_FAB_TYPES = ("PUNCHOUT-AG", "PUNCHOUT-BILLABLE")

def _add_total_cut_lnft(fab_dict: dict) -> None:
    # Uses wj_linft (existing model field), with fallback to wj_lnft if present.
    saw_cut_lnft = float(fab_dict.get("saw_cut_lnft") or 0.0)
    wj_lnft = float(fab_dict.get("wj_linft") or fab_dict.get("wj_lnft") or 0.0)
    fab_dict["total_cut_lnft"] = saw_cut_lnft + wj_lnft


def _compute_fab_progress_fields(plans: List[dict]) -> tuple[Optional[str], float]:
    """
    Returns:
    - estimated_completion_date: latest scheduled end across plan stages
    - percentage_completion: average work_percentage across all plan stages
      formula: total % / total stage count
    """
    if not plans:
        return None, 0.0

    total_percent = 0.0
    stage_count = len(plans)
    latest_end_dt: Optional[datetime] = None

    for p in plans:
        # percentage completion per stage (None treated as 0)
        wp = p.get("work_percentage")
        total_percent += float(wp) if wp is not None else 0.0

        # scheduled end = scheduled_start_date + estimated_hours
        candidate_end: Optional[datetime] = None
        scheduled_start = p.get("scheduled_start_date")
        estimated_hours = p.get("estimated_hours")

        if scheduled_start:
            try:
                start_dt = datetime.fromisoformat(scheduled_start)
                if estimated_hours is not None:
                    candidate_end = start_dt + timedelta(hours=float(estimated_hours))
                else:
                    candidate_end = start_dt
            except Exception:
                candidate_end = None

        # fallback to actual_end_date if needed
        if candidate_end is None and p.get("actual_end_date"):
            try:
                candidate_end = datetime.fromisoformat(p["actual_end_date"])
            except Exception:
                candidate_end = None

        if candidate_end and (latest_end_dt is None or candidate_end > latest_end_dt):
            latest_end_dt = candidate_end

    avg_percent = round((total_percent / stage_count), 2) if stage_count > 0 else 0.0
    estimated_completion_date = latest_end_dt.isoformat() if latest_end_dt else None
    return estimated_completion_date, avg_percent

def _stage_filter_condition(stage_name: str):
    """
    Stage visibility rule:
    - install_completion includes:
      1) FABs whose current_stage is install_completion
      2) FABs still in cut_list but already having shop_est_completion_date
    - all other stages use exact stage match
    """
    if stage_name == "install_completion":
        return or_(
            Fab.current_stage == "install_completion",
            and_(
                Fab.current_stage == "cut_list",
                Fab.shop_est_completion_date.isnot(None),
            ),
        )
    if stage_name == "install_scheduling":
        return and_(
            Fab.current_stage == "install_scheduling",
            ~Fab.fab_type.in_(PUNCHOUT_REDIRECT_FAB_TYPES),
        )
    return Fab.current_stage == stage_name


def _needs_slabsmith(
    slab_smith_ag_needed: Optional[bool] = None,
    slab_smith_cust_needed: Optional[bool] = None,
) -> bool:
    return bool(slab_smith_ag_needed) or bool(slab_smith_cust_needed)

def get_next_stage(
    current_stage: str,
    drafting_needed: Optional[bool] = None,
    slab_smith_ag_needed: Optional[bool] = None,
    slab_smith_cust_needed: Optional[bool] = None,
) -> Optional[str]:
    if not current_stage:
        return "templating"

    if current_stage == "pre_draft_review":
        # Skip drafting when it is explicitly not needed.
        return "sales_ct" if drafting_needed is False else "drafting"

    if current_stage == "drafting":
        return "sales_ct"

    if current_stage == "sales_ct":
        needs_slabsmith = _needs_slabsmith(slab_smith_ag_needed, slab_smith_cust_needed)
        return "slab_smith_request" if needs_slabsmith else "final_programming"

    try:
        current_index = FAB_STAGES.index(current_stage)
        next_index = current_index + 1
        return FAB_STAGES[next_index] if next_index < len(FAB_STAGES) else None
    except ValueError:
        return "templating"


async def get_plans_map_for_fabs(db: AsyncSession, fab_ids: List[int]) -> dict[int, list[dict]]:
    if not fab_ids:
        return {}

    q = (
        select(
            ShopCutPlan,
            Fab.fab_type.label("fab_type"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("plan_name"),
            User.first_name.label("operator_first_name"),
            User.last_name.label("operator_last_name"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .join(User, User.id == ShopCutPlan.user_id, isouter=True)
        .where(ShopCutPlan.fab_id.in_(fab_ids))
        .order_by(ShopCutPlan.fab_id, ShopCutPlan.id.desc())
    )
    rows = (await db.execute(q)).all()

    plans_map: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        p = row[0]
        plans_map[p.fab_id].append({
            "id": p.id,
            "fab_id": p.fab_id,
            "fab_type": row.fab_type,
            "sequence": p.sequence,
            "workstation_id": p.workstation_id,
            "workstation_name": row.workstation_name,
            "planning_section_id": p.planning_section_id,
            "plan_name": row.plan_name,
            "operator_id": p.user_id,
            "operator_name": (
                f"{row.operator_first_name} {row.operator_last_name}".strip()
                if row.operator_first_name else None
            ),
            "estimated_hours": p.estimated_hours,
            "scheduled_start_date": p.scheduled_start_date.isoformat() if p.scheduled_start_date else None,
            "actual_start_date": p.actual_start_date.isoformat() if p.actual_start_date else None,
            "actual_end_date": p.actual_end_date.isoformat() if p.actual_end_date else None,
            "work_percentage": p.work_percentage,
            "notes": p.notes,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    return plans_map


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
            technician = await db.get(User, templating.technician_id) if templating.technician_id else None
            status = await db.get(Status, templating.status_id) if templating.status_id else None

            stage_info["is_complete"] = templating.is_completed
            stage_info["stage_data"] = {
                "templating_id": templating.id,
                "technician_id": templating.technician_id,
                "technician_name": f"{technician.first_name} {technician.last_name}" if technician else None,
                "schedule_start_date": templating.schedule_start_date.isoformat() if templating.schedule_start_date else None,
                "schedule_due_date": templating.schedule_due_date.isoformat() if templating.schedule_due_date else None,
                "actual_start_date": templating.actual_start_date.isoformat() if templating.actual_start_date else None,
                "duration": templating.duration,
                "total_sqft": templating.total_sqft,
                "notes": templating.notes,
                "is_templating_schedule": templating.is_templating_schedule,
                "is_completed": templating.is_completed,
                "rescheduled": templating.rescheduled,
                "status_id": templating.status_id,
                "status_name": status.name if status else None,
                "created_at": templating.created_at.isoformat() if templating.created_at else None,
                "updated_at": templating.updated_at.isoformat() if templating.updated_at else None,
                "updated_by": templating.updated_by
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
    
    # Cost of stone validation (if provided)
    if fab_data.cost_of_stone_id:
        from src.app.database.cost_of_stone import CostOfStone
        cost_stone = await db.get(CostOfStone, fab_data.cost_of_stone_id)
        if not cost_stone:
            return error_response("Cost of stone record not found", 404)
    
    # Create the fab and start it at templating stage (or resurface_scheduling if fab_type is RESURFACE)
    fab_dict = fab_data.model_dump()
    
    # Set default total_sqft to 1 if not provided (as per client requirement)
    if "total_sqft" not in fab_dict or fab_dict["total_sqft"] is None:
        fab_dict["total_sqft"] = 1.0
    
    # Determine initial stage based on fab_type and workflow flags.
    fab_type = (fab_dict.get("fab_type") or "").strip().upper()
    fab_dict["fab_type"] = fab_type  # persist uppercase globally

    if fab_type in PUNCHOUT_REDIRECT_FAB_TYPES:
        # Punchout FABs should be handled via the shop-est-completion flow,
        # not shown in install_scheduling lists.
        current_stage = "cut_list"
        next_stage = get_next_stage("cut_list")
    elif fab_type == "RESURFACE":
        current_stage = "resurface_scheduling"
        next_stage = get_next_stage("resurface_scheduling")
    else:
        # If all workflow-required flags are false, skip directly to Cut List.
        if (
            fab_dict.get("template_needed") is False
            and fab_dict.get("drafting_needed") is False
            and fab_dict.get("sct_needed") is False
            and fab_dict.get("final_programming_needed") is False
        ):
            current_stage = "cut_list"
            next_stage = get_next_stage(
                "cut_list",
                drafting_needed=fab_dict.get("drafting_needed"),
                slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
                slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
            )
        # Skip templating when template is not needed
        elif fab_dict.get("template_needed") is False:
            current_stage = "pre_draft_review"
            next_stage = get_next_stage(
                "pre_draft_review",
                drafting_needed=fab_dict.get("drafting_needed"),
                slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
                slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
            )
        else:
            current_stage = "templating"
            next_stage = get_next_stage(
                "templating",
                drafting_needed=fab_dict.get("drafting_needed"),
                slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
                slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
            )
    
    fab = Fab(
        **fab_dict,
        current_stage=current_stage,
        next_stage=next_stage,
        status_id=1,
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
    templater_id: Optional[int] = Query(None, description="Filter by templater/technician ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
    next_stage: Optional[str] = Query(None, description="Filter by next stage"),
    schedule_start_date: Optional[date] = Query(None, description="Filter FABs scheduled on or after this date (YYYY-MM-DD)"),
    schedule_due_date: Optional[date] = Query(None, description="Filter FABs scheduled on or before this date (YYYY-MM-DD)"),
    schedule_status: Optional[str] = Query(None, description="Filter by schedule status: scheduled or unscheduled"),
    date_filter: Optional[str] = Query(None, description="Predefined date filter: today, this_week, last_week, this_month, last_month, next_week, next_month"),
    shop_date_start: Optional[date] = Query(None, description="Filter by shop_date_schedule on or after this date (YYYY-MM-DD)"),
    shop_date_end: Optional[date] = Query(None, description="Filter by shop_date_schedule on or before this date (YYYY-MM-DD)"),
    template_completed_start: Optional[date] = Query(None, description="Filter by template_completed_date on or after this date (YYYY-MM-DD)"),
    template_completed_end: Optional[date] = Query(None, description="Filter by template_completed_date on or before this date (YYYY-MM-DD)"),
    predraft_completed_start: Optional[date] = Query(None, description="Filter by predraft_completed_date on or after this date (YYYY-MM-DD)"),
    predraft_completed_end: Optional[date] = Query(None, description="Filter by predraft_completed_date on or before this date (YYYY-MM-DD)"),
    draft_completed_start: Optional[date] = Query(None, description="Filter by draft_completed_date on or after this date (YYYY-MM-DD)"),
    draft_completed_end: Optional[date] = Query(None, description="Filter by draft_completed_date on or before this date (YYYY-MM-DD)"),
    sct_completed_start: Optional[date] = Query(None, description="Filter by sct_completed_date on or after this date (YYYY-MM-DD)"),  # NEW
    sct_completed_end: Optional[date] = Query(None, description="Filter by sct_completed_date on or before this date (YYYY-MM-DD)"),  # NEW
    search: Optional[str] = Query(None, description="Search value"),
    type: Optional[str] = Query(None, description="Field to apply search to: fab_id, job_number, job_name"),  # NEW
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fabs with optional filtering and pagination"""

    # Step 1: Apply templating filters to get FAB IDs
    templating_fab_ids = await _apply_templating_filters(
        db,
        templater_id,
        schedule_start_date,
        schedule_due_date,
        schedule_status,
        date_filter if current_stage == "templating" else None
    )

    if templating_fab_ids is not None and len(templating_fab_ids) == 0:
        return {
            "success": True,
            "message": "FABs retrieved successfully",
            "data": {"total": 0, "page": 1, "per_page": limit, "data": []}
        }

    # Step 2: Build latest templating subquery
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )

    # Step 3: Build main query
    # Build search filter based on type
    search_filter = None
    if search and type:
        if type == "fab_id":
            search_filter = sa.cast(Fab.id, sa.String) == search
        elif type == "job_number":
            search_filter = BusinessJob.job_number == search
        elif type == "job_name":
            search_filter = BusinessJob.name.ilike(f"%{search}%")
    else:
        search_filter = None

    query = _build_fab_list_query(
        job_id, fab_type, sales_person_id, status_id, current_stage, next_stage,
        None,  # search is handled below
        templating_fab_ids, latest_templating, shop_date_start, shop_date_end,
        template_completed_start, template_completed_end, predraft_completed_start, predraft_completed_end,
        draft_completed_start, draft_completed_end, sct_completed_start, sct_completed_end,
        date_filter
    )

    # Apply search filter if present
    if search_filter is not None:
        query = query.where(search_filter)
    elif search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search,
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number == search
            )
        )

    # Step 4: Apply pagination and ordering
    query = _apply_pagination_and_ordering(query, skip, limit, current_stage, latest_templating)

    result = await db.execute(query)
    rows = result.all()

    # Step 5: Convert rows to dictionaries
    fabs = [_convert_fab_row_to_dict(row) for row in rows]

    # Step 6: Batch load related data
    await _batch_load_fab_related_data(db, fabs)

    # Step 6.1: Batch load plans and attach per FAB
    fab_ids = [f["id"] for f in fabs]
    plans_map = await get_plans_map_for_fabs(db, fab_ids)
    for f in fabs:
        plans = plans_map.get(f["id"], [])
        f["plans"] = plans

        # NEW computed fields
        estimated_completion_date, percentage_completion = _compute_fab_progress_fields(plans)
        f["estimated_completion_date"] = estimated_completion_date
        f["percentage_completion"] = percentage_completion

    # Step 6.2: Batch load resurface scheduling and attach per FAB
    resurface_scheduling_map = await _batch_load_resurface_scheduling_responses(db, fab_ids)
    for f in fabs:
        f["resurface_scheduling"] = resurface_scheduling_map.get(f["id"])

    # Step 6.3: Batch load install scheduling and attach per FAB
    install_scheduling_map = await _batch_load_install_scheduling_responses(db, fab_ids)
    for f in fabs:
        f["install_details"] = install_scheduling_map.get(f["id"])

    # Step 7: Get total count with stage-specific date filtering
    count_query = select(func.count(Fab.id)).select_from(Fab)
    count_query = count_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
    count_query = count_query.outerjoin(latest_templating, sa.literal(True))

    # Apply all basic filters to count query
    if job_id is not None:
        count_query = count_query.where(Fab.job_id == job_id)
    if fab_type:
        count_query = count_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        count_query = count_query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        count_query = count_query.where(Fab.status_id == status_id)
    if current_stage:
        count_query = count_query.where(_stage_filter_condition(current_stage))
    if next_stage:
        count_query = count_query.where(Fab.next_stage == next_stage)

    # Apply stage-specific date filtering to count
    if current_stage:
        if current_stage == "pre_draft_review":
            date_start, date_end = template_completed_start, template_completed_end
        elif current_stage == "templating":
            date_start, date_end = schedule_start_date, schedule_due_date
        elif current_stage == "drafting":
            date_start, date_end = predraft_completed_start, predraft_completed_end
        elif current_stage == "sales_ct":
            date_start, date_end = draft_completed_start, draft_completed_end
        elif current_stage == "revision":
            date_start, date_end = sct_completed_start, sct_completed_end
        elif current_stage == "cut_list":
            date_start, date_end = shop_date_start, shop_date_end
        else:
            date_start, date_end = None, None

        count_query = _apply_stage_specific_date_filter(
            count_query, current_stage, date_filter, date_start, date_end
        )
    else:
        # Apply all date filters when no specific stage
        if shop_date_start:
            count_query = count_query.where(Fab.shop_date_schedule >= shop_date_start)
        if shop_date_end:
            count_query = count_query.where(Fab.shop_date_schedule <= shop_date_end)
        if template_completed_start:
            count_query = count_query.where(Fab.template_completed_date >= template_completed_start)
        if template_completed_end:
            count_query = count_query.where(Fab.template_completed_date <= template_completed_end)
        if predraft_completed_start:
            count_query = count_query.where(Fab.predraft_completed_date >= predraft_completed_start)
        if predraft_completed_end:
            count_query = count_query.where(Fab.predraft_completed_date <= predraft_completed_end)
        if draft_completed_start:
            count_query = count_query.where(Fab.draft_completed_date >= draft_completed_start)
        if draft_completed_end:
            count_query = count_query.where(Fab.draft_completed_date <= draft_completed_end)
        if sct_completed_start:
            count_query = count_query.where(Fab.sct_completed_date >= sct_completed_start)
        if sct_completed_end:
            count_query = count_query.where(Fab.sct_completed_date <= sct_completed_end)

    # Apply search filter to count query
    if search_filter is not None:
        count_query = count_query.where(search_filter)
    elif search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search,
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number == search
            )
        )

    if templating_fab_ids is not None:
        count_query = count_query.where(Fab.id.in_(templating_fab_ids))
    elif schedule_status == "unscheduled":
        count_query = count_query.where(
            or_(
                ~Fab.id.in_(select(Templating.fab_id)),
                Fab.id.in_(select(Templating.fab_id).where(Templating.schedule_start_date.is_(None)))
            )
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Step 8: Calculate stage totals if needed
    stage_totals = None
    if current_stage:
        stage_totals_query = select(
            func.sum(Fab.total_sqft).label("total_sqft"),
            func.sum(Fab.wj_linft).label("wj_linft"),
            func.sum(Fab.edging_linft).label("edging_linft"),
            func.sum(Fab.cnc_linft).label("cnc_linft"),
            func.sum(Fab.miter_linft).label("miter_linft"),
            func.sum(Fab.saw_cut_lnft).label("saw_cut_lnft"),
            func.sum(Fab.no_of_pieces).label("no_of_pieces")
        ).select_from(Fab).where(_stage_filter_condition(current_stage))

        # Apply same basic filters
        if job_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.job_id == job_id)
        if fab_type:
            stage_totals_query = stage_totals_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
        if sales_person_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.sales_person_id == sales_person_id)
        if status_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.status_id == status_id)

        # Apply stage-specific date filters (same as count_query)
        if current_stage == "pre_draft_review":
            date_start, date_end = template_completed_start, template_completed_end
        elif current_stage == "templating":
            date_start, date_end = schedule_start_date, schedule_due_date
        elif current_stage == "drafting":
            date_start, date_end = predraft_completed_start, predraft_completed_end
        elif current_stage == "sales_ct":
            date_start, date_end = draft_completed_start, draft_completed_end
        elif current_stage == "revision":
            date_start, date_end = sct_completed_start, sct_completed_end
        elif current_stage == "cut_list":
            date_start, date_end = shop_date_start, shop_date_end
        else:
            date_start, date_end = None, None

        # Apply the same stage-specific date filter
        stage_totals_query = _apply_stage_specific_date_filter(
            stage_totals_query, current_stage, date_filter, date_start, date_end
        )

        # Apply search filter to stage totals query
        if search_filter is not None:
            stage_totals_query = stage_totals_query.where(search_filter)
        elif search:
            search_term = f"%{search}%"
            stage_totals_query = stage_totals_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
            stage_totals_query = stage_totals_query.where(
                or_(
                    sa.cast(Fab.id, sa.String) == search,
                    BusinessJob.name.ilike(search_term),
                    BusinessJob.job_number == search
                )
            )

        totals_result = await db.execute(stage_totals_query)
        totals_row = totals_result.first()

        if totals_row:
            stage_totals = {
                "stage": current_stage,
                "total_sqft": float(totals_row[0]) if totals_row[0] else 0.0,
                "wj_linft": float(totals_row[1]) if totals_row[1] else 0.0,
                "edging_linft": float(totals_row[2]) if totals_row[2] else 0.0,
                "cnc_linft": float(totals_row[3]) if totals_row[3] else 0.0,
                "miter_linft": float(totals_row[4]) if totals_row[4] else 0.0,
                "saw_cut_lnft": float(totals_row[5]) if totals_row[5] else 0.0,
                "no_of_pieces": int(totals_row[6]) if totals_row[6] else 0
            }

    # Step 9: Build response
    page = (skip // limit) + 1 if limit > 0 else 1
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "data": fabs
    }

    if stage_totals:
        response_data["stage_totals"] = stage_totals

    return {
        "success": True,
        "message": "FABs retrieved successfully",
        "data": response_data
    }


@router.get("/fabs/shop-est-completion")
async def get_fabs_with_shop_est_completion(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    fab_type: Optional[str] = Query(None, description="Filter by fab type"),
    sales_person_id: Optional[int] = Query(None, description="Filter by sales person ID"),
    templater_id: Optional[int] = Query(None, description="Filter by templater/technician ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
    next_stage: Optional[str] = Query(None, description="Filter by next stage"),
    schedule_start_date: Optional[date] = Query(None, description="Filter FABs scheduled on or after this date (YYYY-MM-DD)"),
    schedule_due_date: Optional[date] = Query(None, description="Filter FABs scheduled on or before this date (YYYY-MM-DD)"),
    schedule_status: Optional[str] = Query(None, description="Filter by schedule status: scheduled or unscheduled"),
    date_filter: Optional[str] = Query(None, description="Predefined date filter: today, this_week, last_week, this_month, last_month, next_week, next_month"),
    shop_date_start: Optional[date] = Query(None, description="Filter by shop_date_schedule on or after this date (YYYY-MM-DD)"),
    shop_date_end: Optional[date] = Query(None, description="Filter by shop_date_schedule on or before this date (YYYY-MM-DD)"),
    template_completed_start: Optional[date] = Query(None, description="Filter by template_completed_date on or after this date (YYYY-MM-DD)"),
    template_completed_end: Optional[date] = Query(None, description="Filter by template_completed_date on or before this date (YYYY-MM-DD)"),
    predraft_completed_start: Optional[date] = Query(None, description="Filter by predraft_completed_date on or after this date (YYYY-MM-DD)"),
    predraft_completed_end: Optional[date] = Query(None, description="Filter by predraft_completed_date on or before this date (YYYY-MM-DD)"),
    draft_completed_start: Optional[date] = Query(None, description="Filter by draft_completed_date on or after this date (YYYY-MM-DD)"),
    draft_completed_end: Optional[date] = Query(None, description="Filter by draft_completed_date on or before this date (YYYY-MM-DD)"),
    sct_completed_start: Optional[date] = Query(None, description="Filter by sct_completed_date on or after this date (YYYY-MM-DD)"),
    sct_completed_end: Optional[date] = Query(None, description="Filter by sct_completed_date on or before this date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search value"),
    type: Optional[str] = Query(None, description="Field to apply search to: fab_id, job_number, job_name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of FABs that have a shop_est_completion_date set, with full FAB details."""

    # Step 1: Apply templating filters to get FAB IDs
    templating_fab_ids = await _apply_templating_filters(
        db,
        templater_id,
        schedule_start_date,
        schedule_due_date,
        schedule_status,
        date_filter if current_stage == "templating" else None
    )

    if templating_fab_ids is not None and len(templating_fab_ids) == 0:
        return {
            "success": True,
            "message": "FABs retrieved successfully",
            "data": {"total": 0, "page": 1, "per_page": limit, "data": []}
        }

    # Step 2: Build latest templating subquery
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )

    # Step 3: Build main query
    search_filter = None
    search_value = search.strip() if isinstance(search, str) else search
    search_type = type.strip().lower() if isinstance(type, str) else None
    if search_value and search_type:
        if search_type == "fab_id":
            search_filter = sa.cast(Fab.id, sa.String) == search_value
        elif search_type == "job_number":
            search_filter = sa.cast(BusinessJob.job_number, sa.String) == search_value
        elif search_type == "job_name":
            search_filter = BusinessJob.name.ilike(f"%{search_value}%")

    query = _build_fab_list_query(
        job_id, fab_type, sales_person_id, status_id, current_stage, next_stage,
        None,  # search is handled below
        templating_fab_ids, latest_templating, shop_date_start, shop_date_end,
        template_completed_start, template_completed_end, predraft_completed_start, predraft_completed_end,
        draft_completed_start, draft_completed_end, sct_completed_start, sct_completed_end,
        date_filter
    )

    # Include records that already have shop_est_completion_date or belong to
    # punchout FAB types that should be handled in this endpoint.
    shop_est_or_punchout_filter = or_(
        Fab.shop_est_completion_date.isnot(None),
        Fab.fab_type.in_(PUNCHOUT_REDIRECT_FAB_TYPES),
    )
    query = query.where(shop_est_or_punchout_filter)

    # Apply search filter if present
    if search_filter is not None:
        query = query.where(search_filter)
    elif search_value:
        search_term = f"%{search_value}%"
        query = query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search_value,
                BusinessJob.name.ilike(search_term),
                sa.cast(BusinessJob.job_number, sa.String) == search_value
            )
        )

    # Step 4: Apply pagination and ordering
    query = _apply_pagination_and_ordering(query, skip, limit, current_stage, latest_templating)

    result = await db.execute(query)
    rows = result.all()

    # Step 5: Convert rows to dictionaries
    fabs = [_convert_fab_row_to_dict(row) for row in rows]

    # Step 6: Batch load related data
    await _batch_load_fab_related_data(db, fabs)

    # Step 6.1: Batch load plans and attach per FAB
    fab_ids = [f["id"] for f in fabs]
    plans_map = await get_plans_map_for_fabs(db, fab_ids)
    for f in fabs:
        plans = plans_map.get(f["id"], [])
        f["plans"] = plans

        estimated_completion_date, percentage_completion = _compute_fab_progress_fields(plans)
        f["estimated_completion_date"] = estimated_completion_date
        f["percentage_completion"] = percentage_completion

    # Step 7: Get total count
    count_query = select(func.count(Fab.id)).select_from(Fab)
    count_query = count_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
    count_query = count_query.outerjoin(latest_templating, sa.literal(True))

    count_query = count_query.where(shop_est_or_punchout_filter)

    # Apply all basic filters to count query
    if job_id is not None:
        count_query = count_query.where(Fab.job_id == job_id)
    if fab_type:
        count_query = count_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        count_query = count_query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        count_query = count_query.where(Fab.status_id == status_id)
    if current_stage:
        count_query = count_query.where(_stage_filter_condition(current_stage))
    if next_stage:
        count_query = count_query.where(Fab.next_stage == next_stage)

    # Apply stage-specific date filtering to count
    if current_stage:
        if current_stage == "pre_draft_review":
            date_start, date_end = template_completed_start, template_completed_end
        elif current_stage == "templating":
            date_start, date_end = schedule_start_date, schedule_due_date
        elif current_stage == "drafting":
            date_start, date_end = predraft_completed_start, predraft_completed_end
        elif current_stage == "sales_ct":
            date_start, date_end = draft_completed_start, draft_completed_end
        elif current_stage == "revision":
            date_start, date_end = sct_completed_start, sct_completed_end
        elif current_stage == "cut_list":
            date_start, date_end = shop_date_start, shop_date_end
        else:
            date_start, date_end = None, None

        count_query = _apply_stage_specific_date_filter(
            count_query, current_stage, date_filter, date_start, date_end
        )
    else:
        if shop_date_start:
            count_query = count_query.where(Fab.shop_date_schedule >= shop_date_start)
        if shop_date_end:
            count_query = count_query.where(Fab.shop_date_schedule <= shop_date_end)
        if template_completed_start:
            count_query = count_query.where(Fab.template_completed_date >= template_completed_start)
        if template_completed_end:
            count_query = count_query.where(Fab.template_completed_date <= template_completed_end)
        if predraft_completed_start:
            count_query = count_query.where(Fab.predraft_completed_date >= predraft_completed_start)
        if predraft_completed_end:
            count_query = count_query.where(Fab.predraft_completed_date <= predraft_completed_end)
        if draft_completed_start:
            count_query = count_query.where(Fab.draft_completed_date >= draft_completed_start)
        if draft_completed_end:
            count_query = count_query.where(Fab.draft_completed_date <= draft_completed_end)
        if sct_completed_start:
            count_query = count_query.where(Fab.sct_completed_date >= sct_completed_start)
        if sct_completed_end:
            count_query = count_query.where(Fab.sct_completed_date <= sct_completed_end)

    if search_filter is not None:
        count_query = count_query.where(search_filter)
    elif search_value:
        search_term = f"%{search_value}%"
        count_query = count_query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search_value,
                BusinessJob.name.ilike(search_term),
                sa.cast(BusinessJob.job_number, sa.String) == search_value
            )
        )

    if templating_fab_ids is not None:
        count_query = count_query.where(Fab.id.in_(templating_fab_ids))
    elif schedule_status == "unscheduled":
        count_query = count_query.where(
            or_(
                ~Fab.id.in_(select(Templating.fab_id)),
                Fab.id.in_(select(Templating.fab_id).where(Templating.schedule_start_date.is_(None)))
            )
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Step 8: Calculate stage totals if needed
    stage_totals = None
    if current_stage:
        stage_totals_query = select(
            func.sum(Fab.total_sqft).label("total_sqft"),
            func.sum(Fab.wj_linft).label("wj_linft"),
            func.sum(Fab.edging_linft).label("edging_linft"),
            func.sum(Fab.cnc_linft).label("cnc_linft"),
            func.sum(Fab.miter_linft).label("miter_linft"),
            func.sum(Fab.saw_cut_lnft).label("saw_cut_lnft"),
            func.sum(Fab.no_of_pieces).label("no_of_pieces")
        ).select_from(Fab).where(_stage_filter_condition(current_stage))

        stage_totals_query = stage_totals_query.where(shop_est_or_punchout_filter)

        if job_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.job_id == job_id)
        if fab_type:
            stage_totals_query = stage_totals_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
        if sales_person_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.sales_person_id == sales_person_id)
        if status_id is not None:
            stage_totals_query = stage_totals_query.where(Fab.status_id == status_id)

        if current_stage == "pre_draft_review":
            date_start, date_end = template_completed_start, template_completed_end
        elif current_stage == "templating":
            date_start, date_end = schedule_start_date, schedule_due_date
        elif current_stage == "drafting":
            date_start, date_end = predraft_completed_start, predraft_completed_end
        elif current_stage == "sales_ct":
            date_start, date_end = draft_completed_start, draft_completed_end
        elif current_stage == "revision":
            date_start, date_end = sct_completed_start, sct_completed_end
        elif current_stage == "cut_list":
            date_start, date_end = shop_date_start, shop_date_end
        else:
            date_start, date_end = None, None

        stage_totals_query = _apply_stage_specific_date_filter(
            stage_totals_query, current_stage, date_filter, date_start, date_end
        )

        if search_filter is not None:
            stage_totals_query = stage_totals_query.where(search_filter)
        elif search_value:
            search_term = f"%{search_value}%"
            stage_totals_query = stage_totals_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
            stage_totals_query = stage_totals_query.where(
                or_(
                    sa.cast(Fab.id, sa.String) == search_value,
                    BusinessJob.name.ilike(search_term),
                    sa.cast(BusinessJob.job_number, sa.String) == search_value
                )
            )

        totals_result = await db.execute(stage_totals_query)
        totals_row = totals_result.first()

        if totals_row:
            stage_totals = {
                "stage": current_stage,
                "total_sqft": float(totals_row[0]) if totals_row[0] else 0.0,
                "wj_linft": float(totals_row[1]) if totals_row[1] else 0.0,
                "edging_linft": float(totals_row[2]) if totals_row[2] else 0.0,
                "cnc_linft": float(totals_row[3]) if totals_row[3] else 0.0,
                "miter_linft": float(totals_row[4]) if totals_row[4] else 0.0,
                "saw_cut_lnft": float(totals_row[5]) if totals_row[5] else 0.0,
                "no_of_pieces": int(totals_row[6]) if totals_row[6] else 0
            }

    # Step 9: Build response
    page = (skip // limit) + 1 if limit > 0 else 1
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "data": fabs
    }

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
    fab_dict["next_stage"] = get_next_stage(
        fab_dict.get("current_stage"),
        drafting_needed=fab_dict.get("drafting_needed"),
        slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
        slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
    )
    
    _add_total_cut_lnft(fab_dict)

    # Fetch fab_notes
    fab_notes = await get_fab_notes(db, fab_id)
    fab_dict["fab_notes"] = fab_notes
    
    # Fetch draft data
    draft_data = await get_draft_data(db, fab_id)
    fab_dict["draft_data"] = draft_data

    # Fetch CNC data
    cnc_data = await get_cnc_data(db, fab_id)
    fab_dict["cnc_data"] = cnc_data
    
    # Fetch Sales CT data
    sales_ct_data = await get_sales_ct_data(db, fab_id)
    fab_dict["sales_ct_data"] = sales_ct_data
    
    # Fetch SlabSmith data
    slabsmith_data = await get_slabsmith_data(db, fab_id)
    fab_dict["slabsmith_data"] = slabsmith_data
    
    # Fetch latest revision
    revisions = await _batch_load_latest_revisions(db, [fab_id])
    fab_dict["latest_revision"] = revisions.get(fab_id)
    
    # Fetch drafting session
    sessions = await _batch_load_drafting_sessions(db, [fab_id])
    fab_dict["drafting_session"] = sessions.get(fab_id)
    
    # Add stage completion status and stage-specific data
    stage_info = await get_stage_completion_data(db, fab_id, fab_dict.get("current_stage"))
    fab_dict["is_complete"] = stage_info["is_complete"]
    fab_dict["stage_data"] = stage_info["stage_data"]
    
    # Attach plans for this FAB
    plans_map = await get_plans_map_for_fabs(db, [fab_id])
    fab_dict["plans"] = plans_map.get(fab_id, [])
    
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
    if fab_data.drafter_id and fab.data.drafter_id != fab.drafter_id:
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
        fab.next_stage = get_next_stage(
            new_current_stage,
            drafting_needed=fab.drafting_needed,
            slab_smith_ag_needed=fab.slab_smith_ag_needed,
            slab_smith_cust_needed=getattr(fab, "slab_smith_cust_needed", None),
        )
    
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
        fab_dict["next_stage"] = get_next_stage(
            fab_dict.get("current_stage"),
            drafting_needed=fab_dict.get("drafting_needed"),
            slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
            slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
        )        
        fabs.append(fab_dict)
    
    # Fetch fab_notes for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
        
        # Fetch draft data
        draft_data = await get_draft_data(db, fab_dict["id"])
        fab_dict["draft_data"] = draft_data

        # Fetch CNC data
        cnc_data = await get_cnc_data(db, fab_dict["id"])
        fab_dict["cnc_data"] = cnc_data
        
        # Fetch Sales CT data
        sales_ct_data = await get_sales_ct_data(db, fab_dict["id"])
        fab_dict["sales_ct_data"] = sales_ct_data
    
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
    from sqlalchemy import and_, func, or_
    
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
    if stage_name == "install_scheduling":
        query = query.where(
            or_(
                and_(
                    Fab.current_stage == "install_scheduling",
                    ~Fab.fab_type.in_(PUNCHOUT_REDIRECT_FAB_TYPES),
                ),
                and_(
                    Fab.current_stage == "resurface_scheduling",
                    Fab.shop_date_schedule.isnot(None),
                ),
            )
        )
    else:
        query = query.where(Fab.current_stage == stage_name)
    
    # Apply optional filters
    if job_id:
        query = query.where(Fab.job_id == job_id)
    if status_id:
        query = query.where(Fab.status_id == status_id)
    
    # Get total count before pagination
    if stage_name == "install_scheduling":
        count_query = select(func.count()).select_from(Fab).where(
            or_(
                and_(
                    Fab.current_stage == "install_scheduling",
                    ~Fab.fab_type.in_(PUNCHOUT_REDIRECT_FAB_TYPES),
                ),
                and_(
                    Fab.current_stage == "resurface_scheduling",
                    Fab.shop_date_schedule.isnot(None),
                ),
            )
        )
    else:
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
        fab_dict["next_stage"] = get_next_stage(
            fab_dict.get("current_stage"),
            drafting_needed=fab_dict.get("drafting_needed"),
            slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
            slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
        )        
        fabs.append(fab_dict)
    
    # Fetch fab_notes for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
        
        # Fetch draft data
        draft_data = await get_draft_data(db, fab_dict["id"])
        fab_dict["draft_data"] = draft_data

        # Fetch CNC data
        cnc_data = await get_cnc_data(db, fab_dict["id"])
        fab_dict["cnc_data"] = cnc_data
        
        # Fetch Sales CT data
        sales_ct_data = await get_sales_ct_data(db, fab_dict["id"])
        fab_dict["sales_ct_data"] = sales_ct_data
    
    return success_response(fabs, f"Found {len(fabs)} FABs in stage '{stage_name}'")


@router.get("/stages/final_programming/pending", response_model=SuccessResponse[dict])
async def get_pending_final_programming_fabs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    shop_date_start: Optional[date] = Query(None, description="Filter by shop_date_schedule on or after this date (YYYY-MM-DD)"),  # NEW
    shop_date_end: Optional[date] = Query(None, description="Filter by shop_date_schedule on or before this date (YYYY-MM-DD)"),  # NEW
    fab_type: Optional[str] = Query(None, description="Filter by fab type"),  # NEW
    search: Optional[str] = Query(None, description="Search by FAB ID or Job Name"),  # NEW
    type: Optional[str] = Query(None, description="Field to apply search to: fab_id, job_number, job_name"),  # NEW
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get FABs that should be in final programming stage.
    
    Criteria:
    - current_stage == "final_programming" OR
    - (current_stage == "cut_list" AND shop_date_schedule IS NOT NULL AND final_programming_complete == False)
    
    Supports filtering by:
    - shop_date_schedule date range
    - fab_type
    - search (FAB ID or Job Name)
    """
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_, or_, func
    
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
    
    # Apply final programming criteria
    query = query.where(
        or_(
            Fab.current_stage == "final_programming",
            and_(
                Fab.current_stage == "cut_list",
                Fab.shop_date_schedule.isnot(None),
                Fab.final_programming_complete == False
            )
        )
    )
    
    # Apply optional filters
    if job_id:
        query = query.where(Fab.job_id == job_id)
    if status_id:
        query = query.where(Fab.status_id == status_id)
    
    # NEW: Apply shop_date_schedule date range filters
    if shop_date_start:
        query = query.where(Fab.shop_date_schedule >= shop_date_start)
    if shop_date_end:
        query = query.where(Fab.shop_date_schedule <= shop_date_end)
    
    # NEW: Apply fab_type filter
    if fab_type:
        query = query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    
    # NEW: Build search filter based on type
    if search and type:
        if type == "fab_id":
            search_filter = sa.cast(Fab.id, sa.String) == search
        elif type == "job_number":
            search_filter = BusinessJob.job_number == search
        elif type == "job_name":
            search_filter = BusinessJob.name.ilike(f"%{search}%")
        else:
            search_filter = None
    else:
        search_filter = None

    if search_filter is not None:
        query = query.where(search_filter)
    elif search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search,
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number == search
            )
        )
    
    # Get total count before pagination
    count_query = select(func.count()).select_from(Fab).where(
        or_(
            Fab.current_stage == "final_programming",
            and_(
                Fab.current_stage == "cut_list",
                Fab.shop_date_schedule.isnot(None),
                Fab.final_programming_complete == False
            )
        )
    )
    if job_id:
        count_query = count_query.where(Fab.job_id == job_id)
    if status_id:
        count_query = count_query.where(Fab.status_id == status_id)
    if shop_date_start:
        count_query = count_query.where(Fab.shop_date_schedule >= shop_date_start)
    if shop_date_end:
        count_query = count_query.where(Fab.shop_date_schedule <= shop_date_end)
    if fab_type:
        count_query = count_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if search_filter is not None:
        count_query = count_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
        count_query = count_query.where(search_filter)
    elif search:
        search_term = f"%{search}%"
        count_query = count_query.join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
        count_query = count_query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search,
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number == search
            )
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.offset(skip).limit(limit).order_by(Fab.shop_date_schedule.asc().nullslast(), Fab.id.desc())
    
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
        
        # Ensure notes is always a list
        if fab_dict.get("notes") and not isinstance(fab_dict["notes"], list):
            fab_dict["notes"] = [fab_dict["notes"]] if fab_dict["notes"] else None
        
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
        
        # Add effective stage indicator
        fab_dict["effective_stage"] = "final_programming"
        fab_dict["is_from_cut_list"] = fab_dict.get("current_stage") == "cut_list"
        fab_dict["next_stage"] = get_next_stage("final_programming")
        
        fabs.append(fab_dict)
    
    # Fetch fab_notes and stage data for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
        
        # Fetch draft data
        draft_data = await get_draft_data(db, fab_dict["id"])
        fab_dict["draft_data"] = draft_data

        # Fetch CNC data
        cnc_data = await get_cnc_data(db, fab_dict["id"])
        fab_dict["cnc_data"] = cnc_data
        
        # Fetch Sales CT data
        sales_ct_data = await get_sales_ct_data(db, fab_dict["id"])
        fab_dict["sales_ct_data"] = sales_ct_data
        
        # Add stage completion status and stage-specific data
        stage_info = await get_stage_completion_data(db, fab_dict["id"], "final_programming")
        fab_dict["is_complete"] = stage_info["is_complete"]
        fab_dict["stage_data"] = stage_info["stage_data"]
    
    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    
    response_data = {
        "total": total,
        "page": page,
        "per_page": limit,
        "data": fabs
    }
    
    return success_response(
        response_data,
        f"Found {total} FABs requiring final programming ({len(fabs)} returned)"
    )

@router.get("/stages", response_model=SuccessResponse[List[dict]])
async def get_all_stages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workflow stages with FAB count for each stage"""
    from sqlalchemy import func, case, and_, or_
    
    # Get count of FABs for each stage with special logic for final_programming
    stage_counts_query = select(
        case(
            # If current_stage is cut_list AND shop_date_schedule is set AND final_programming_complete is False,
            # count it as final_programming instead of cut_list
            (
                and_(
                    Fab.current_stage == "cut_list",
                    Fab.shop_date_schedule.isnot(None),
                    Fab.final_programming_complete == False
                ),
                "final_programming"
            ),
            else_=Fab.current_stage
        ).label("effective_stage"),
        func.count(Fab.id).label('count')
    ).group_by("effective_stage")
    
    result = await db.execute(stage_counts_query)
    stage_counts_dict = {row[0]: row[1] for row in result.all()}
    
    # NEW: slab_smith_request count should mirror /stages/slabsmith/pending
    slabsmith_pending_filters = [
        or_(Fab.current_stage == "sales_ct", Fab.current_stage == "revision"),
        or_(Fab.slab_smith_ag_needed.is_(True), Fab.slab_smith_cust_needed.is_(True)),
        Fab.slabsmith_completed_date.is_(None),
    ]
    slabsmith_count_result = await db.execute(
        select(func.count(Fab.id)).where(*slabsmith_pending_filters)
    )
    slabsmith_pending_count = slabsmith_count_result.scalar() or 0
    
    slabsmith_ids_result = await db.execute(
        select(Fab.id)
        .where(*slabsmith_pending_filters)
        .order_by(Fab.id.desc())
        .limit(10)
    )
    slabsmith_last_10_ids = [row[0] for row in slabsmith_ids_result.all()]
    
    # Build response with all defined stages
    stages_data = []
    for idx, stage_name in enumerate(FAB_STAGES):
        fab_count = stage_counts_dict.get(stage_name, 0)
        
        # Build query for FAB IDs with same logic
        if stage_name == "final_programming":
            # For final_programming: include both actual final_programming FABs 
            # AND cut_list FABs that meet the criteria
            fab_ids_query = select(Fab.id).where(
                or_(
                    Fab.current_stage == "final_programming",
                    and_(
                        Fab.current_stage == "cut_list",
                        Fab.shop_date_schedule.isnot(None),
                        Fab.final_programming_complete == False
                    )
                )
            ).order_by(Fab.id.desc()).limit(10)
        elif stage_name == "cut_list":
            # For cut_list: EXCLUDE FABs that should be counted as final_programming
            fab_ids_query = select(Fab.id).where(
                and_(
                    Fab.current_stage == "cut_list",
                    or_(
                        Fab.shop_date_schedule.is_(None),
                        Fab.final_programming_complete == True
                    )
                )
            ).order_by(Fab.id.desc()).limit(10)
        elif stage_name == "slab_smith_request":
            fab_count = slabsmith_pending_count
            fab_ids = slabsmith_last_10_ids
            stages_data.append({
                "stage_name": stage_name,
                "stage_order": idx + 1,
                "fab_count": fab_count,
                "last_10_fab_ids": fab_ids,
                "next_stage": get_next_stage(stage_name)
            })
            continue
        else:
            # Normal query for other stages
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
        and_(
            Fab.current_stage.notin_(FAB_STAGES),
            # Exclude cut_list FABs that should be in final_programming
            or_(
                Fab.current_stage != "cut_list",
                and_(
                    Fab.current_stage == "cut_list",
                    or_(
                        Fab.shop_date_schedule.is_(None),
                        Fab.final_programming_complete == True
                    )
                )
            )
        )
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


@router.patch("/fabs/{fab_id}/hold")
async def toggle_fab_hold(
    fab_id: int,
    on_hold: bool = Query(..., description="Set fab on hold (true) or release it (false)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle FAB hold status by changing status_id (0=on hold, 1=active)"""
    fab_result = await db.execute(
        select(Fab).where(Fab.id == fab_id)
    )
    fab = fab_result.scalar_one_or_none()
    
    if not fab:
        return error_response("FAB not found", 404)
    
    # Set status_id: 0 for on hold, 1 for active
    fab.status_id = 0 if on_hold else 1
    fab.updated_by = current_user.id
    await db.commit()
    
    return success_response(
        {"fab_id": fab_id, "on_hold": on_hold, "status_id": fab.status_id},
        f"FAB {fab_id} {'placed on hold' if on_hold else 'released from hold'}"
    )



@router.patch("/fabs/{fab_id}/stage", response_model=SuccessResponse[FabResponse])
async def update_fab_stage(
    fab_id: int,
    stage_data: FabStageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update fab current_stage (admin-only handled in view)"""
    result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = result.scalar_one_or_none()
    if not fab:
        return error_response("Fab not found", 404)
    
    fab.current_stage = stage_data.current_stage
    fab.next_stage = get_next_stage(
        stage_data.current_stage,
        drafting_needed=fab.drafting_needed,
        slab_smith_ag_needed=fab.slab_smith_ag_needed,
        slab_smith_cust_needed=getattr(fab, "slab_smith_cust_needed", None),
    )
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(fab)
    
    return await get_fab(fab_id, db, current_user)
# ============ HELPER FUNCTIONS FOR FAB QUERIES ============

async def _apply_templating_filters(
    db: AsyncSession,
    templater_id: Optional[int],
    schedule_start_date: Optional[date],
    schedule_due_date: Optional[date],
    schedule_status: Optional[str],
    date_filter: Optional[str]
) -> Optional[List[int]]:
    """
    Apply templating-related filters and return matching FAB IDs.
    Returns None if no templating filters applied, or a list of FAB IDs.
    """
    if not any([schedule_start_date, schedule_due_date, date_filter, schedule_status, templater_id is not None]):
        return None
    
    templating_query = select(Templating.fab_id).distinct()
    
    # Apply templater_id filter
    if templater_id is not None:
        if templater_id == 0:
            templating_result = await db.execute(select(Templating.fab_id).distinct())
            fabs_with_templating = [row[0] for row in templating_result.all()]
            if fabs_with_templating:
                templating_query = select(Fab.id).where(~Fab.id.in_(fabs_with_templating))
            else:
                templating_query = select(Fab.id)
        else:
            templating_query = templating_query.where(Templating.technician_id == templater_id)
    
    # Apply date range filters
    if schedule_start_date is not None:
        templating_query = templating_query.where(Templating.schedule_start_date >= schedule_start_date)
    if schedule_due_date is not None:
        templating_query = templating_query.where(Templating.schedule_due_date <= schedule_due_date)
    
    # Apply schedule status filter
    if schedule_status == "scheduled":
        templating_query = templating_query.where(Templating.schedule_start_date.isnot(None))
    
    # Apply predefined date filters
    if date_filter:
        templating_query = _apply_date_filter(templating_query, date_filter)
    
    # Execute query
    if schedule_status != "unscheduled":
        result = await db.execute(templating_query)
        fab_ids = [row[0] for row in result.all()]
        return fab_ids if fab_ids else []
    else:
        # For unscheduled
        unscheduled_query = select(Fab.id).where(
            or_(
                ~Fab.id.in_(select(Templating.fab_id)),
                Fab.id.in_(select(Templating.fab_id).where(Templating.schedule_start_date.is_(None)))
            )
        )
        result = await db.execute(unscheduled_query)
        fab_ids = [row[0] for row in result.all()]
        return fab_ids if fab_ids else []


def _apply_date_filter(query, date_filter: str):
    """Apply predefined date filters to a query."""
    today = date.today()
    
    if date_filter == "today":
        return query.where(Templating.schedule_start_date == today)
    elif date_filter == "this_week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return query.where(Templating.schedule_start_date.between(start, end))
    elif date_filter == "last_week":
        # Start from last Monday
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return query.where(Templating.schedule_start_date.between(start, end))
    elif date_filter == "this_month":
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return query.where(Templating.schedule_start_date.between(start, end))
    elif date_filter == "last_month":
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return query.where(Templating.schedule_start_date.between(last_month_start, last_month_end))
    elif date_filter == "next_week":
        # Next Monday
        start = today + timedelta(days=(7 - today.weekday()))
        end = start + timedelta(days=6)
        return query.where(Templating.schedule_start_date.between(start, end))
    elif date_filter == "next_month":
        first_next = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        last_next = (first_next + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return query.where(Templating.schedule_start_date.between(first_next, last_next))
    
    return query


def _build_fab_list_query(
    job_id: Optional[int],
    fab_type: Optional[str],
    sales_person_id: Optional[int],
    status_id: Optional[int],
    current_stage: Optional[str],
    next_stage: Optional[str],
    search: Optional[str],
    templating_fab_ids: Optional[List[int]],
    latest_templating,
    shop_date_start: Optional[date] = None,
    shop_date_end: Optional[date] = None,
    template_completed_start: Optional[date] = None,
    template_completed_end: Optional[date] = None,
    predraft_completed_start: Optional[date] = None,
    predraft_completed_end: Optional[date] = None,
    draft_completed_start: Optional[date] = None,
    draft_completed_end: Optional[date] = None,
    sct_completed_start: Optional[date] = None,
    sct_completed_end: Optional[date] = None,
    date_filter: Optional[str] = None
) -> select:
    """Build the main FAB list query with all joins."""
    from sqlalchemy.orm import aliased
    
    TechnicianUser = aliased(User)
    DrafterUser = aliased(User)
    DrafterAssignedByUser = aliased(User)
    
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
        latest_templating.c.actual_end_date.label("templating_actual_end_date"),
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
    ).select_from(Fab)
    
    # Apply all joins
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
    
    # Apply basic filters
    if job_id is not None:
        query = query.where(Fab.job_id == job_id)
    if fab_type:
        query = query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
    if sales_person_id is not None:
        query = query.where(Fab.sales_person_id == sales_person_id)
    if status_id is not None:
        query = query.where(Fab.status_id == status_id)
    if current_stage:
        query = query.where(_stage_filter_condition(current_stage))
    if next_stage:
        query = query.where(Fab.next_stage == next_stage)
    

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                sa.cast(Fab.id, sa.String).ilike(search_term),
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number.ilike(search_term)
            )
        )


    # Apply stage-specific date filtering
    if current_stage:
        if current_stage == "templating":
            # Apply date filter to latest_templating.c.schedule_start_date
            query = _apply_stage_specific_date_filter(
                query, current_stage, date_filter, shop_date_start, shop_date_end, latest_templating
            )
            # Also filter by templating_fab_ids if present
            if templating_fab_ids is not None:
                query = query.where(Fab.id.in_(templating_fab_ids))
            return query
        elif current_stage == "pre_draft_review":
            date_start, date_end = template_completed_start, template_completed_end
        elif current_stage == "drafting":
            date_start, date_end = predraft_completed_start, predraft_completed_end
        elif current_stage == "sales_ct":
            date_start, date_end = draft_completed_start, draft_completed_end
        elif current_stage == "revision":
            date_start, date_end = sct_completed_start, sct_completed_end
        elif current_stage == "cut_list":
            date_start, date_end = shop_date_start, shop_date_end
        else:
            date_start, date_end = None, None
        
        # Apply the stage-specific date filter
        query = _apply_stage_specific_date_filter(
            query, current_stage, date_filter, date_start, date_end, latest_templating
        )
    else:
        # If no stage specified, apply all date filters generically
        if shop_date_start:
            query = query.where(Fab.shop_date_schedule >= shop_date_start)
        if shop_date_end:
            query = query.where(Fab.shop_date_schedule <= shop_date_end)
        if template_completed_start:
            query = query.where(Fab.template_completed_date >= template_completed_start)
        if template_completed_end:
            query = query.where(Fab.template_completed_date <= template_completed_end)
        if predraft_completed_start:
            query = query.where(Fab.predraft_completed_date >= predraft_completed_start)
        if predraft_completed_end:
            query = query.where(Fab.predraft_completed_date <= predraft_completed_end)
        if draft_completed_start:
            query = query.where(Fab.draft_completed_date >= draft_completed_start)
        if draft_completed_end:
            query = query.where(Fab.draft_completed_date <= draft_completed_end)
        if sct_completed_start:
            query = query.where(Fab.sct_completed_date >= sct_completed_start)
        if sct_completed_end:
            query = query.where(Fab.sct_completed_date <= sct_completed_end)
    
    
    if templating_fab_ids is not None:
        query = query.where(Fab.id.in_(templating_fab_ids))
    
    return query


def _apply_stage_specific_date_filter(
    query,
    current_stage: Optional[str],
    date_filter: Optional[str],
    date_start: Optional[date],
    date_end: Optional[date],
    latest_templating=None
) -> select:
    """
    Apply stage-specific date filtering based on the stage's primary date field.
    Supports both predefined filters (today, this_week, etc.) and custom date ranges.
    """
    if not current_stage:
        return query

    # Determine which date field to filter on based on stage
    date_field = None

    if current_stage == "templating":
        if latest_templating is not None:
            date_field = latest_templating.c.schedule_start_date
        else:
            return query
    elif current_stage == "pre_draft_review":
        date_field = Fab.template_completed_date
    elif current_stage == "drafting":
        date_field = Fab.predraft_completed_date
    elif current_stage == "sales_ct":
        date_field = Fab.draft_completed_date
    elif current_stage == "revision":
        date_field = Fab.sct_completed_date
    elif current_stage == "cut_list":
        date_field = Fab.shop_date_schedule
    else:
        return query

    date_field_cast = sa.cast(date_field, sa.Date)

    # Apply predefined date filter if provided
    if date_filter and date_field is not None:
        today = date.today()

        if date_filter == "today":
            query = query.where(date_field_cast == today)
        elif date_filter == "this_week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            query = query.where(date_field_cast.between(start, end))
        elif date_filter == "last_week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            query = query.where(date_field_cast.between(start, end))
        elif date_filter == "this_month":
            start = today.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            query = query.where(date_field_cast.between(start, end))
        elif date_filter == "last_month":
            first = today.replace(day=1)
            last_month_end = first - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            query = query.where(date_field_cast.between(last_month_start, last_month_end))
        elif date_filter == "next_week":
            start = today + timedelta(days=(7 - today.weekday()))
            end = start + timedelta(days=6)
            query = query.where(date_field_cast.between(start, end))
        elif date_filter == "next_month":
            first_next = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            last_next = (first_next + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            query = query.where(date_field_cast.between(first_next, last_next))

    # Apply custom date range if provided (and no predefined filter)
    elif date_field is not None:
        if date_start:
            query = query.where(date_field_cast >= date_start)
        if date_end:
            query = query.where(date_field_cast <= date_end)

    return query

def _apply_pagination_and_ordering(query, skip: int, limit: int, current_stage: Optional[str], latest_templating):
    """Apply pagination and stage-specific ordering."""
    if current_stage == "templating":
        return query.offset(skip).limit(limit).order_by(
            latest_templating.c.schedule_start_date.asc().nullslast(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    elif current_stage == "pre_draft_review":
        return query.offset(skip).limit(limit).order_by(
            Fab.template_completed_date.asc().nullsfirst(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    elif current_stage == "drafting":
        return query.offset(skip).limit(limit).order_by(
            Fab.predraft_completed_date.asc().nullsfirst(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    elif current_stage == "sales_ct":
        # Sort by draft_completed_date (oldest first, nulls last)
        return query.offset(skip).limit(limit).order_by(
            Fab.draft_completed_date.asc().nullslast(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    elif current_stage == "revision":
        # Sort by sct_completed_date (oldest first, nulls last)
        return query.offset(skip).limit(limit).order_by(
            Fab.sct_completed_date.asc().nullslast(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    elif current_stage == "cut_list":
        return query.offset(skip).limit(limit).order_by(
            Fab.shop_date_schedule.asc().nullsfirst(),
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    else:
        return query.offset(skip).limit(limit).order_by(
            Fab.updated_at.asc().nullsfirst(),
            Fab.created_at.asc()
        )
    

def _convert_fab_row_to_dict(row: tuple) -> dict:
    """Convert a fab query row to a dictionary with all related data."""
    fab = row[0]
    fab_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                for k, v in fab.__dict__.items() if not k.startswith('_')}
    
    if fab_dict.get("notes") and not isinstance(fab_dict["notes"], list):
        fab_dict["notes"] = [fab_dict["notes"]] if fab_dict["notes"] else None
    
    # Unpack remaining row data
    sales_person_first_name, sales_person_last_name = row[1], row[2]
    stone_type_name, stone_color_name, stone_thickness_value = row[3], row[4], row[5]
    edge_name = row[6]
    templating_schedule_start_date, templating_schedule_due_date, templating_notes = row[7], row[8], row[9]
    templating_actual_end_date = row[10]
    technician_first_name, technician_last_name = row[11], row[12]
    business_job = row[13]
    account_name, account_number, account_contact_person, account_email, account_phone = row[14:19]
    drafter_first_name, drafter_last_name = row[19], row[20]
    drafter_assigned_by_first_name, drafter_assigned_by_last_name = row[21], row[22]
    
    # Add related data
    fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
    fab_dict["stone_type_name"] = stone_type_name
    fab_dict["stone_color_name"] = stone_color_name
    fab_dict["stone_thickness_value"] = stone_thickness_value
    fab_dict["edge_name"] = edge_name
    
    if business_job:
        job_dict = {k: v.isoformat() if isinstance(v, (datetime, date)) else (float(v) if isinstance(v, Decimal) else v)
                   for k, v in business_job.__dict__.items() if not k.startswith('_')}
        fab_dict["job_details"] = job_dict
        fab_dict["account_id"] = business_job.account_id
    else:
        fab_dict["job_details"] = None
        fab_dict["account_id"] = None
    
    fab_dict["account_name"] = account_name
    fab_dict["account_number"] = account_number
    fab_dict["account_contact_person"] = account_contact_person
    fab_dict["account_email"] = account_email
    fab_dict["account_phone"] = account_phone
    
    fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
    fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
    fab_dict["templating_notes"] = templating_notes
    fab_dict["templating_actual_end_date"] = templating_actual_end_date.isoformat() if templating_actual_end_date else None
    fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
    
    fab_dict["drafter_name"] = f"{drafter_first_name} {drafter_last_name}" if drafter_first_name else None
    fab_dict["drafter_assigned_by_name"] = f"{drafter_assigned_by_first_name} {drafter_assigned_by_last_name}" if drafter_assigned_by_first_name else None
    fab_dict["next_stage"] = get_next_stage(
        fab_dict.get("current_stage"),
        drafting_needed=fab_dict.get("drafting_needed"),
        slab_smith_ag_needed=fab_dict.get("slab_smith_ag_needed"),
        slab_smith_cust_needed=fab_dict.get("slab_smith_cust_needed"),
    )    
    fab_dict["final_programming_complete"] = fab.final_programming_complete
    fab_dict["final_programming_completed_date"] = fab.final_programming_completed_date
    
    _add_total_cut_lnft(fab_dict)

    return fab_dict


async def _batch_load_fab_related_data(db: AsyncSession, fab_dicts: List[dict]) -> None:
    """Batch load and attach notes, draft, sales CT, and slabsmith data to fab dictionaries."""
    fab_ids = [fab["id"] for fab in fab_dicts]
    
    if not fab_ids:
        for fab_dict in fab_dicts:
            fab_dict["fab_notes"] = []
            fab_dict["draft_data"] = None
            fab_dict["cnc_data"] = None
            fab_dict["sales_ct_data"] = None
            fab_dict["slabsmith_data"] = None
            fab_dict["resurface_details"] = None
            fab_dict["install_details"] = None
            fab_dict["latest_revision"] = None
            fab_dict["drafting_session"] = None
            fab_dict["is_complete"] = False
            fab_dict["stage_data"] = None
        return
    
    # Load notes
    notes_by_fab = await _batch_load_fab_notes(db, fab_ids)
    
    # Load drafting data
    drafting_by_fab = await _batch_load_drafting_data(db, fab_ids)

    # Load CNC data
    cnc_by_fab = await _batch_load_cnc_data(db, fab_ids)
    
    # Load sales CT data
    sales_ct_by_fab = await _batch_load_sales_ct_data(db, fab_ids)
    
    # Load slabsmith data
    slabsmith_by_fab = await _batch_load_slabsmith_data(db, fab_ids)
    
    # Load resurface scheduling data
    resurface_by_fab = await _batch_load_resurface_data(db, fab_ids)

    # Load install completion data
    install_by_fab = await _batch_load_install_completion_data(db, fab_ids)
    
    # Load stage data
    stage_data_by_fab = await _batch_load_stage_data(db, fab_ids)
    drafting_sessions_by_fab = await _batch_load_drafting_sessions(db, fab_ids)
    latest_revisions_by_fab = await _batch_load_latest_revisions(db, fab_ids)
    
    # Attach to fab dicts
    for fab_dict in fab_dicts:
        fab_id = fab_dict["id"]
        fab_dict["fab_notes"] = notes_by_fab.get(fab_id, [])
        fab_dict["draft_data"] = drafting_by_fab.get(fab_id)
        fab_dict["cnc_data"] = cnc_by_fab.get(fab_id)
        fab_dict["sales_ct_data"] = sales_ct_by_fab.get(fab_id)
        fab_dict["slabsmith_data"] = slabsmith_by_fab.get(fab_id)
        fab_dict["resurface_details"] = resurface_by_fab.get(fab_id)
        fab_dict["install_details"] = install_by_fab.get(fab_id)
        fab_dict["latest_revision"] = latest_revisions_by_fab.get(fab_id)
        fab_dict["drafting_session"] = drafting_sessions_by_fab.get(fab_id)

        current_stage = fab_dict.get("current_stage")
        if current_stage == "templating":
            stage_info = stage_data_by_fab.get(fab_id, {"is_complete": False, "stage_data": None})
            fab_dict["is_complete"] = stage_info["is_complete"]
            fab_dict["stage_data"] = stage_info["stage_data"]
        else:
            fab_dict["is_complete"] = False
            fab_dict["stage_data"] = None


async def _batch_load_fab_notes(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load last 10 notes per FAB."""
    from sqlalchemy.orm import aliased
    
    CreatorUser = aliased(User)
    UpdaterUser = aliased(User)
    
    query = select(
        FabNotes,
        CreatorUser.first_name.label("creator_first_name"),
        CreatorUser.last_name.label("creator_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(FabNotes.fab_id.in_(fab_ids))\
     .join(CreatorUser, FabNotes.created_by == CreatorUser.id, isouter=True)\
     .join(UpdaterUser, FabNotes.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(FabNotes.fab_id, FabNotes.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    notes_by_fab = {}
    for row in rows:
        note = row[0]
        creator_first, creator_last = row[1], row[2]
        updater_first, updater_last = row[3], row[4]
        
        if note.fab_id not in notes_by_fab:
            notes_by_fab[note.fab_id] = []
        
        if len(notes_by_fab[note.fab_id]) < 10:
            notes_by_fab[note.fab_id].append({
                "id": note.id,
                "fab_id": note.fab_id,
                "stage": note.stage,
                "note": note.note,
                "created_by": note.created_by,
                "created_by_name": f"{creator_first} {creator_last}" if creator_first else None,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                "updated_by": note.updated_by,
                "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
            })
    
    return notes_by_fab


async def _batch_load_drafting_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load drafting data with files for each FAB."""
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
    ).where(Drafting.fab_id.in_(fab_ids))\
     .join(DrafterUser, Drafting.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, Drafting.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(Drafting.fab_id, Drafting.id.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Get all file IDs first
    all_file_ids = set()
    for row in rows:
        draft = row[0]
        if draft.file_ids:
            all_file_ids.update(int(fid.strip()) for fid in draft.file_ids.split(",") if fid.strip())
    
    # Batch load files
    files_by_id = {}
    if all_file_ids:
        UploaderUser = aliased(User)
        files_query = (
            select(File, UploaderUser.first_name, UploaderUser.last_name)
            .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
            .where(File.id.in_(all_file_ids))
        )
        files_result = await db.execute(files_query)
        for row in files_result.all():
            file = row[0]
            uploader_first = row[1]
            uploader_last = row[2]
            file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
            files_by_id[file.id] = {
                "id": file.id,
                "name": file.name,
                "file_url": file_url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "stage": file.stage,
                "file_design": file.file_design,
                "stage_name": file.stage_name,
                "uploaded_by": file.uploaded_by,
                "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_by": file.uploaded_by,
                "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_at": file.created_at.isoformat() if file.created_at else None,
            }
    # Group by FAB (get latest only)
    drafting_by_fab = {}
    for row in rows:
        draft = row[0]
        if draft.fab_id not in drafting_by_fab:
            files_data = []
            if draft.file_ids:
                file_id_list = [int(fid.strip()) for fid in draft.file_ids.split(",") if fid.strip()]
                files_data = [files_by_id[fid] for fid in file_id_list if fid in files_by_id]
            
            drafting_by_fab[draft.fab_id] = {
                "id": draft.id,
                "fab_id": draft.fab_id,
                "drafter_id": draft.drafter_id,
                "drafter_name": f"{row[1]} {row[2]}" if row[1] else None,
                "drafter_start_date": draft.drafter_start_date.isoformat() if draft.drafter_start_date else None,
                "drafter_end_date": draft.drafter_end_date.isoformat() if draft.drafter_end_date else None,
                "total_sqft_drafted": float(draft.total_sqft_drafted) if draft.total_sqft_drafted else None,
                "no_of_piece_drafted": draft.no_of_piece_drafted,
                "draft_note": draft.draft_note,
                "mentions": draft.mentions,
                "total_hours_drafted": float(draft.total_hours_drafted) if draft.total_hours_drafted else None,
                "file_ids": draft.file_ids,
                "files": files_data,
                "status_id": draft.status_id,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
                "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
                "updated_by": draft.updated_by,
                "updated_by_name": f"{row[3]} {row[4]}" if row[3] else None
            }
    
    return drafting_by_fab


async def _batch_load_cnc_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load CNC drafting data with files for each FAB."""
    from src.app.database.cnc import CNCDrafting
    from src.app.database.file import File
    from sqlalchemy.orm import aliased

    DrafterUser = aliased(User)
    UpdaterUser = aliased(User)

    query = select(
        CNCDrafting,
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(CNCDrafting.fab_id.in_(fab_ids))\
     .join(DrafterUser, CNCDrafting.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, CNCDrafting.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(CNCDrafting.fab_id, CNCDrafting.id.desc())

    result = await db.execute(query)
    rows = result.all()

    all_file_ids = set()
    for row in rows:
        cnc = row[0]
        if cnc.file_ids:
            all_file_ids.update(int(fid.strip()) for fid in cnc.file_ids.split(",") if fid.strip())

    files_by_id = {}
    if all_file_ids:
        UploaderUser = aliased(User)
        files_query = (
            select(File, UploaderUser.first_name, UploaderUser.last_name)
            .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
            .where(File.id.in_(all_file_ids))
        )
        files_result = await db.execute(files_query)
        for file_row in files_result.all():
            file = file_row[0]
            uploader_first = file_row[1]
            uploader_last = file_row[2]
            file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
            files_by_id[file.id] = {
                "id": file.id,
                "name": file.name,
                "file_url": file_url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "stage": file.stage,
                "file_design": file.file_design,
                "stage_name": file.stage_name,
                "uploaded_by": file.uploaded_by,
                "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_by": file.uploaded_by,
                "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_at": file.created_at.isoformat() if file.created_at else None,
            }

    cnc_by_fab = {}
    for row in rows:
        cnc = row[0]
        if cnc.fab_id not in cnc_by_fab:
            files_data = []
            if cnc.file_ids:
                file_id_list = [int(fid.strip()) for fid in cnc.file_ids.split(",") if fid.strip()]
                files_data = [files_by_id[fid] for fid in file_id_list if fid in files_by_id]

            cnc_by_fab[cnc.fab_id] = {
                "id": cnc.id,
                "fab_id": cnc.fab_id,
                "drafter_id": cnc.drafter_id,
                "drafter_name": f"{row[1]} {row[2]}" if row[1] else None,
                "scheduled_start_date": cnc.scheduled_start_date.isoformat() if cnc.scheduled_start_date else None,
                "scheduled_end_date": cnc.scheduled_end_date.isoformat() if cnc.scheduled_end_date else None,
                "drafter_start_date": cnc.drafter_start_date.isoformat() if cnc.drafter_start_date else None,
                "drafter_end_date": cnc.drafter_end_date.isoformat() if cnc.drafter_end_date else None,
                "total_sqft_required_to_draft": cnc.total_sqft_required_to_draft,
                "total_sqft": float(cnc.total_sqft) if cnc.total_sqft is not None else None,
                "no_of_pieces": cnc.no_of_pieces,
                "cad_review_complete": cnc.cad_review_complete,
                "draft_completed": cnc.draft_completed,
                "notes": cnc.notes,
                "current_stage": cnc.current_stage,
                "total_sqft_drafted": float(cnc.total_sqft_drafted) if cnc.total_sqft_drafted is not None else None,
                "no_of_piece_drafted": cnc.no_of_piece_drafted,
                "draft_note": cnc.draft_note,
                "mentions": cnc.mentions,
                "total_hours_drafted": float(cnc.total_hours_drafted) if cnc.total_hours_drafted is not None else None,
                "is_completed": cnc.is_completed,
                "file_ids": cnc.file_ids,
                "files": files_data,
                "status_id": cnc.status_id,
                "created_at": cnc.created_at.isoformat() if cnc.created_at else None,
                "updated_at": cnc.updated_at.isoformat() if cnc.updated_at else None,
                "updated_by": cnc.updated_by,
                "updated_by_name": f"{row[3]} {row[4]}" if row[3] else None,
            }

    return cnc_by_fab


async def _batch_load_sales_ct_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load sales CT data with files for each FAB."""
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
    ).where(SalesCT.fab_id.in_(fab_ids))\
     .join(DrafterUser, SalesCT.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, SalesCT.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(SalesCT.fab_id, SalesCT.id.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Get all file IDs
    all_file_ids = set()
    for row in rows:
        sct = row[0]
        if sct.file_ids:
            all_file_ids.update(int(fid.strip()) for fid in sct.file_ids.split(",") if fid.strip())
    
    # Batch load files
    files_by_id = {}
    if all_file_ids:
        UploaderUser = aliased(User)
        files_query = (
            select(File, UploaderUser.first_name, UploaderUser.last_name)
            .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
            .where(File.id.in_(all_file_ids))
        )
        files_result = await db.execute(files_query)
        for row in files_result.all():
            file = row[0]
            uploader_first = row[1]
            uploader_last = row[2]
            file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
            files_by_id[file.id] = {
                "id": file.id,
                "name": file.name,
                "file_url": file_url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "stage": file.stage,
                "file_design": file.file_design,
                "stage_name": file.stage_name,
                "uploaded_by": file.uploaded_by,
                "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_by": file.uploaded_by,
                "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_at": file.created_at.isoformat() if file.created_at else None
            }
    
    # Group by FAB (get latest only)
    sales_ct_by_fab = {}
    for row in rows:
        sct = row[0]
        if sct.fab_id not in sales_ct_by_fab:
            files_data = []
            if sct.file_ids:
                file_id_list = [int(fid.strip()) for fid in sct.file_ids.split(",") if fid.strip()]
                files_data = [files_by_id[fid] for fid in file_id_list if fid in files_by_id]
            
            sales_ct_by_fab[sct.fab_id] = {
                "id": sct.id,
                "fab_id": sct.fab_id,
                "slab_smith_type": sct.slab_smith_type,
                "drafter_id": sct.drafter_id,
                "drafter_name": f"{row[1]} {row[2]}" if row[1] else None,
                "start_date": sct.start_date.isoformat() if sct.start_date else None,
                "end_date": sct.end_date.isoformat() if sct.end_date else None,
                "total_sqft_completed": sct.total_sqft_completed,
                "is_revision_needed": sct.is_revision_needed,
                "is_revision_completed": sct.is_revision_completed,
                "no_of_revisions": sct.no_of_revisions,
                "current_revision_count": sct.current_revision_count,
                "revision_reason": sct.revision_reason,
                "revision_type": sct.revision_type,
                "file_ids": sct.file_ids,
                "files": files_data,
                "status_id": sct.status_id,
                "created_at": sct.created_at.isoformat() if sct.created_at else None,
                "updated_at": sct.updated_at.isoformat() if sct.updated_at else None,
                "updated_by": sct.updated_by,
                "updated_by_name": f"{row[3]} {row[4]}" if row[3] else None
            }
    
    return sales_ct_by_fab


async def _batch_load_stage_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load templating stage data for templating stage FABs."""
    query = select(
        Templating,
        User.first_name.label("technician_first_name"),
        User.last_name.label("technician_last_name"),
        Status.name.label("status_name")
    ).where(
        Templating.fab_id.in_(fab_ids),
        Templating.is_templating_schedule == True
    ).outerjoin(User, Templating.technician_id == User.id)\
     .outerjoin(Status, Templating.status_id == Status.id)\
     .order_by(Templating.fab_id, Templating.id.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    stage_data_by_fab = {}
    for row in rows:
        templating = row[0]
        technician_first, technician_last = row[1], row[2]
        status_name = row[3]
        if templating.fab_id not in stage_data_by_fab:
            stage_data_by_fab[templating.fab_id] = {
                "is_complete": templating.is_completed,
                "stage_data": {
                    "templating_id": templating.id,
                    "technician_id": templating.technician_id,
                    "technician_name": f"{technician_first} {technician_last}" if technician_first else None,
                    "schedule_start_date": templating.schedule_start_date.isoformat() if templating.schedule_start_date else None,
                    "schedule_due_date": templating.schedule_due_date.isoformat() if templating.schedule_due_date else None,
                    "actual_start_date": templating.actual_start_date.isoformat() if templating.actual_start_date else None,
                    "duration": templating.duration,
                    "total_sqft": templating.total_sqft,
                    "notes": templating.notes,
                    "is_templating_schedule": templating.is_templating_schedule,
                    "is_completed": templating.is_completed,
                    "rescheduled": templating.rescheduled,
                    "status_id": templating.status_id,
                    "status_name": status_name,
                    "created_at": templating.created_at.isoformat() if templating.created_at else None,
                    "updated_at": templating.updated_at.isoformat() if templating.updated_at else None,
                    "updated_by": templating.updated_by
                }
            }
    return stage_data_by_fab


async def _batch_load_slabsmith_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load slabsmith data with files for each FAB."""
    from src.app.database.slab_smith import SlabSmith
    from src.app.database.file import File
    from sqlalchemy.orm import aliased
    
    UpdaterUser = aliased(User)
    
    query = select(
        SlabSmith,
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(SlabSmith.fab_id.in_(fab_ids))\
     .join(UpdaterUser, SlabSmith.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(SlabSmith.fab_id, SlabSmith.id.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Get all file IDs
    all_file_ids = set()
    for row in rows:
        slabsmith = row[0]
        if slabsmith.file_ids:
            all_file_ids.update(int(fid.strip()) for fid in slabsmith.file_ids.split(",") if fid.strip())
    
    # Batch load files
    files_by_id = {}
    if all_file_ids:
        UploaderUser = aliased(User)
        files_query = (
            select(File, UploaderUser.first_name, UploaderUser.last_name)
            .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
            .where(File.id.in_(all_file_ids))
        )
        files_result = await db.execute(files_query)
        for row in files_result.all():
            file = row[0]
            uploader_first = row[1]
            uploader_last = row[2]
            file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
            files_by_id[file.id] = {
                "id": file.id,
                "name": file.name,
                "file_url": file_url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "stage": file.stage,
                "file_design": file.file_design,
                "stage_name": file.stage_name,
                "uploaded_by": file.uploaded_by,
                "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_by": file.uploaded_by,
                "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_at": file.created_at.isoformat() if file.created_at else None
            }
    
    # Group by FAB (get latest only)
    slabsmith_by_fab = {}
    for row in rows:
        slabsmith = row[0]
        if slabsmith.fab_id not in slabsmith_by_fab:
            files_data = []
            if slabsmith.file_ids:
                file_id_list = [int(fid.strip()) for fid in slabsmith.file_ids.split(",") if fid.strip()]
                files_data = [files_by_id[fid] for fid in file_id_list if fid in files_by_id]
            
            slabsmith_by_fab[slabsmith.fab_id] = {
                "id": slabsmith.id,
                "fab_id": slabsmith.fab_id,
                "slab_smith_type": slabsmith.slab_smith_type,
                "drafter_id": slabsmith.drafter_id,
                "start_date": slabsmith.start_date.isoformat() if slabsmith.start_date else None,
                "end_date": slabsmith.end_date.isoformat() if slabsmith.end_date else None,
                "total_sqft_completed": slabsmith.total_sqft_completed,
                "file_ids": slabsmith.file_ids,
                "files": files_data,
                "status_id": slabsmith.status_id,
                "created_at": slabsmith.created_at.isoformat() if slabsmith.created_at else None,
                "updated_at": slabsmith.updated_at.isoformat() if slabsmith.updated_at else None,
                "updated_by": slabsmith.updated_by,
                "updated_by_name": f"{row[1]} {row[2]}" if row[1] else None
            }
    
    return slabsmith_by_fab

# Add these helper functions before the router endpoints

async def get_draft_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get the latest drafting data for a FAB"""
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
    ).where(Drafting.fab_id == fab_id)\
     .join(DrafterUser, Drafting.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, Drafting.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(Drafting.id.desc())\
     .limit(1)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return None
    
    draft = row[0]
    drafter_first = row[1]
    drafter_last = row[2]
    updater_first = row[3]
    updater_last = row[4]
    
    # Get files if any
    files_data = []
    if draft.file_ids:
        file_id_list = [int(fid.strip()) for fid in draft.file_ids.split(",") if fid.strip()]
        if file_id_list:
            # Join File with User to get uploader name
            UploaderUser = aliased(User)
            files_query = (
                select(File, UploaderUser.first_name, UploaderUser.last_name)
                .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
                .where(File.id.in_(file_id_list))
            )
            files_result = await db.execute(files_query)

            for row in files_result.all():
                file = row[0]
                uploader_first = row[1]
                uploader_last = row[2]

                file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"

                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "stage": file.stage,
                    "file_design": file.file_design,
                    "stage_name": file.stage_name,
                    "uploaded_by": file.uploaded_by,
                    "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_by": file.uploaded_by,
                    "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                })
    
    return {
        "id": draft.id,
        "fab_id": draft.fab_id,
        "drafter_id": draft.drafter_id,
        "drafter_name": f"{drafter_first} {drafter_last}" if drafter_first else None,
        "drafter_start_date": draft.drafter_start_date.isoformat() if draft.drafter_start_date else None,
        "drafter_end_date": draft.drafter_end_date.isoformat() if draft.drafter_end_date else None,
        "total_sqft_drafted": float(draft.total_sqft_drafted) if draft.total_sqft_drafted else None,
        "no_of_piece_drafted": draft.no_of_piece_drafted,
        "draft_note": draft.draft_note,
        "mentions": draft.mentions,
        "total_hours_drafted": float(draft.total_hours_drafted) if draft.total_hours_drafted else None,
        "file_ids": draft.file_ids,
        "files": files_data,
        "status_id": draft.status_id,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
        "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
        "updated_by": draft.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
    }


async def get_cnc_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get the latest CNC drafting data for a FAB"""
    from src.app.database.cnc import CNCDrafting
    from src.app.database.file import File
    from sqlalchemy.orm import aliased

    DrafterUser = aliased(User)
    UpdaterUser = aliased(User)

    query = select(
        CNCDrafting,
        DrafterUser.first_name.label("drafter_first_name"),
        DrafterUser.last_name.label("drafter_last_name"),
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(CNCDrafting.fab_id == fab_id)\
     .join(DrafterUser, CNCDrafting.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, CNCDrafting.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(CNCDrafting.id.desc())\
     .limit(1)

    result = await db.execute(query)
    row = result.first()

    if not row:
        return None

    cnc = row[0]
    drafter_first = row[1]
    drafter_last = row[2]
    updater_first = row[3]
    updater_last = row[4]

    files_data = []
    if cnc.file_ids:
        file_id_list = [int(fid.strip()) for fid in cnc.file_ids.split(",") if fid.strip()]
        if file_id_list:
            UploaderUser = aliased(User)
            files_query = (
                select(File, UploaderUser.first_name, UploaderUser.last_name)
                .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
                .where(File.id.in_(file_id_list))
            )
            files_result = await db.execute(files_query)
            for file_row in files_result.all():
                file = file_row[0]
                uploader_first = file_row[1]
                uploader_last = file_row[2]
                file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "stage": file.stage,
                    "file_design": file.file_design,
                    "stage_name": file.stage_name,
                    "uploaded_by": file.uploaded_by,
                    "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_by": file.uploaded_by,
                    "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_at": file.created_at.isoformat() if file.created_at else None,
                })

    return {
        "id": cnc.id,
        "fab_id": cnc.fab_id,
        "drafter_id": cnc.drafter_id,
        "drafter_name": f"{drafter_first} {drafter_last}" if drafter_first else None,
        "scheduled_start_date": cnc.scheduled_start_date.isoformat() if cnc.scheduled_start_date else None,
        "scheduled_end_date": cnc.scheduled_end_date.isoformat() if cnc.scheduled_end_date else None,
        "drafter_start_date": cnc.drafter_start_date.isoformat() if cnc.drafter_start_date else None,
        "drafter_end_date": cnc.drafter_end_date.isoformat() if cnc.drafter_end_date else None,
        "total_sqft_required_to_draft": cnc.total_sqft_required_to_draft,
        "total_sqft": float(cnc.total_sqft) if cnc.total_sqft is not None else None,
        "no_of_pieces": cnc.no_of_pieces,
        "cad_review_complete": cnc.cad_review_complete,
        "draft_completed": cnc.draft_completed,
        "notes": cnc.notes,
        "current_stage": cnc.current_stage,
        "total_sqft_drafted": float(cnc.total_sqft_drafted) if cnc.total_sqft_drafted is not None else None,
        "no_of_piece_drafted": cnc.no_of_piece_drafted,
        "draft_note": cnc.draft_note,
        "mentions": cnc.mentions,
        "total_hours_drafted": float(cnc.total_hours_drafted) if cnc.total_hours_drafted is not None else None,
        "is_completed": cnc.is_completed,
        "file_ids": cnc.file_ids,
        "files": files_data,
        "status_id": cnc.status_id,
        "created_at": cnc.created_at.isoformat() if cnc.created_at else None,
        "updated_at": cnc.updated_at.isoformat() if cnc.updated_at else None,
        "updated_by": cnc.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None,
    }


async def get_sales_ct_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get the latest sales CT data for a FAB"""
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
    ).where(SalesCT.fab_id == fab_id)\
     .join(DrafterUser, SalesCT.drafter_id == DrafterUser.id, isouter=True)\
     .join(UpdaterUser, SalesCT.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(SalesCT.id.desc())\
     .limit(1)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return None
    
    sct = row[0]
    drafter_first = row[1]
    drafter_last = row[2]
    updater_first = row[3]
    updater_last = row[4]
    
    # Get files if any
    files_data = []
    if sct.file_ids:
        file_id_list = [int(fid.strip()) for fid in sct.file_ids.split(",") if fid.strip()]
        if file_id_list:
            # Join File with User to get uploader name
            UploaderUser = aliased(User)
            files_query = (
                select(File, UploaderUser.first_name, UploaderUser.last_name)
                .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
                .where(File.id.in_(file_id_list))
            )
            files_result = await db.execute(files_query)

            for row in files_result.all():
                file = row[0]
                uploader_first = row[1]
                uploader_last = row[2]

                file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"

                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "stage": file.stage,
                    "file_design": file.file_design,
                    "stage_name": file.stage_name,
                    "uploaded_by": file.uploaded_by,
                    "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_by": file.uploaded_by,
                    "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                })
    
    return {
        "id": sct.id,
        "fab_id": sct.fab_id,
        "slab_smith_type": sct.slab_smith_type,
        "drafter_id": sct.drafter_id,
        "drafter_name": f"{drafter_first} {drafter_last}" if drafter_first else None,
        "start_date": sct.start_date.isoformat() if sct.start_date else None,
        "end_date": sct.end_date.isoformat() if sct.end_date else None,
        "total_sqft_completed": sct.total_sqft_completed,
        "is_revision_needed": sct.is_revision_needed,
        "is_revision_completed": sct.is_revision_completed,
        "no_of_revisions": sct.no_of_revisions,
        "current_revision_count": sct.current_revision_count,
        "revision_reason": sct.revision_reason,
        "revision_type": sct.revision_type,
        "file_ids": sct.file_ids,
        "files": files_data,
        "status_id": sct.status_id,
        "created_at": sct.created_at.isoformat() if sct.created_at else None,
        "updated_at": sct.updated_at.isoformat() if sct.updated_at else None,
        "updated_by": sct.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
    }

async def _batch_load_resurface_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load latest resurface scheduling data for each FAB."""
    from src.app.interface.generated_schemas import ResurfaceScheduling

    query = (
        select(ResurfaceScheduling)
        .where(ResurfaceScheduling.fab_id.in_(fab_ids))
        .order_by(ResurfaceScheduling.fab_id, ResurfaceScheduling.id.desc())
    )

    result = await db.execute(query)
    rows = result.scalars().all()

    resurface_by_fab = {}
    for r in rows:
        if r.fab_id not in resurface_by_fab:
            resurface_by_fab[r.fab_id] = {
                "id": r.id,
                "scheduled_start_date": r.scheduled_start_date.isoformat() if r.scheduled_start_date else None,
                "scheduled_end_date": r.scheduled_end_date.isoformat() if r.scheduled_end_date else None,
                "is_completed": r.is_completed,
                "status_id": r.status_id,
            }

    return resurface_by_fab


async def _batch_load_resurface_scheduling_responses(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load full ResurfaceSchedulingResponse data for each FAB."""
    if not fab_ids:
        return {}
    
    query = (
        select(ResurfaceScheduling)
        .where(ResurfaceScheduling.fab_id.in_(fab_ids))
        .order_by(ResurfaceScheduling.fab_id, ResurfaceScheduling.id.desc())
    )

    result = await db.execute(query)
    rows = result.scalars().all()

    resurface_responses_by_fab = {}
    for r in rows:
        if r.fab_id not in resurface_responses_by_fab:
            resurface_responses_by_fab[r.fab_id] = ResurfaceSchedulingResponse(
                id=r.id,
                fab_id=r.fab_id,
                technician_id=r.technician_id,
                scheduled_start_date=r.scheduled_start_date,
                scheduled_end_date=r.scheduled_end_date,
                actual_start_date=r.actual_start_date,
                actual_end_date=r.actual_end_date,
                total_sqft=r.total_sqft,
                completed_sqft=r.completed_sqft,
                is_completed=r.is_completed,
                status_id=r.status_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                updated_by=r.updated_by
            )

    return resurface_responses_by_fab


async def _batch_load_install_scheduling_responses(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load full InstallSchedulingResponse data for each FAB."""
    if not fab_ids:
        return {}
    
    query = (
        select(InstallScheduling)
        .where(InstallScheduling.fab_id.in_(fab_ids))
        .order_by(InstallScheduling.fab_id, InstallScheduling.id.desc())
    )

    result = await db.execute(query)
    rows = result.scalars().all()

    install_scheduling_responses_by_fab = {}
    for r in rows:
        if r.fab_id not in install_scheduling_responses_by_fab:
            # Fetch installer name if installer_id is set
            installer_name = None
            if r.installer_id:
                installer_result = await db.execute(select(User).where(User.id == r.installer_id))
                installer = installer_result.scalar_one_or_none()
                if installer:
                    installer_name = f"{installer.first_name} {installer.last_name}".strip()
            
            install_scheduling_responses_by_fab[r.fab_id] = InstallSchedulingResponse(
                id=r.id,
                fab_id=r.fab_id,
                installer_id=r.installer_id,
                installer_name=installer_name,
                scheduled_install_date=r.scheduled_install_date,
                scheduled_end_date=r.scheduled_end_date,
                actual_install_date=r.actual_install_date,
                total_sqft=r.total_sqft,
                is_completed=r.is_completed,
                status_id=r.status_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                updated_by=r.updated_by
            )

    return install_scheduling_responses_by_fab


async def _batch_load_install_completion_data(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load latest install completion data for each FAB."""
    from sqlalchemy.orm import aliased
    from src.app.interface.generated_schemas import InstallCompletion

    InstallerUser = aliased(User)
    UpdaterUser = aliased(User)

    query = (
        select(
            InstallCompletion,
            InstallerUser.first_name.label("installer_first_name"),
            InstallerUser.last_name.label("installer_last_name"),
            UpdaterUser.first_name.label("updater_first_name"),
            UpdaterUser.last_name.label("updater_last_name"),
            Status.name.label("status_name"),
        )
        .where(InstallCompletion.fab_id.in_(fab_ids))
        .join(InstallerUser, InstallCompletion.installer_id == InstallerUser.id, isouter=True)
        .join(UpdaterUser, InstallCompletion.updated_by == UpdaterUser.id, isouter=True)
        .join(Status, InstallCompletion.status_id == Status.value_id, isouter=True)
        .order_by(InstallCompletion.fab_id, InstallCompletion.id.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    install_by_fab = {}
    for row in rows:
        install = row[0]
        if install.fab_id not in install_by_fab:
            install_by_fab[install.fab_id] = {
                "id": install.id,
                "fab_id": install.fab_id,
                "installer_id": install.installer_id,
                "installer_name": f"{row[1]} {row[2]}" if row[1] else None,
                "install_date": install.install_date.isoformat() if install.install_date else None,
                "completion_date": install.completion_date.isoformat() if install.completion_date else None,
                "total_sqft_installed": install.total_sqft_installed,
                "customer_signature": install.customer_signature,
                "completion_notes": install.completion_notes,
                "is_completed": install.is_completed,
                "status_id": install.status_id,
                "status_name": row[5],
                "created_at": install.created_at.isoformat() if install.created_at else None,
                "updated_at": install.updated_at.isoformat() if install.updated_at else None,
                "updated_by": install.updated_by,
                "updated_by_name": f"{row[3]} {row[4]}" if row[3] else None,
            }

    return install_by_fab

async def get_slabsmith_data(db: AsyncSession, fab_id: int) -> Optional[dict]:
    """Get the latest slabsmith data for a FAB"""
    from src.app.database.slab_smith import SlabSmith
    from src.app.database.file import File
    from sqlalchemy.orm import aliased
    
    UpdaterUser = aliased(User)
    
    query = select(
        SlabSmith,
        UpdaterUser.first_name.label("updater_first_name"),
        UpdaterUser.last_name.label("updater_last_name")
    ).where(SlabSmith.fab_id == fab_id)\
     .join(UpdaterUser, SlabSmith.updated_by == UpdaterUser.id, isouter=True)\
     .order_by(SlabSmith.fab_id, SlabSmith.id.desc())\
     .limit(1)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return None
    
    slabsmith = row[0]
    updater_first = row[1]
    updater_last = row[2]
    
    # Get files if any
    files_data = []
    if slabsmith.file_ids:
        file_id_list = [int(fid.strip()) for fid in slabsmith.file_ids.split(",") if fid.strip()]
        if file_id_list:
            UploaderUser = aliased(User)
            files_query = (
                select(File, UploaderUser.first_name, UploaderUser.last_name)
                .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
                .where(File.id.in_(file_id_list))
            )
            files_result = await db.execute(files_query)
            for file_row in files_result.all():
                file = file_row[0]
                uploader_first = file_row[1]
                uploader_last = file_row[2]
                file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
                files_data.append({
                    "id": file.id,
                    "name": file.name,
                    "file_url": file_url,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "stage": file.stage,
                    "file_design": file.file_design,
                    "stage_name": file.stage_name,
                    "uploaded_by": file.uploaded_by,
                    "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_by": file.uploaded_by,
                    "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                })
    
    return {
        "id": slabsmith.id,
        "fab_id": slabsmith.fab_id,
        "slab_smith_type": slabsmith.slab_smith_type,
        "drafter_id": slabsmith.drafter_id,
        "start_date": slabsmith.start_date.isoformat() if slabsmith.start_date else None,
        "end_date": slabsmith.end_date.isoformat() if slabsmith.end_date else None,
        "total_sqft_completed": slabsmith.total_sqft_completed,
        "file_ids": slabsmith.file_ids,
        "files": files_data,
        "status_id": slabsmith.status_id,
        "created_at": slabsmith.created_at.isoformat() if slabsmith.created_at else None,
        "updated_at": slabsmith.updated_at.isoformat() if slabsmith.updated_at else None,
        "updated_by": slabsmith.updated_by,
        "updated_by_name": f"{updater_first} {updater_last}" if updater_first else None
    }


from src.app.interface.generated_schemas import Revision

async def _batch_load_latest_revisions(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load the most recent revision for each FAB."""
    from sqlalchemy.orm import aliased
    
    RequestedByUser = aliased(User)
    AssignedToUser = aliased(User)
    UpdatedByUser = aliased(User)
    
    query = select(
        Revision,
        RequestedByUser.first_name.label("requested_by_first_name"),
        RequestedByUser.last_name.label("requested_by_last_name"),
        AssignedToUser.first_name.label("assigned_to_first_name"),
        AssignedToUser.last_name.label("assigned_to_last_name"),
        UpdatedByUser.first_name.label("updated_by_first_name"),
        UpdatedByUser.last_name.label("updated_by_last_name")
    ).where(Revision.fab_id.in_(fab_ids))\
     .join(RequestedByUser, Revision.requested_by == RequestedByUser.id, isouter=True)\
     .join(AssignedToUser, Revision.assigned_to == AssignedToUser.id, isouter=True)\
     .join(UpdatedByUser, Revision.updated_by == UpdatedByUser.id, isouter=True)\
     .order_by(Revision.fab_id, Revision.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Get all file IDs
    all_file_ids = set()
    for row in rows:
        rev = row[0]
        if rev.file_ids:
            all_file_ids.update(int(fid.strip()) for fid in rev.file_ids.split(",") if fid.strip())
    
    # Batch load files
    files_by_id = {}
    if all_file_ids:
        from src.app.database.file import File
        from sqlalchemy.orm import aliased as _aliased
        UploaderUser = _aliased(User)
        files_query = (
            select(File, UploaderUser.first_name, UploaderUser.last_name)
            .join(UploaderUser, File.uploaded_by == UploaderUser.id, isouter=True)
            .where(File.id.in_(all_file_ids))
        )
        files_result = await db.execute(files_query)
        for file_row in files_result.all():
            file = file_row[0]
            uploader_first = file_row[1]
            uploader_last = file_row[2]
            file_url = f"{BASE_URL}/api/v1/files/{file.id}/view"
            files_by_id[file.id] = {
                "id": file.id,
                "name": file.name,
                "file_url": file_url,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "stage": file.stage,
                "file_design": file.file_design,
                "stage_name": file.stage_name,
                "uploaded_by": file.uploaded_by,
                "uploaded_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_by": file.uploaded_by,
                "created_by_name": f"{uploader_first} {uploader_last}" if uploader_first else None,
                "created_at": file.created_at.isoformat() if file.created_at else None
            }
    
    # Group by FAB (get latest only)
    latest_revisions = {}
    for row in rows:
        rev = row[0]
        if rev.fab_id not in latest_revisions:
            files_data = []
            if rev.file_ids:
                file_id_list = [int(fid.strip()) for fid in rev.file_ids.split(",") if fid.strip()]
                files_data = [files_by_id[fid] for fid in file_id_list if fid in files_by_id]
            
            latest_revisions[rev.fab_id] = {
                "id": rev.id,
                "fab_id": rev.fab_id,
                "revision_type": rev.revision_type,
                "requested_by": rev.requested_by,
                "requested_by_name": f"{row[1]} {row[2]}" if row[1] else None,
                "assigned_to": rev.assigned_to,
                "assigned_to_name": f"{row[3]} {row[4]}" if row[3] else None,
                "scheduled_start_date": rev.scheduled_start_date.isoformat() if rev.scheduled_start_date else None,
                "scheduled_end_date": rev.scheduled_end_date.isoformat() if rev.scheduled_end_date else None,
                "actual_start_date": rev.actual_start_date.isoformat() if rev.actual_start_date else None,
                "actual_end_date": rev.actual_end_date.isoformat() if rev.actual_end_date else None,
                "revision_notes": rev.revision_notes,
                "is_completed": rev.is_completed,
                "status_id": rev.status_id,
                "file_ids": rev.file_ids,
                "files": files_data,
                "created_at": rev.created_at.isoformat() if rev.created_at else None,
                "updated_at": rev.updated_at.isoformat() if rev.updated_at else None,
                "updated_by": rev.updated_by,
                "updated_by_name": f"{row[5]} {row[6]}" if row[5] else None
            }
    
    return latest_revisions


from src.app.database.drafting import DraftingSession, DraftingSessionNote  # add with other imports

async def _batch_load_drafting_sessions(db: AsyncSession, fab_ids: List[int]) -> dict:
    """Load the latest drafting session (and its notes) for each FAB."""
    # Fetch sessions ordered by latest first per fab
    session_rows = await db.execute(
        select(DraftingSession)
        .where(DraftingSession.fab_id.in_(fab_ids))
        .order_by(DraftingSession.fab_id, DraftingSession.id.desc())
    )
    sessions = session_rows.scalars().all()

    latest_by_fab = {}
    session_ids = []
    for s in sessions:
        if s.fab_id not in latest_by_fab:
            latest_by_fab[s.fab_id] = s
            session_ids.append(s.id)

    # Fetch notes for the chosen sessions
    notes_by_session = {}
    if session_ids:
        note_rows = await db.execute(
            select(DraftingSessionNote)
            .where(DraftingSessionNote.session_id.in_(session_ids))
            .order_by(DraftingSessionNote.timestamp.asc())
        )
        for n in note_rows.scalars().all():
            notes_by_session.setdefault(n.session_id, []).append({
                "timestamp": n.timestamp.isoformat() if n.timestamp else None,
                "action": n.action,
                "note": n.note,
                "sqft_drafted": n.sqft_drafted,
                "work_percentage_done": n.work_percentage_done,
            })

    # Build dict payload
    result = {}
    for fab_id, s in latest_by_fab.items():
        result[fab_id] = {
            "id": s.id,
            "fab_id": s.fab_id,
            "drafter_id": s.drafter_id,
            "status": s.status,
            "session_start_time": s.session_start_time.isoformat() if s.session_start_time else None,
            "session_end_time": s.session_end_time.isoformat() if s.session_end_time else None,
            "current_pause_start_time": s.current_pause_start_time.isoformat() if s.current_pause_start_time else None,
            "total_pause_duration": s.total_pause_duration,
            "total_time_spent": s.total_time_spent,
            "cumulative_sqft_drafted": s.cumulative_sqft_drafted,
            "work_percentage_done": s.work_percentage_done,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "notes": notes_by_session.get(s.id, []),
        }
    return result


async def _load_plans_for_fabs(db: AsyncSession, fab_ids: list[int]) -> dict[int, list[dict]]:
    if not fab_ids:
        return {}

    plans_result = await db.execute(
        select(ShopCutPlan).where(ShopCutPlan.fab_id.in_(fab_ids))
    )
    plans = plans_result.scalars().all()

    ws_ids = {p.workstation_id for p in plans}
    ps_ids = {p.planning_section_id for p in plans}
    user_ids = {p.user_id for p in plans}

    ws_map = {}
    if ws_ids:
        ws_result = await db.execute(select(WorkStation).where(WorkStation.id.in_(ws_ids)))
        ws_map = {w.id: w for w in ws_result.scalars().all()}

    ps_map = {}
    if ps_ids:
        ps_result = await db.execute(select(PlanningSection).where(PlanningSection.id.in_(ps_ids)))
        ps_map = {p.id: p for p in ps_result.scalars().all()}

    user_map = {}
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        user_map = {u.id: u for u in user_result.scalars().all()}

    by_fab = defaultdict(list)
    for p in plans:
        u = user_map.get(p.user_id)
        operator_name = None
        if u:
            operator_name = f"{u.first_name} {u.last_name}".strip() or u.username

        ws = ws_map.get(p.workstation_id)
        ps = ps_map.get(p.planning_section_id)

        by_fab[p.fab_id].append({
            "id": p.id,
            "sequence": p.sequence,
            "workstation_id": p.workstation_id,
            "workstation_name": getattr(ws, "name", None),
            "planning_section_id": p.planning_section_id,
            "plan_name": getattr(ps, "plan_name", None),
            "operator_id": p.user_id,
            "operator_name": operator_name,
            "estimated_hours": p.estimated_hours,
            "scheduled_start_date": p.scheduled_start_date,
            "actual_start_date": p.actual_start_date,
            "actual_end_date": p.actual_end_date,
            "work_percentage": p.work_percentage,
            "notes": p.notes,
        })

    return by_fab

@router.get("/resurface-schedule", response_model=SuccessResponse[dict])
async def get_resurface_schedule(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all FABs where:
    - fab_type is RESURFACE
    - shop_date_schedule is set (not null)

    Enriched with label fields for frontend display.
    """
    from sqlalchemy.orm import aliased

    SalesUser = aliased(User)

    base_query = (
        select(
            Fab,
            BusinessJob.name.label("job_name"),
            BusinessJob.job_number.label("job_number"),
            Account.name.label("account_name"),
            Account.account_number.label("account_number"),
            SalesUser.first_name.label("sales_first_name"),
            SalesUser.last_name.label("sales_last_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness_value"),
            Edge.name.label("edge_name"),
            Status.name.label("status_name"),
        )
        .select_from(Fab)
        .outerjoin(BusinessJob, Fab.job_id == BusinessJob.id)
        .outerjoin(Account, BusinessJob.account_id == Account.id)
        .outerjoin(SalesUser, Fab.sales_person_id == SalesUser.id)
        .outerjoin(StoneType, Fab.stone_type_id == StoneType.id)
        .outerjoin(StoneColor, Fab.stone_color_id == StoneColor.id)
        .outerjoin(StoneThickness, Fab.stone_thickness_id == StoneThickness.id)
        .outerjoin(Edge, Fab.edge_id == Edge.id)
        .outerjoin(Status, Fab.status_id == Status.value_id)
        .where(
            func.upper(sa.func.trim(Fab.fab_type)) == "RESURFACE",
            Fab.shop_date_schedule.isnot(None),
        )
    )

    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        base_query
        .order_by(Fab.shop_date_schedule.asc(), Fab.id.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    data = []
    for row in rows:
        fab = row[0]
        fab_dict = {
            k: (
                v.isoformat() if isinstance(v, (datetime, date))
                else (float(v) if isinstance(v, Decimal) else v)
            )
            for k, v in fab.__dict__.items()
            if not k.startswith("_")
        }

        sales_name = None
        if row.sales_first_name:
            sales_name = f"{row.sales_first_name} {row.sales_last_name}".strip()

        fab_dict["job_name"] = row.job_name
        fab_dict["job_number"] = row.job_number
        fab_dict["account_name"] = row.account_name
        fab_dict["account_number"] = row.account_number
        fab_dict["sales_person_name"] = sales_name
        fab_dict["stone_type_name"] = row.stone_type_name
        fab_dict["stone_color_name"] = row.stone_color_name
        fab_dict["stone_thickness_value"] = row.stone_thickness_value
        fab_dict["edge_name"] = row.edge_name
        fab_dict["status_name"] = row.status_name

        data.append(fab_dict)

    return success_response(
        {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": data
        },
        "Resurface schedule fetched successfully"
    )