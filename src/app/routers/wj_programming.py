from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import WJProgramming
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    WJProgrammingCreate,
    WJProgrammingUpdate,
    WJProgrammingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/wj-programming", response_model=SuccessResponse[WJProgrammingResponse], status_code=201)
async def create_wj_programming(
    wj_data: WJProgrammingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create WJ programming for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == wj_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if drafter exists
    drafter_result = await db.execute(select(User).where(User.id == wj_data.drafter_id))
    if not drafter_result.scalar_one_or_none():
        raise error_response("Drafter not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(WJProgramming).where(WJProgramming.fab_id == wj_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("WJ Programming already exists for this fab", 400)
    
    # Create WJ programming
    wj_programming = WJProgramming(
        fab_id=wj_data.fab_id,
        drafter_id=wj_data.drafter_id,
        scheduled_start_date=wj_data.scheduled_start_date,
        scheduled_end_date=wj_data.scheduled_end_date,
        total_ln_ft=wj_data.total_ln_ft,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "wj_programmings"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(wj_programming)
    await db.commit()
    await db.refresh(wj_programming)
    
    return success_response(
        WJProgrammingResponse(
            id=wj_programming.id,
            fab_id=wj_programming.fab_id,
            drafter_id=wj_programming.drafter_id,
            scheduled_start_date=wj_programming.scheduled_start_date,
            scheduled_end_date=wj_programming.scheduled_end_date,
            drafter_start_date=wj_programming.drafter_start_date,
            drafter_end_date=wj_programming.drafter_end_date,
            no_of_pieces=wj_programming.no_of_pieces,
            total_ln_ft=wj_programming.total_ln_ft,
            is_completed=wj_programming.is_completed,
            status_id=wj_programming.status_id,
            created_at=wj_programming.created_at,
            updated_at=wj_programming.updated_at,
            updated_by=wj_programming.updated_by
        ),
        "WJ Programming created successfully"
    )


@router.put("/wj-programming/{wj_programming_id}", response_model=SuccessResponse[WJProgrammingResponse])
async def update_wj_programming(
    wj_programming_id: int,
    update_data: WJProgrammingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update WJ programming"""
    
    result = await db.execute(select(WJProgramming).where(WJProgramming.id == wj_programming_id))
    wj_programming = result.scalar_one_or_none()
    
    if not wj_programming:
        raise error_response("WJ Programming not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(wj_programming, key, value)
    
    wj_programming.updated_at = datetime.now()
    wj_programming.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(wj_programming)
    
    return success_response(
        WJProgrammingResponse(
            id=wj_programming.id,
            fab_id=wj_programming.fab_id,
            drafter_id=wj_programming.drafter_id,
            scheduled_start_date=wj_programming.scheduled_start_date,
            scheduled_end_date=wj_programming.scheduled_end_date,
            drafter_start_date=wj_programming.drafter_start_date,
            drafter_end_date=wj_programming.drafter_end_date,
            no_of_pieces=wj_programming.no_of_pieces,
            total_ln_ft=wj_programming.total_ln_ft,
            is_completed=wj_programming.is_completed,
            status_id=wj_programming.status_id,
            created_at=wj_programming.created_at,
            updated_at=wj_programming.updated_at,
            updated_by=wj_programming.updated_by
        ),
        "WJ Programming updated successfully"
    )


@router.get("/wj-programming/fab/{fab_id}", response_model=SuccessResponse[WJProgrammingResponse])
async def get_wj_programming_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get WJ programming by fab ID"""
    
    result = await db.execute(select(WJProgramming).where(WJProgramming.fab_id == fab_id))
    wj_programming = result.scalar_one_or_none()
    
    if not wj_programming:
        raise error_response("WJ Programming not found for this fab", 404)
    
    return success_response(
        WJProgrammingResponse(
            id=wj_programming.id,
            fab_id=wj_programming.fab_id,
            drafter_id=wj_programming.drafter_id,
            scheduled_start_date=wj_programming.scheduled_start_date,
            scheduled_end_date=wj_programming.scheduled_end_date,
            drafter_start_date=wj_programming.drafter_start_date,
            drafter_end_date=wj_programming.drafter_end_date,
            no_of_pieces=wj_programming.no_of_pieces,
            total_ln_ft=wj_programming.total_ln_ft,
            is_completed=wj_programming.is_completed,
            status_id=wj_programming.status_id,
            created_at=wj_programming.created_at,
            updated_at=wj_programming.updated_at,
            updated_by=wj_programming.updated_by
        ),
        "WJ Programming retrieved successfully"
    )
