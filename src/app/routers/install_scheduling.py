from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import InstallScheduling
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    InstallSchedulingCreate,
    InstallSchedulingUpdate,
    InstallSchedulingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/install-scheduling", response_model=SuccessResponse[InstallSchedulingResponse], status_code=201)
async def create_install_scheduling(
    install_data: InstallSchedulingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create install scheduling for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == install_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(InstallScheduling).where(InstallScheduling.fab_id == install_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("Install Scheduling already exists for this fab", 400)
    
    # Create install scheduling
    install_scheduling = InstallScheduling(
        fab_id=install_data.fab_id,
        scheduled_install_date=install_data.scheduled_install_date,
        scheduled_end_date=install_data.scheduled_end_date,
        total_sqft=install_data.total_sqft,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "install_scheduling"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(install_scheduling)
    await db.commit()
    await db.refresh(install_scheduling)
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            scheduled_install_date=install_scheduling.scheduled_install_date,
            scheduled_end_date=install_scheduling.scheduled_end_date,
            actual_install_date=install_scheduling.actual_install_date,
            total_sqft=install_scheduling.total_sqft,
            is_completed=install_scheduling.is_completed,
            status_id=install_scheduling.status_id,
            created_at=install_scheduling.created_at,
            updated_at=install_scheduling.updated_at,
            updated_by=install_scheduling.updated_by
        ),
        "Install Scheduling created successfully"
    )


@router.put("/install-scheduling/{install_scheduling_id}", response_model=SuccessResponse[InstallSchedulingResponse])
async def update_install_scheduling(
    install_scheduling_id: int,
    update_data: InstallSchedulingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update install scheduling"""
    
    result = await db.execute(select(InstallScheduling).where(InstallScheduling.id == install_scheduling_id))
    install_scheduling = result.scalar_one_or_none()
    
    if not install_scheduling:
        raise error_response("Install Scheduling not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(install_scheduling, key, value)
    
    install_scheduling.updated_at = datetime.now()
    install_scheduling.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(install_scheduling)
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            scheduled_install_date=install_scheduling.scheduled_install_date,
            scheduled_end_date=install_scheduling.scheduled_end_date,
            actual_install_date=install_scheduling.actual_install_date,
            total_sqft=install_scheduling.total_sqft,
            is_completed=install_scheduling.is_completed,
            status_id=install_scheduling.status_id,
            created_at=install_scheduling.created_at,
            updated_at=install_scheduling.updated_at,
            updated_by=install_scheduling.updated_by
        ),
        "Install Scheduling updated successfully"
    )


@router.get("/install-scheduling/fab/{fab_id}", response_model=SuccessResponse[InstallSchedulingResponse])
async def get_install_scheduling_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get install scheduling by fab ID"""
    
    result = await db.execute(select(InstallScheduling).where(InstallScheduling.fab_id == fab_id))
    install_scheduling = result.scalar_one_or_none()
    
    if not install_scheduling:
        raise error_response("Install Scheduling not found for this fab", 404)
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            scheduled_install_date=install_scheduling.scheduled_install_date,
            scheduled_end_date=install_scheduling.scheduled_end_date,
            actual_install_date=install_scheduling.actual_install_date,
            total_sqft=install_scheduling.total_sqft,
            is_completed=install_scheduling.is_completed,
            status_id=install_scheduling.status_id,
            created_at=install_scheduling.created_at,
            updated_at=install_scheduling.updated_at,
            updated_by=install_scheduling.updated_by
        ),
        "Install Scheduling retrieved successfully"
    )
