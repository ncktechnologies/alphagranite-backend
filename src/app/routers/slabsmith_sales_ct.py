from datetime import datetime, timedelta, date
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
import sqlalchemy as sa

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.slab_smith import SlabSmith
from src.app.database.sales_ct import SalesCT
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.interface.generated_schemas import Revision

from src.app.interface.business_schemas import (
    SlabSmithCreate,
    SlabSmithUpdate,
    SlabSmithResponse,
    SalesCTCreate,
    SalesCTUpdate,
    SalesCTRevisionCreate,
    SalesCTRevisionUpdate,
    SalesCTResponse,
    FabResponse, 
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response
from src.app.database.templating import Templating
from src.app.routers.fabs import (
    _build_fab_list_query,
    _convert_fab_row_to_dict,
    _batch_load_fab_related_data
)

router = APIRouter()


# ============ HELPER FUNCTIONS ============

def serialize_datetime_fields(obj) -> dict:
    """Convert SQLAlchemy model to dict with datetime fields as ISO strings"""
    from datetime import datetime as dt, date
    return {
        k: (v.isoformat() if isinstance(v, (dt, date)) else v)
        for k, v in obj.__dict__.items()
        if not k.startswith('_')
    }


# ============ SLAB SMITH ENDPOINTS ============

@router.post("/slabsmith", response_model=SuccessResponse[SlabSmithResponse], status_code=201)
async def create_slabsmith(
    slabsmith_data: SlabSmithCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new slab smith entry"""
    
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == slabsmith_data.fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)
    
    # Validate drafter exists
    drafter_result = await db.execute(select(User).where(User.id == slabsmith_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)
    
    # Create slab smith
    slabsmith = SlabSmith(
        fab_id=slabsmith_data.fab_id,
        slab_smith_type=slabsmith_data.slab_smith_type,
        drafter_id=slabsmith_data.drafter_id,
        start_date=slabsmith_data.start_date,
        end_date=slabsmith_data.end_date,
        total_sqft_completed=slabsmith_data.total_sqft_completed,
        file_ids=None,
        status_id=1,
        created_at=datetime.now(),
        updated_at=None,
        updated_by=None
    )
    
    db.add(slabsmith)
    await db.commit()
    await db.refresh(slabsmith)
    
    return success_response(serialize_datetime_fields(slabsmith), "Slab smith created successfully")


@router.put("/slabsmith/{slabsmith_id}", response_model=SuccessResponse[SlabSmithResponse])
async def update_slabsmith(
    slabsmith_id: int,
    slabsmith_data: SlabSmithUpdate = Body(
        ...,
        examples=[
            {
                "drafter_id": 12,
                "end_date": "2026-04-15T14:30:00",
                "total_sqft_completed": "150.5",
                "is_completed": False,
                "status_id": 1,
            }
        ],
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update slab smith entry"""
    
    result = await db.execute(select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found", 404)
    
    # Update fields
    update_data = slabsmith_data.model_dump(exclude_unset=True)

    # Validate drafter exists when reassigned
    if "drafter_id" in update_data:
        drafter_result = await db.execute(select(User).where(User.id == update_data["drafter_id"]))
        if not drafter_result.scalar_one_or_none():
            raise error_response("Drafter not found", 404)

    for field, value in update_data.items():
        setattr(slabsmith, field, value)
    
    slabsmith.updated_at = datetime.now()
    slabsmith.updated_by = current_user.id

    # If completed, move the related FAB to cut_list stage and save completion date
    if update_data.get("is_completed") is True:
        fab_result = await db.execute(select(Fab).where(Fab.id == slabsmith.fab_id))
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "cut_list"
            fab.next_stage = "final_programming"
            fab.slabsmith_completed_date = datetime.now()  # ADD THIS
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id

    await db.commit()
    await db.refresh(slabsmith)

    return success_response(serialize_datetime_fields(slabsmith), "Slab smith updated successfully")


@router.post("/slabsmith/{slabsmith_id}/complete", response_model=SuccessResponse[None])
async def mark_slabsmith_completed(
    slabsmith_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark slab smith as completed"""
    
    result = await db.execute(select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found", 404)
    
    # Mark as completed
    slabsmith.status_id = 3  # Completed status
    slabsmith.end_date = datetime.now()
    slabsmith.updated_at = datetime.now()
    slabsmith.updated_by = current_user.id
    slabsmith_completed_date = datetime.now() 
    
    # Update fab stage to next step (sales check)
    fab_result = await db.execute(select(Fab).where(Fab.id == slabsmith.fab_id))
    fab = fab_result.scalar_one_or_none()
    if fab:
        fab.current_stage = "sales_ct"
        fab.next_stage = "cut_list"  # Will be cut_list or revision based on review
        fab.slabsmith_completed_date = datetime.now()  
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Slab smith marked as completed")


@router.post("/slabsmith/{slabsmith_id}/add-file", response_model=SuccessResponse[None])
async def add_file_to_slabsmith(
    slabsmith_id: int,
    file_id: int,
    file_design: Optional[str] = None,
    stage_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add file to slab smith"""
    from src.app.database.file import File
    
    result = await db.execute(select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found", 404)
    
    # Update file record with metadata and uploader
    file_result = await db.execute(select(File).where(File.id == file_id))
    file_obj = file_result.scalar_one_or_none()
    if file_obj:
        if file_design:
            file_obj.file_design = file_design
        if stage_name:
            file_obj.stage_name = stage_name
        file_obj.uploaded_by = current_user.id
    
    # Add file ID to comma-separated list
    if slabsmith.file_ids:
        file_ids_list = slabsmith.file_ids.split(',')
        if str(file_id) not in file_ids_list:
            file_ids_list.append(str(file_id))
            slabsmith.file_ids = ','.join(file_ids_list)
    else:
        slabsmith.file_ids = str(file_id)
    
    slabsmith.updated_at = datetime.now()
    slabsmith.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(slabsmith)
    return success_response(None, "File added to slab smith successfully")


@router.delete("/slabsmith/{slabsmith_id}/file/{file_id}", response_model=SuccessResponse[None])
async def delete_file_from_slabsmith(
    slabsmith_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file from slab smith"""
    
    result = await db.execute(select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found", 404)
    
    # Remove file ID from comma-separated list
    if slabsmith.file_ids:
        file_ids_list = slabsmith.file_ids.split(',')
        if str(file_id) in file_ids_list:
            file_ids_list.remove(str(file_id))
            slabsmith.file_ids = ','.join(file_ids_list) if file_ids_list else None
    
    slabsmith.updated_at = datetime.now()
    slabsmith.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "File removed from slab smith successfully")


@router.get("/slabsmith/fab/{fab_id}", response_model=SuccessResponse[SlabSmithResponse])
async def get_slabsmith_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get slab smith by fab ID (returns latest if multiple exist)"""
    
    result = await db.execute(
        select(SlabSmith)
        .where(SlabSmith.fab_id == fab_id)
        .order_by(SlabSmith.id.desc())  # Get the latest one
        .limit(1)
    )
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found for this fab", 404)
    
    return success_response(serialize_datetime_fields(slabsmith), "Slab smith fetched successfully")


# ============ SALES CT / REVIEW ENDPOINTS ============

@router.post("/sales-ct", response_model=SuccessResponse[SalesCTResponse], status_code=201)
async def create_sales_ct(
    sales_ct_data: SalesCTCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a sales CT entry"""
    
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == sales_ct_data.fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)
    
    # Check if Sales CT already exists for this fab
    existing_sales_ct = await db.execute(
        select(SalesCT).where(SalesCT.fab_id == sales_ct_data.fab_id)
    )
    if existing_sales_ct.scalar_one_or_none():
        raise error_response("Sales CT already exists for this FAB", 409)
    
    try:
        # Create sales CT
        sales_ct = SalesCT(
            fab_id=sales_ct_data.fab_id,
            is_revision_needed=sales_ct_data.is_revision_needed,
            revision_reason=sales_ct_data.revision_reason,
            revision_type=sales_ct_data.revision_type if hasattr(sales_ct_data, 'revision_type') else None,
            is_revision_completed=None,
            no_of_revisions=None,
            current_revision_count=None,
            status_id=1,
            created_at=datetime.now(),
            updated_at=None,
            updated_by=None,
            # Fields from model definition
            slab_smith_type="",
            drafter_id=0,
            start_date=datetime.now(),
            end_date=datetime.now(),
            total_sqft_completed=None,
            file_ids=None
        )
        
        db.add(sales_ct)
        await db.commit()
        await db.refresh(sales_ct)
        
    except IntegrityError:
        await db.rollback()
        raise error_response("Sales CT already exists for this FAB", 409)

    revision_count_result = await db.execute(
        select(func.count(Revision.id)).where(Revision.fab_id == sales_ct.fab_id)
    )
    revision_count = int(revision_count_result.scalar() or 0)

    data = serialize_datetime_fields(sales_ct)
    data["current_revision_count"] = str(revision_count)

    return success_response(data, "Sales CT created successfully")


@router.put("/sales-ct/{sales_ct_id}/review-no", response_model=SuccessResponse[None])
async def set_review_needed_no(
    sales_ct_id: int,
    revenue: Optional[float] = None,
    status_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set review needed as No, add revenue and status"""
    
    result = await db.execute(select(SalesCT).where(SalesCT.id == sales_ct_id))
    sales_ct = result.scalar_one_or_none()
    
    if not sales_ct:
        raise error_response("Sales CT not found", 404)
    
    sales_ct.is_revision_needed = False
    if status_id:
        sales_ct.status_id = status_id
    
    sales_ct.updated_at = datetime.now()
    sales_ct.updated_by = current_user.id
    
    # Update fab to next stage (cut list) and save completion date
    fab_result = await db.execute(select(Fab).where(Fab.id == sales_ct.fab_id))
    fab = fab_result.scalar_one_or_none()
    if fab:
        fab.current_stage = "cut_list"
        fab.next_stage = "final_programming"
        fab.sales_ct_completed_date = datetime.now()  # ADD THIS
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Review set to No successfully")

@router.put("/sales-ct/{sales_ct_id}/review-yes", response_model=SuccessResponse[None])
async def set_review_needed_yes(
    sales_ct_id: int,
    revision_reason: str,
    revision_type: Optional[str] = None,
    file_ids: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set review needed as Yes, add revision reason, revision type and files (optional)"""
    
    result = await db.execute(select(SalesCT).where(SalesCT.id == sales_ct_id))
    sales_ct = result.scalar_one_or_none()
    
    if not sales_ct:
        raise error_response("Sales CT not found", 404)
    
    sales_ct.is_revision_needed = True
    sales_ct.is_revision_completed = False
    sales_ct.revision_reason = revision_reason
    
    if revision_type:
        sales_ct.revision_type = revision_type
    
    # Increment revision count
    if sales_ct.current_revision_count:
        count = int(sales_ct.current_revision_count) + 1
        sales_ct.current_revision_count = str(count)
    else:
        sales_ct.current_revision_count = "0"
    
    if file_ids:
        sales_ct.file_ids = file_ids
    
    sales_ct.updated_at = datetime.now()
    sales_ct.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Review set to Yes with revision reason added")



@router.put("/sales-ct/{sales_ct_id}/revision", response_model=SuccessResponse[None])
async def update_revision_type(
    sales_ct_id: int,
    revision_data: SalesCTRevisionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update revision type. Can set revision status as completed, add draft note.
    Track revision count, type, and dates
    """
    
    result = await db.execute(select(SalesCT).where(SalesCT.id == sales_ct_id))
    sales_ct = result.scalar_one_or_none()
    
    if not sales_ct:
        raise error_response("Sales CT not found", 404)
    
    # Update revision_type if provided
    if revision_data.revision_type:
        sales_ct.revision_type = revision_data.revision_type
    
    if revision_data.is_revision_completed:
        sales_ct.is_revision_completed = True
        sales_ct.status_id = 3  # Completed
        
        # Update fab to revision stage (will loop back to sales_check)
        fab_result = await db.execute(select(Fab).where(Fab.id == sales_ct.fab_id))
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "revision"
            fab.next_stage = "sales_check"  # Revision loops back to sales check
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id
    
    sales_ct.updated_at = datetime.now()
    sales_ct.updated_by = current_user.id
    
    await db.commit()
    
    return success_response(None, "Revision updated successfully")


@router.get("/sales-ct/fab/{fab_id}", response_model=SuccessResponse[SalesCTResponse])
async def get_sales_ct_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales CT by fab ID, ordered by newest first"""
    
    result = await db.execute(
        select(SalesCT)
        .where(SalesCT.fab_id == fab_id)
        .order_by(SalesCT.created_at.desc())
    )
    sales_ct = result.scalar_one_or_none()
    
    if not sales_ct:
        raise error_response("Sales CT not found for this fab", 404)

    revision_count_result = await db.execute(
        select(func.count(Revision.id)).where(Revision.fab_id == fab_id)
    )
    revision_count = int(revision_count_result.scalar() or 0)

    data = serialize_datetime_fields(sales_ct)
    data["current_revision_count"] = str(revision_count)

    return success_response(data, "Sales CT fetched successfully")

@router.get("/sales-ct", response_model=SuccessResponse[List[SalesCTResponse]])
async def get_all_sales_ct(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sales CT entries ordered by completion date (oldest first)"""
    
    result = await db.execute(
        select(SalesCT, Fab.sales_ct_completed_date)
        .join(Fab, SalesCT.fab_id == Fab.id)
        .order_by(Fab.sales_ct_completed_date.asc().nulls_last())
    )
    sales_cts = [row[0] for row in result.all()]

    fab_ids = [sct.fab_id for sct in sales_cts if sct.fab_id is not None]
    revision_counts = {}
    if fab_ids:
        counts_result = await db.execute(
            select(Revision.fab_id, func.count(Revision.id))
            .where(Revision.fab_id.in_(fab_ids))
            .group_by(Revision.fab_id)
        )
        revision_counts = {
            fab_id: int(count or 0)
            for fab_id, count in counts_result.all()
        }

    data = []
    for sct in sales_cts:
        item = serialize_datetime_fields(sct)
        item["current_revision_count"] = str(revision_counts.get(sct.fab_id, 0))
        data.append(item)
    
    return success_response(
        data,
        "Sales CT entries fetched successfully"
    )

@router.get("/stages/slabsmith/pending", response_model=SuccessResponse[dict])
async def get_pending_slabsmith_fab_ids(
    search: Optional[str] = None,
    type: Optional[str] = Query(None, description="Field to apply search to: fab_id, job_number, job_name, account_name"),
    date_filter: Optional[str] = Query(
        None,
        description="Predefined date filter: today, this_week, last_week, this_month, last_month, next_week, next_month",
    ),
    draft_completed_start: Optional[date] = Query(
        None,
        description="Filter by draft_completed_date on or after this date (YYYY-MM-DD)",
    ),
    draft_completed_end: Optional[date] = Query(
        None,
        description="Filter by draft_completed_date on or before this date (YYYY-MM-DD)",
    ),
    fab_type: Optional[str] = None,
    drafter_id: Optional[int] = Query(None, description="Filter by drafter/programmer ID"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get FABs where:
    - current_stage is sales_ct (SCT)
    - slab_smith_ag_needed or slab_smith_cust_needed is true
    - slabsmith_completed_date is null
    Optional search by FAB ID or Job Number.
    """
    filters = [
        (Fab.current_stage == "sales_ct") | (Fab.current_stage == "revision"),
        (Fab.slab_smith_ag_needed.is_(True)) | (Fab.slab_smith_cust_needed.is_(True)),
        Fab.slabsmith_completed_date.is_(None),
    ]

    # Date filter on Fab.draft_completed_date
    if date_filter:
        valid_filters = {
            "today", "this_week", "last_week",
            "this_month", "last_month",
            "next_week", "next_month"
        }
        if date_filter not in valid_filters:
            raise error_response("Invalid date_filter", 400)

        today = datetime.now().date()
        start_this_week = today - timedelta(days=today.weekday())

        def month_start(d):
            return d.replace(day=1)

        def add_months(d, months):
            year = d.year + ((d.month - 1 + months) // 12)
            month = ((d.month - 1 + months) % 12) + 1
            return d.replace(year=year, month=month, day=1)

        start = end = None

        if date_filter == "today":
            start = today
            end = today + timedelta(days=1)
        elif date_filter == "this_week":
            start = start_this_week
            end = start_this_week + timedelta(days=7)
        elif date_filter == "last_week":
            start = start_this_week - timedelta(days=7)
            end = start_this_week
        elif date_filter == "next_week":
            start = start_this_week + timedelta(days=7)
            end = start + timedelta(days=7)
        elif date_filter == "this_month":
            start = month_start(today)
            end = add_months(start, 1)
        elif date_filter == "last_month":
            end = month_start(today)
            start = add_months(end, -1)
        elif date_filter == "next_month":
            start = add_months(month_start(today), 1)
            end = add_months(start, 1)
        if start is not None:
            start_dt = datetime.combine(start, datetime.min.time())
            if end is not None:
                end_dt = datetime.combine(end, datetime.min.time())
                filters.append(Fab.draft_completed_date >= start_dt)
                filters.append(Fab.draft_completed_date < end_dt)
            else:
                filters.append(Fab.draft_completed_date >= start_dt)

    if draft_completed_start and draft_completed_end and draft_completed_start > draft_completed_end:
        raise error_response("draft_completed_start cannot be after draft_completed_end", 400)

    if draft_completed_start:
        filters.append(Fab.draft_completed_date >= datetime.combine(draft_completed_start, datetime.min.time()))
    if draft_completed_end:
        filters.append(Fab.draft_completed_date < datetime.combine(draft_completed_end + timedelta(days=1), datetime.min.time()))

    # FAB Type filter
    if fab_type:
        filters.append(Fab.fab_type.ilike(f"%{fab_type}%"))

    if drafter_id is not None:
        filters.append(Fab.drafter_id == drafter_id)

    # Build latest templating subquery (for consistent FAB payload)
    latest_templating = (
        select(Templating)
        .where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc())
        .limit(1)
        .lateral("latest_templating")
    )

    base_query = _build_fab_list_query(
        job_id=None,
        fab_type=fab_type,
        sales_person_id=None,
        status_id=None,
        current_stage=None,
        next_stage=None,
        search=None,
        templating_fab_ids=None,
        latest_templating=latest_templating,
        shop_date_start=None,
        shop_date_end=None,
        template_completed_start=None,
        template_completed_end=None,
        predraft_completed_start=None,
        predraft_completed_end=None,
        draft_completed_start=None,
        draft_completed_end=None,
        sct_completed_start=None,
        sct_completed_end=None,
        date_filter=None
    ).where(*filters)

    # Build search filter based on type
    if search and type:
        if type == "fab_id":
            search_filter = sa.cast(Fab.id, sa.String) == search
        elif type == "job_number":
            search_filter = BusinessJob.job_number == search
        elif type == "job_name":
            search_filter = BusinessJob.name.ilike(f"%{search}%")
        elif type == "account_name":
            search_filter = Account.name.ilike(f"%{search}%")
        else:
            search_filter = None
    else:
        search_filter = None

    if search_filter is not None:
        base_query = base_query.where(search_filter)
    elif search:
        search_term = f"%{search}%"
        base_query = base_query.where(
            or_(
                sa.cast(Fab.id, sa.String) == search,
                BusinessJob.name.ilike(search_term),
                BusinessJob.job_number == search
            )
        )

    count_query = (
        select(func.count(Fab.id))
        .select_from(Fab)
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
        .join(Account, BusinessJob.account_id == Account.id, isouter=True)
        .where(*filters)
    )
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

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = base_query.order_by(sa.asc(Fab.draft_completed_date).nulls_last()).offset(skip).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    fabs = [_convert_fab_row_to_dict(row) for row in rows]
    await _batch_load_fab_related_data(db, fabs)

    page = (skip // limit) + 1 if limit > 0 else 1
    return success_response(
        {
            "total": total,
            "page": page,
            "per_page": limit,
            "data": fabs
        },
        "Pending Slabsmith FABs fetched successfully"
    )
