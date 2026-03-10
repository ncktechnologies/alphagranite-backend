from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import InstallCompletion
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    InstallCompletionCreate,
    InstallCompletionUpdate,
    InstallCompletionResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/install-completion", response_model=SuccessResponse[InstallCompletionResponse], status_code=201)
async def create_install_completion(
    install_data: InstallCompletionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create install completion record for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == install_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if installer exists
    installer_result = await db.execute(select(User).where(User.id == install_data.installer_id))
    if not installer_result.scalar_one_or_none():
        raise error_response("Installer not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(InstallCompletion).where(InstallCompletion.fab_id == install_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("Install Completion already exists for this fab", 400)
    
    # Create install completion
    install_completion = InstallCompletion(
        fab_id=install_data.fab_id,
        installer_id=install_data.installer_id,
        install_date=install_data.install_date,
        completion_date=install_data.completion_date,
        total_sqft_installed=install_data.total_sqft_installed,
        customer_signature=install_data.customer_signature,
        completion_notes=install_data.completion_notes,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage - mark as completed
    fab.current_stage = "install_completions"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(install_completion)
    await db.commit()
    await db.refresh(install_completion)
    
    # If install is marked complete, move FAB to install_completion stage
    if install_completion.is_completed:
        fab_result = await db.execute(
            select(Fab).where(Fab.id == install_completion.fab_id)
        )
        fab = fab_result.scalar_one_or_none()
        if fab:
            fab.current_stage = "install_completion"
            fab.next_stage = None  # final stage in workflow
            fab.updated_at = datetime.now()
            fab.updated_by = current_user.id
    
    return success_response(
        InstallCompletionResponse(
            id=install_completion.id,
            fab_id=install_completion.fab_id,
            installer_id=install_completion.installer_id,
            install_date=install_completion.install_date,
            completion_date=install_completion.completion_date,
            total_sqft_installed=install_completion.total_sqft_installed,
            customer_signature=install_completion.customer_signature,
            completion_notes=install_completion.completion_notes,
            is_completed=install_completion.is_completed,
            status_id=install_completion.status_id,
            created_at=install_completion.created_at,
            updated_at=install_completion.updated_at,
            updated_by=install_completion.updated_by
        ),
        "Install Completion created successfully"
    )


@router.put("/install-completion/{install_completion_id}", response_model=SuccessResponse[InstallCompletionResponse])
async def update_install_completion(
    install_completion_id: int,
    update_data: InstallCompletionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update install completion"""
    
    result = await db.execute(select(InstallCompletion).where(InstallCompletion.id == install_completion_id))
    install_completion = result.scalar_one_or_none()
    
    if not install_completion:
        raise error_response("Install Completion not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(install_completion, key, value)
    
    install_completion.updated_at = datetime.now()
    install_completion.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(install_completion)
    
    return success_response(
        InstallCompletionResponse(
            id=install_completion.id,
            fab_id=install_completion.fab_id,
            installer_id=install_completion.installer_id,
            install_date=install_completion.install_date,
            completion_date=install_completion.completion_date,
            total_sqft_installed=install_completion.total_sqft_installed,
            customer_signature=install_completion.customer_signature,
            completion_notes=install_completion.completion_notes,
            is_completed=install_completion.is_completed,
            status_id=install_completion.status_id,
            created_at=install_completion.created_at,
            updated_at=install_completion.updated_at,
            updated_by=install_completion.updated_by
        ),
        "Install Completion updated successfully"
    )


@router.get("/install-completion/fab/{fab_id}", response_model=SuccessResponse[InstallCompletionResponse])
async def get_install_completion_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get install completion by fab ID"""
    
    result = await db.execute(select(InstallCompletion).where(InstallCompletion.fab_id == fab_id))
    install_completion = result.scalar_one_or_none()
    
    if not install_completion:
        raise error_response("Install Completion not found for this fab", 404)
    
    return success_response(
        InstallCompletionResponse(
            id=install_completion.id,
            fab_id=install_completion.fab_id,
            installer_id=install_completion.installer_id,
            install_date=install_completion.install_date,
            completion_date=install_completion.completion_date,
            total_sqft_installed=install_completion.total_sqft_installed,
            customer_signature=install_completion.customer_signature,
            completion_notes=install_completion.completion_notes,
            is_completed=install_completion.is_completed,
            status_id=install_completion.status_id,
            created_at=install_completion.created_at,
            updated_at=install_completion.updated_at,
            updated_by=install_completion.updated_by
        ),
        "Install Completion retrieved successfully"
    )
