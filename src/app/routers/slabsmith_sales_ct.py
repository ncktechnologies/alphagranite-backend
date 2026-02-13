from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
import sqlalchemy as sa

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.slab_smith import SlabSmith
from src.app.database.sales_ct import SalesCT
from src.app.database.business_job import BusinessJob

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
    slabsmith_data: SlabSmithUpdate,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add file to slab smith"""
    
    result = await db.execute(select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("Slab smith not found", 404)
    
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
    
    return success_response(serialize_datetime_fields(sales_ct), "Sales CT created successfully")


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
        sales_ct.current_revision_count = "1"
    
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
    
    return success_response(serialize_datetime_fields(sales_ct), "Sales CT fetched successfully")

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
    
    return success_response(
        [serialize_datetime_fields(sct) for sct in sales_cts],
        "Sales CT entries fetched successfully"
    )

@router.get("/stages/slabsmith/pending", response_model=SuccessResponse[dict])
async def get_pending_slabsmith_fab_ids(
    search: Optional[str] = None,
    date_filter: Optional[str] = None,
    fab_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get FABs where:
    - current_stage is sales_ct (SCT)
    - slab_smith_ag_needed is true
    - slabsmith_completed_date is null
    Optional search by FAB ID or Job Number.
    """
    filters = [
        (Fab.current_stage == "sales_ct") | (Fab.current_stage == "revision"),
        Fab.slab_smith_ag_needed.is_(True),
        Fab.slabsmith_completed_date.is_(None),
    ]

    # Date filter on Fab.draft_completed_date
    if date_filter:
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
        elif date_filter == "next":
            start = today + timedelta(days=1)

        if start:
            start_dt = datetime.combine(start, datetime.min.time())
            if end:
                end_dt = datetime.combine(end, datetime.min.time())
                filters.append(Fab.draft_completed_date >= start_dt)
                filters.append(Fab.draft_completed_date < end_dt)
            else:
                filters.append(Fab.draft_completed_date >= start_dt)

    # FAB Type filter
    if fab_type:
        filters.append(Fab.fab_type == fab_type)

    latest_slabsmith_id = (
        select(func.max(SlabSmith.id))
        .where(SlabSmith.fab_id == Fab.id)
        .correlate(Fab)
        .scalar_subquery()
    )

    base_query = (
        select(
            Fab,
            BusinessJob.job_number,
            BusinessJob.name,
            SlabSmith.drafter_id.label("drafter_id"),
            User.first_name.label("drafter_first_name"),
            User.last_name.label("drafter_last_name"),
        )
        .select_from(Fab)
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
        .join(SlabSmith, SlabSmith.id == latest_slabsmith_id, isouter=True)
        .join(User, User.id == SlabSmith.drafter_id, isouter=True)
        .where(*filters)
    )

    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(
            or_(
                sa.cast(Fab.id, sa.String).ilike(search_term),
                BusinessJob.job_number.ilike(search_term)
            )
        )

    count_query = (
        select(func.count(Fab.id))
        .select_from(Fab)
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)
        .where(*filters)
    )
    if search:
        count_query = count_query.where(
            or_(
                sa.cast(Fab.id, sa.String).ilike(search_term),
                BusinessJob.job_number.ilike(search_term)
            )
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = base_query.order_by(Fab.id.asc()).offset(skip).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    data: List[FabResponse] = []
    for fab, _, _, drafter_id, drafter_first_name, drafter_last_name in rows:
        payload = serialize_datetime_fields(fab)
        if isinstance(payload.get("notes"), str):
            payload["notes"] = [payload["notes"]] if payload["notes"] else []

        payload["drafter_id"] = drafter_id
        if drafter_first_name or drafter_last_name:
            payload["drafter_name"] = f"{drafter_first_name or ''} {drafter_last_name or ''}".strip()
        else:
            payload["drafter_name"] = None

        data.append(FabResponse.model_validate(payload))

    page = (skip // limit) + 1 if limit > 0 else 1
    return success_response(
        {
            "total": total,
            "page": page,
            "per_page": limit,
            "data": data
        },
        "Pending Slabsmith FABs fetched successfully"
    )
