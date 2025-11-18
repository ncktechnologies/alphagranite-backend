from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.business_job import BusinessJob
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
    "fab_created",          # Stage 1: Fab Created
    "templating",           # Stage 2: Templating Queue
    "pre_draft_review",     # Stage 3: Pre-Draft Review
    "drafting",             # Stage 4: CAD/Drafting Department
    "sales_check",          # Stage 5: Sales Department Review
    "revision",             # Stage 6: Revisions Queue (loops back to sales_check)
    "cut_list",             # Stage 7: Cut List Scheduling
    "final_programming",    # Stage 8: Final Programming
    "shop_planning"         # Stage 9: Shop Planning (final stage)
]

def get_next_stage(current_stage: str) -> Optional[str]:
    """
    Get the next stage in the fab workflow.
    Special handling for revision loop: revision -> sales_check
    Returns None if current stage is the last stage (shop_planning).
    """
    if not current_stage or current_stage == "fab_created":
        return "fab_created"
    
    # Special case: revision always goes back to sales_check
    if current_stage == "revision":
        return "sales_check"
    
    try:
        current_index = FAB_STAGES.index(current_stage)
        # Skip revision stage in normal flow (it's only entered from sales_check)
        next_index = current_index + 1
        if current_index == FAB_STAGES.index("sales_check"):
            # From sales_check, skip revision and go to cut_list (normal approval flow)
            next_index = FAB_STAGES.index("cut_list")
        
        if next_index < len(FAB_STAGES) and FAB_STAGES[next_index] != "revision":
            return FAB_STAGES[next_index]
        
        return None  # Last stage, no next stage
    except ValueError:
        # Current stage not in list, default to fab_created
        return "fab_created"


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fabs with optional filtering"""
    
    # Use aliased User for sales_person and technician to avoid conflicts
    from sqlalchemy.orm import aliased
    TechnicianUser = aliased(User)
    
    # Build query with joins to get related data including templating
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        Templating.schedule_start_date.label("templating_schedule_start_date"),
        Templating.schedule_due_date.label("templating_schedule_due_date"),
        Templating.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name")
    ).select_from(Fab)
    
    # Join with related tables
    query = query.join(User, Fab.sales_person_id == User.id, isouter=True)
    query = query.join(StoneType, Fab.stone_type_id == StoneType.id, isouter=True)
    query = query.join(StoneColor, Fab.stone_color_id == StoneColor.id, isouter=True)
    query = query.join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id, isouter=True)
    query = query.join(Edge, Fab.edge_id == Edge.id, isouter=True)
    query = query.join(Templating, Fab.id == Templating.fab_id, isouter=True)
    query = query.join(TechnicianUser, Templating.technician_id == TechnicianUser.id, isouter=True)
    
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
        
        # Convert to dict and serialize datetime objects
        fab_dict = {k: v.isoformat() if isinstance(v, datetime) else v 
                    for k, v in fab.__dict__.items() if not k.startswith('_')}
        fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
        fab_dict["stone_type_name"] = stone_type_name
        fab_dict["stone_color_name"] = stone_color_name
        fab_dict["stone_thickness_value"] = stone_thickness_value
        fab_dict["edge_name"] = edge_name
        
        # Add templating data
        fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
        fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
        fab_dict["templating_notes"] = templating_notes
        fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
        
        # Add next stage
        fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
        
        fabs.append(fab_dict)
    
    return success_response(fabs, "Fabs fetched successfully")


@router.get("/fabs/{fab_id}", response_model=SuccessResponse[FabResponse])
async def get_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific fab by ID with related data"""
    # Use a join query to get all related data in one go
    # Use aliased User for sales_person and technician to avoid conflicts
    from sqlalchemy.orm import aliased
    TechnicianUser = aliased(User)
    
    query = select(
        Fab,
        User.first_name.label("sales_person_first_name"),
        User.last_name.label("sales_person_last_name"),
        StoneType.name.label("stone_type_name"),
        StoneColor.name.label("stone_color_name"),
        StoneThickness.thickness.label("stone_thickness_value"),
        Edge.name.label("edge_name"),
        Templating.schedule_start_date.label("templating_schedule_start_date"),
        Templating.schedule_due_date.label("templating_schedule_due_date"),
        Templating.notes.label("templating_notes"),
        TechnicianUser.first_name.label("technician_first_name"),
        TechnicianUser.last_name.label("technician_last_name")
    ).select_from(Fab).where(Fab.id == fab_id)
    
    # Join with related tables
    query = query.join(User, Fab.sales_person_id == User.id, isouter=True)
    query = query.join(StoneType, Fab.stone_type_id == StoneType.id, isouter=True)
    query = query.join(StoneColor, Fab.stone_color_id == StoneColor.id, isouter=True)
    query = query.join(StoneThickness, Fab.stone_thickness_id == StoneThickness.id, isouter=True)
    query = query.join(Edge, Fab.edge_id == Edge.id, isouter=True)
    query = query.join(Templating, Fab.id == Templating.fab_id, isouter=True)
    query = query.join(TechnicianUser, Templating.technician_id == TechnicianUser.id, isouter=True)
    
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
    
    # Convert to dict and add related names
    fab_dict = {k: v.isoformat() if isinstance(v, datetime) else v 
                for k, v in fab.__dict__.items() if not k.startswith('_')}
    fab_dict["sales_person_name"] = f"{sales_person_first_name} {sales_person_last_name}" if sales_person_first_name else None
    fab_dict["stone_type_name"] = stone_type_name
    fab_dict["stone_color_name"] = stone_color_name
    fab_dict["stone_thickness_value"] = stone_thickness_value
    fab_dict["edge_name"] = edge_name
    
    # Add templating data
    fab_dict["templating_schedule_start_date"] = templating_schedule_start_date.isoformat() if templating_schedule_start_date else None
    fab_dict["templating_schedule_due_date"] = templating_schedule_due_date.isoformat() if templating_schedule_due_date else None
    fab_dict["templating_notes"] = templating_notes
    fab_dict["technician_name"] = f"{technician_first_name} {technician_last_name}" if technician_first_name else None
    
    # Add next stage to response
    fab_dict["next_stage"] = get_next_stage(fab_dict.get("current_stage"))
    
    # Determine success message based on stage
    message = "Fab fetched successfully"
    if fab_dict.get("current_stage") == "fab_created" and fab_dict.get("updated_at") is None:
        # Just created (no updates yet)
        message = f"FAB {fab_dict['id']} submitted successfully for review!"
    
    return success_response(fab_dict, message)


@router.put("/fabs/{fab_id}", response_model=FabResponse)
async def update_fab(
    fab_id: int,
    fab_data: FabUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a fab"""
    
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
    
    # Update fields
    update_data = fab_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fab, field, value)
    
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(fab)
    
    return fab


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


@router.get("/jobs/{job_id}/fabs", response_model=List[FabResponse])
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
    
    query = select(Fab).where(Fab.job_id == job_id)
    query = query.offset(skip).limit(limit).order_by(Fab.created_at.desc())
    
    result = await db.execute(query)
    fabs = result.scalars().all()
    
    return fabs
