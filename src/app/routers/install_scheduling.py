from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.interface.generated_schemas import InstallCompletion
from src.app.interface.generated_schemas import InstallScheduling
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    InstallCompletionResponse,
    InstallSchedulingCreate,
    InstallSchedulingUpdate,
    InstallSchedulingResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


async def _resolve_install_crew_names(
    db: AsyncSession,
    installer_id: Optional[int],
    extra_crew_1_id: Optional[int],
    extra_crew_2_id: Optional[int],
    extra_crew_3_id: Optional[int],
):
    crew_ids = [crew_id for crew_id in [installer_id, extra_crew_1_id, extra_crew_2_id, extra_crew_3_id] if crew_id]
    if not crew_ids:
        return None, None, None, None

    users_result = await db.execute(select(User).where(User.id.in_(crew_ids)))
    users = users_result.scalars().all()
    user_names = {
        u.id: f"{u.first_name or ''} {u.last_name or ''}".strip() or None
        for u in users
    }

    return (
        user_names.get(installer_id),
        user_names.get(extra_crew_1_id),
        user_names.get(extra_crew_2_id),
        user_names.get(extra_crew_3_id),
    )


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
        installer_id=install_data.installer_id,
        extra_crew_1_id=install_data.extra_crew_1_id,
        extra_crew_2_id=install_data.extra_crew_2_id,
        extra_crew_3_id=install_data.extra_crew_3_id,
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
    
    installer_name, extra_crew_1_name, extra_crew_2_name, extra_crew_3_name = await _resolve_install_crew_names(
        db,
        install_scheduling.installer_id,
        install_scheduling.extra_crew_1_id,
        install_scheduling.extra_crew_2_id,
        install_scheduling.extra_crew_3_id,
    )
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            installer_name=installer_name,
            extra_crew_1_id=install_scheduling.extra_crew_1_id,
            extra_crew_1_name=extra_crew_1_name,
            extra_crew_2_id=install_scheduling.extra_crew_2_id,
            extra_crew_2_name=extra_crew_2_name,
            extra_crew_3_id=install_scheduling.extra_crew_3_id,
            extra_crew_3_name=extra_crew_3_name,
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

    update_dict = update_data.model_dump(exclude_unset=True)
    if update_dict.get("is_completed") is True:
        progress_result = await db.execute(
            select(
                func.count(ShopCutPlan.id).label("plan_count"),
                func.avg(func.coalesce(ShopCutPlan.work_percentage, 0)).label("percentage_completion"),
            ).where(ShopCutPlan.fab_id == install_scheduling.fab_id)
        )
        plan_count, percentage_completion = progress_result.one()
        percentage_completion = float(percentage_completion or 0.0)

        if (plan_count or 0) == 0:
            raise error_response(
                "Install scheduling cannot be marked complete until shop percentage_completion reaches 100%",
                400,
            )

        if percentage_completion < 100.0:
            raise error_response(
                f"Install scheduling cannot be marked complete until shop percentage_completion reaches 100% (current: {round(percentage_completion, 2)}%)",
                400,
            )
    
    # Update fields
    for key, value in update_dict.items():
        setattr(install_scheduling, key, value)
    
    install_scheduling.updated_at = datetime.now()
    install_scheduling.updated_by = current_user.id
    
    # Update FAB's current_stage to install_completion when install scheduling is updated
    fab_result = await db.execute(select(Fab).where(Fab.id == install_scheduling.fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if fab:
        fab.current_stage = "install_completion"
        fab.next_stage = None  # install_completion is typically the final stage
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(install_scheduling)
    
    installer_name, extra_crew_1_name, extra_crew_2_name, extra_crew_3_name = await _resolve_install_crew_names(
        db,
        install_scheduling.installer_id,
        install_scheduling.extra_crew_1_id,
        install_scheduling.extra_crew_2_id,
        install_scheduling.extra_crew_3_id,
    )
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            installer_name=installer_name,
            extra_crew_1_id=install_scheduling.extra_crew_1_id,
            extra_crew_1_name=extra_crew_1_name,
            extra_crew_2_id=install_scheduling.extra_crew_2_id,
            extra_crew_2_name=extra_crew_2_name,
            extra_crew_3_id=install_scheduling.extra_crew_3_id,
            extra_crew_3_name=extra_crew_3_name,
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
    
    installer_name, extra_crew_1_name, extra_crew_2_name, extra_crew_3_name = await _resolve_install_crew_names(
        db,
        install_scheduling.installer_id,
        install_scheduling.extra_crew_1_id,
        install_scheduling.extra_crew_2_id,
        install_scheduling.extra_crew_3_id,
    )
    
    return success_response(
        InstallSchedulingResponse(
            id=install_scheduling.id,
            fab_id=install_scheduling.fab_id,
            installer_id=install_scheduling.installer_id,
            installer_name=installer_name,
            extra_crew_1_id=install_scheduling.extra_crew_1_id,
            extra_crew_1_name=extra_crew_1_name,
            extra_crew_2_id=install_scheduling.extra_crew_2_id,
            extra_crew_2_name=extra_crew_2_name,
            extra_crew_3_id=install_scheduling.extra_crew_3_id,
            extra_crew_3_name=extra_crew_3_name,
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


@router.patch("/install-scheduling/fab/{fab_id}/unmark", response_model=SuccessResponse[InstallSchedulingResponse])
async def unmark_install_scheduling(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unmark (uncheck) install scheduling for a fab by reverting is_completed to False."""

    result = await db.execute(select(InstallScheduling).where(InstallScheduling.fab_id == fab_id))
    install_scheduling = result.scalar_one_or_none()

    if not install_scheduling:
        raise error_response("Install Scheduling not found for this fab", 404)

    if not install_scheduling.is_completed:
        raise error_response("Install Scheduling is not marked as completed", 400)

    install_scheduling.is_completed = False
    install_scheduling.updated_at = datetime.now()
    install_scheduling.updated_by = current_user.id

    # Revert the FAB stage back to install_scheduling
    fab = (await db.execute(select(Fab).where(Fab.id == fab_id))).scalar_one_or_none()
    if fab:
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id

    await db.commit()
    await db.refresh(install_scheduling)

    installer_name, extra_crew_1_name, extra_crew_2_name, extra_crew_3_name = await _resolve_install_crew_names(
        db,
        install_scheduling.installer_id,
        install_scheduling.extra_crew_1_id,
        install_scheduling.extra_crew_2_id,
        install_scheduling.extra_crew_3_id,
    )

    response_data = install_scheduling.model_dump()
    response_data["installer_name"] = installer_name
    response_data["extra_crew_1_name"] = extra_crew_1_name
    response_data["extra_crew_2_name"] = extra_crew_2_name
    response_data["extra_crew_3_name"] = extra_crew_3_name

    return success_response(response_data, "Install Scheduling unmarked successfully")


@router.patch("/install-completion/fab/{fab_id}/unmark", response_model=SuccessResponse[InstallCompletionResponse])
async def unmark_install_completion(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unmark (uncheck) install completion for a fab by reverting is_completed to False."""

    result = await db.execute(select(InstallCompletion).where(InstallCompletion.fab_id == fab_id))
    install_completion = result.scalar_one_or_none()

    if not install_completion:
        raise error_response("Install Completion not found for this fab", 404)

    if not install_completion.is_completed:
        raise error_response("Install Completion is not marked as completed", 400)

    install_completion.is_completed = False
    install_completion.updated_at = datetime.now()
    install_completion.updated_by = current_user.id

    # Revert the FAB stage back to install_completion
    fab = (await db.execute(select(Fab).where(Fab.id == fab_id))).scalar_one_or_none()
    if fab:
        fab.current_stage = "install_completion"
        fab.next_stage = None  # It's the last stage
        fab.updated_at = datetime.now()
        fab.updated_by = current_user.id

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
            install_confirm=install_completion.is_confirmed,
            status_id=install_completion.status_id,
            created_at=install_completion.created_at,
            updated_at=install_completion.updated_at,
            updated_by=install_completion.updated_by
        ),
        "Install Completion unmarked successfully"
    )
