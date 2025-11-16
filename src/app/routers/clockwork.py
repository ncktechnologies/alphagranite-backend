from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.clockwork import Clockwork
from src.app.interface.business_schemas import (
    ClockworkCreate,
    ClockworkUpdate,
    ClockworkResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/clockwork", response_model=SuccessResponse[ClockworkResponse], status_code=201)
async def save_clockwork(
    clockwork_data: ClockworkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save technician/drafter clockwork.
    Flow: Start date and time for template/draft, End date and time, 
    No of sqft completed (for entered duration), Status (completed), fab_id, table_name (e.g templatings)
    """
    
    # Validate fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == clockwork_data.fab_id))
    if not fab_result.scalar_one_or_none():
        raise error_response("Fab not found", 404)
    
    # Validate technician exists
    tech_result = await db.execute(select(User).where(User.id == clockwork_data.technician_id))
    if not tech_result.scalar_one_or_none():
        raise error_response("Technician/Drafter not found", 404)
    
    # Create clockwork entry
    clockwork = Clockwork(
        fab_id=clockwork_data.fab_id,
        technician_id=clockwork_data.technician_id,
        table_name=clockwork_data.table_name,
        table_id=clockwork_data.table_id,
        started_at=clockwork_data.started_at,
        completed_at=clockwork_data.completed_at,
        total_sqft_done=clockwork_data.total_sqft_done,
        notes=clockwork_data.notes,
        pause_reason=clockwork_data.pause_reason,
        created_at=datetime.now(),
        created_by=current_user.id
    )
    
    db.add(clockwork)
    await db.commit()
    await db.refresh(clockwork)
    
    return success_response(clockwork, "Clockwork saved successfully")


@router.put("/clockwork/{clockwork_id}", response_model=SuccessResponse[ClockworkResponse])
async def update_clockwork(
    clockwork_id: int,
    clockwork_data: ClockworkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update technician/drafter clockwork"""
    
    result = await db.execute(select(Clockwork).where(Clockwork.id == clockwork_id))
    clockwork = result.scalar_one_or_none()
    
    if not clockwork:
        raise error_response("Clockwork entry not found", 404)
    
    # Update fields
    update_data = clockwork_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clockwork, field, value)
    
    await db.commit()
    await db.refresh(clockwork)
    
    return success_response(clockwork, "Clockwork updated successfully")


@router.delete("/clockwork/{clockwork_id}", response_model=SuccessResponse[None])
async def delete_clockwork(
    clockwork_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete technician/drafter clockwork entry"""
    
    result = await db.execute(select(Clockwork).where(Clockwork.id == clockwork_id))
    clockwork = result.scalar_one_or_none()
    
    if not clockwork:
        raise error_response("Clockwork entry not found", 404)
    
    await db.delete(clockwork)
    await db.commit()
    
    return success_response(None, "Clockwork deleted successfully")


@router.get("/clockwork", response_model=SuccessResponse[List[ClockworkResponse]])
async def list_clockwork(
    technician_id: Optional[int] = Query(None, description="Filter by technician/drafter ID"),
    fab_id: Optional[int] = Query(None, description="Filter by fab ID"),
    table_name: Optional[str] = Query(None, description="Filter by table name (e.g., 'templatings', 'draftings')"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List technician/drafter clockwork entries.
    Can filter by technician_id, fab_id, and table_name.
    """
    
    query = select(Clockwork)
    
    # Apply filters
    if technician_id is not None:
        query = query.where(Clockwork.technician_id == technician_id)
    if fab_id is not None:
        query = query.where(Clockwork.fab_id == fab_id)
    if table_name:
        query = query.where(Clockwork.table_name == table_name)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Clockwork.created_at.desc())
    
    result = await db.execute(query)
    clockworks = result.scalars().all()
    
    return success_response(clockworks, "Clockwork entries fetched successfully")


@router.get("/clockwork/{clockwork_id}", response_model=SuccessResponse[ClockworkResponse])
async def get_clockwork(
    clockwork_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific clockwork entry by ID"""
    
    result = await db.execute(select(Clockwork).where(Clockwork.id == clockwork_id))
    clockwork = result.scalar_one_or_none()
    
    if not clockwork:
        raise error_response("Clockwork entry not found", 404)
    
    return success_response(clockwork, "Clockwork fetched successfully")
