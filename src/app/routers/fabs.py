from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

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
from src.app.interface.business_schemas import (
    FabCreate, FabUpdate, FabResponse,
)
from src.app.interface.response_wrappers import SuccessResponse, error_response, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()

# Define the fab workflow stages in order (based on client workflow)
FAB_STAGES = [
    "fab_created",              # Stage 1: Fab Created
    "templating",               # Stage 2: Templating
    "templating_technician",    # Stage 3: Templating Technician Assignment
    "pre_draft",                # Stage 4: Pre-Draft
    "drafting",                 # Stage 5: Drafting
    "drafting_review",          # Stage 6: Drafting Review
    "drafting_revision",        # Stage 7: Drafting Revision
    "shop_production"           # Stage 8: Shop Production (final stage)
]

def get_next_stage(current_stage: str) -> Optional[str]:
    """
    Get the next stage in the fab workflow.
    Returns None if current stage is the last stage (shop_production).
    """
    if not current_stage or current_stage == "fab_created":
        return "templating"
    
    try:
        current_index = FAB_STAGES.index(current_stage)
        next_index = current_index + 1
        
        if next_index < len(FAB_STAGES):
            return FAB_STAGES[next_index]
        
        return None  # Last stage, no next stage
    except ValueError:
        # Current stage not in list, default to templating
        return "templating"


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
        raise error_response("Job not found", 404)
    
    # Sales person validation
    sales_person = await db.get(User, fab_data.sales_person_id)
    if not sales_person:
        raise error_response("Sales person not found", 404)
    
    # Stone type validation
    stone_type = await db.get(StoneType, fab_data.stone_type_id)
    if not stone_type:
        raise error_response("Stone type not found", 404)
    
    # Stone color validation
    stone_color = await db.get(StoneColor, fab_data.stone_color_id)
    if not stone_color:
        raise error_response("Stone color not found", 404)
    
    # Stone thickness validation
    stone_thickness = await db.get(StoneThickness, fab_data.stone_thickness_id)
    if not stone_thickness:
        raise error_response("Stone thickness not found", 404)
    
    # Edge validation
    edge = await db.get(Edge, fab_data.edge_id)
    if not edge:
        raise error_response("Edge not found", 404)
    
    # Create the fab and let it be on fab_created stage
    fab_dict = fab_data.model_dump()
    
    # Set default total_sqft to 1 if not provided (as per client requirement)
    if "total_sqft" not in fab_dict or fab_dict["total_sqft"] is None:
        fab_dict["total_sqft"] = 1.0
    
    fab = Fab(
        **fab_dict,
        current_stage="fab_created",
        next_stage="templating",  # Next stage after creation
        status_id=1,  # Active/Created status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(fab)
    await db.commit()
    await db.refresh(fab)
    
    # Get the created fab with related data
    return await get_fab(fab.id, db, current_user)


@router.get("/fabs", response_model=List[FabResponse])
async def get_fabs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    fab_type: Optional[str] = Query(None, description="Filter by fab type"),
    sales_person_id: Optional[int] = Query(None, description="Filter by sales person ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    current_stage: Optional[str] = Query(None, description="Filter by current stage"),
    next_stage: Optional[str] = Query(None, description="Filter by next stage"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fabs with optional filtering"""
    
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
    
    # Fetch fab_notes for all FABs
    for fab_dict in fabs:
        fab_notes = await get_fab_notes(db, fab_dict["id"])
        fab_dict["fab_notes"] = fab_notes
    
    return success_response(fabs, "Fabs fetched successfully")


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
        raise error_response("Fab not found", 404)
    
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
    
    # Determine success message based on stage
    message = "Fab fetched successfully"
    if fab_dict.get("current_stage") == "fab_created" and fab_dict.get("updated_at") is None:
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
    
    return success_response(fabs, f"Found {len(fabs)} FABs for job {job_id}")
