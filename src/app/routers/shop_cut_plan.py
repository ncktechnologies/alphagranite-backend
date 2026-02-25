from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, cast, String
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.shop_notes import ShopNotes
from src.app.database.user import User
from src.app.interface.business_schemas import (
    ShopCutPlanCreate,
    ShopCutPlanStageCreate,
    ShopCutPlanUpdate
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response
from src.app.database.work_station import WorkStation
from src.app.database.planning_section import PlanningSection

router = APIRouter(
    prefix="/shop",
    tags=["Shop Cut Planning"]
)


@router.post("/plans", response_model=dict)
async def create_shop_plans(
    plan_data: ShopCutPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create shop cut plans with multiple stages for a FAB"""
    
    try:
        if plan_data.status_id not in (0, 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status_id must be 0 (inactive) or 1 (active)"
            )

        # Verify FAB exists
        result = await db.execute(select(Fab).where(Fab.id == plan_data.fab_id))
        fab = result.scalar_one_or_none()
        
        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAB with ID {plan_data.fab_id} not found"
            )

        if not plan_data.stages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one stage is required"
            )

        created_plans = []

        for stage in plan_data.stages:
            ws_result = await db.execute(
                select(WorkStation).where(WorkStation.id == stage.workstation_id)
            )
            workstation = ws_result.scalar_one_or_none()
            if not workstation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workstation with ID {stage.workstation_id} not found"
                )

            if not stage.operator_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one operator is required"
                )

            user_result = await db.execute(select(User).where(User.id == stage.operator_ids[0]))
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Operator with ID {stage.operator_ids[0]} not found"
                )

            ps_result = await db.execute(
                select(PlanningSection).where(PlanningSection.id == stage.planning_section_id)
            )
            planning_section = ps_result.scalar_one_or_none()
            if not planning_section:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Planning section with ID {stage.planning_section_id} not found"
                )

            # derive cut_type / stage_name from planning section
            derived_cut_type = planning_section.plan_name.lower().strip()
            derived_stage_name = planning_section.plan_name.strip()

            scheduled_start = stage.scheduled_start.replace(tzinfo=None) if stage.scheduled_start.tzinfo else stage.scheduled_start

            for operator_id in stage.operator_ids:
                user_result = await db.execute(select(User).where(User.id == operator_id))
                user = user_result.scalar_one_or_none()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Operator with ID {operator_id} not found"
                    )

                plan = ShopCutPlan(
                    fab_id=plan_data.fab_id,
                    workstation_id=stage.workstation_id,
                    planning_section_id=stage.planning_section_id,
                    user_id=operator_id,
                    estimated_hours=stage.estimated_hours,
                    scheduled_start_date=scheduled_start,
                    work_percentage=0,
                    notes=stage.notes,
                    created_by=current_user.id,
                    created_at=datetime.now()
                )
                db.add(plan)
                created_plans.append(plan)

        shop_note = ShopNotes(
            fab_id=plan_data.fab_id,
            note=f"Shop cut plan created. status_id={plan_data.status_id}",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(shop_note)

        await db.commit()
        for plan in created_plans:
            await db.refresh(plan)

        return {
            "success": True,
            "message": f"Shop plans created successfully with {len(created_plans)} plan(s)",
            "data": {
                "fab_id": plan_data.fab_id,
                "status_id": plan_data.status_id,
                "plans_created": len(created_plans),
                "plans": [
                    {
                        "id": plan.id,
                        "workstation_id": plan.workstation_id,
                        "planning_section_id": plan.planning_section_id,
                        "operator_id": plan.user_id,
                        "estimated_hours": plan.estimated_hours,
                        "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
                        "work_percentage": plan.work_percentage,
                        "notes": plan.notes
                    }
                    for plan in created_plans
                ]
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create shop plans: {str(e)}"
        )


@router.get("/plans", response_model=dict)
async def get_all_shop_plans(
    fab_id: Optional[int] = None,
    search_fab_id: Optional[str] = None,
    fab_type: Optional[str] = None,
    workstation_id: Optional[int] = None,
    planning_section_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    status_id: Optional[int] = None,
    cut_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    target_month = month or now.month
    target_year = year or now.year
    _validate_month_year(target_month, target_year)

    query = _build_shop_plans_query()
    query = _apply_shop_plan_filters(
        query,
        fab_id=fab_id,
        search_fab_id=search_fab_id,
        fab_type=fab_type,
        workstation_id=workstation_id,
        planning_section_id=planning_section_id,
        operator_id=operator_id,
        status_id=status_id,
        cut_type=cut_type,
    )
    query = _apply_month_scope(query, target_month, target_year)

    total = await _get_total_count(db, query)
    plans = await _fetch_ordered_plans(db, query, skip, limit)
    serialized_plans, grouped_plans = await _serialize_and_group_plans(db, plans)

    return {
        "success": True,
        "message": "Shop plans retrieved successfully",
        "data": {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "month": target_month,
            "year": target_year,
            "plans": serialized_plans,
            "grouped_plans": grouped_plans
        }
    }


@router.get("/plans/fab/{fab_id}", response_model=dict)
async def get_shop_plans_by_fab_id(
    fab_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shop plans by FAB id (grouped by date, unscheduled first)."""
    now = datetime.now()
    target_month = month or now.month
    target_year = year or now.year
    _validate_month_year(target_month, target_year)

    query = select(ShopCutPlan).where(ShopCutPlan.fab_id == fab_id)
    query = _apply_month_scope(query, target_month, target_year)

    total = await _get_total_count(db, query)
    plans = await _fetch_ordered_plans(db, query, skip, limit)
    serialized_plans, grouped_plans = await _serialize_and_group_plans(db, plans)

    return {
        "success": True,
        "message": "Shop plans by FAB retrieved successfully",
        "data": {
            "fab_id": fab_id,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "month": target_month,
            "year": target_year,
            "plans": serialized_plans,
            "grouped_plans": grouped_plans
        }
    }


@router.get("/plans/{plan_id}", response_model=dict)
async def get_shop_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shop cut plan by ID"""
    
    result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop plan with ID {plan_id} not found"
        )
    
    return {
        "success": True,
        "message": "Shop plan retrieved successfully",
        "data": {
            "id": plan.id,
            "fab_id": plan.fab_id,
            "workstation_id": plan.workstation_id,
            "planning_section_id": plan.planning_section_id,
            "operator_id": plan.user_id,
            "estimated_hours": plan.estimated_hours,
            "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
            "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "work_percentage": plan.work_percentage,
            "notes": plan.notes,
            "created_at": plan.created_at.isoformat(),
            "created_by": plan.created_by,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
            "updated_by": plan.updated_by
        }
    }


@router.put("/plans/{plan_id}", response_model=dict)
async def update_shop_plan(
    plan_id: int,
    update_data: ShopCutPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a shop cut plan with stage details and metadata"""

    try:
        if update_data.status_id not in (0, 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status_id must be 0 (inactive) or 1 (active)"
            )

        result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shop plan with ID {plan_id} not found"
            )

        stage = update_data.stage

        ws_result = await db.execute(
            select(WorkStation).where(WorkStation.id == stage.workstation_id)
        )
        workstation = ws_result.scalar_one_or_none()
        if not workstation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workstation with ID {stage.workstation_id} not found"
            )

        if not stage.operator_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one operator is required"
            )

        user_result = await db.execute(select(User).where(User.id == stage.operator_ids[0]))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operator with ID {stage.operator_ids[0]} not found"
            )

        ps_result = await db.execute(
            select(PlanningSection).where(PlanningSection.id == stage.planning_section_id)
        )
        planning_section = ps_result.scalar_one_or_none()
        if not planning_section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning section with ID {stage.planning_section_id} not found"
            )

        scheduled_start = (
            stage.scheduled_start.replace(tzinfo=None)
            if stage.scheduled_start and stage.scheduled_start.tzinfo
            else stage.scheduled_start
        )

        plan.workstation_id = stage.workstation_id
        plan.planning_section_id = stage.planning_section_id
        plan.user_id = stage.operator_ids[0]
        plan.estimated_hours = stage.estimated_hours
        plan.scheduled_start_date = scheduled_start
        plan.notes = update_data.notes
        plan.updated_at = datetime.now()
        plan.updated_by = current_user.id

        shop_note = ShopNotes(
            fab_id=plan.fab_id,
            note=f"Shop cut plan updated. status_id={update_data.status_id}",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(shop_note)

        await db.commit()
        await db.refresh(plan)

        return {
            "success": True,
            "message": "Shop plan updated successfully",
            "data": {
                "id": plan.id,
                "fab_id": plan.fab_id,
                "workstation_id": plan.workstation_id,
                "planning_section_id": plan.planning_section_id,
                "operator_id": plan.user_id,
                "estimated_hours": plan.estimated_hours,
                "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
                "work_percentage": plan.work_percentage,
                "notes": plan.notes,
                "updated_at": plan.updated_at.isoformat(),
                "updated_by": plan.updated_by,
                "status_id": update_data.status_id
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update shop plan: {str(e)}"
        )


@router.delete("/plans/{plan_id}", response_model=dict)
async def delete_shop_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a shop cut plan"""
    
    try:
        result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shop plan with ID {plan_id} not found"
            )
        
        fab_id = plan.fab_id
        await db.delete(plan)
        await db.commit()
        
        return {
            "success": True,
            "message": "Shop plan deleted successfully",
            "data": {
                "deleted_plan_id": plan_id,
                "fab_id": fab_id
            }
        }
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete shop plan: {str(e)}"
        )


class RescheduleShopPlanRequest(BaseModel):
    scheduled_start: datetime


@router.put("/plans/{plan_id}/unschedule", response_model=dict)
async def unschedule_shop_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unschedule date from a shop plan"""
    try:
        result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shop plan with ID {plan_id} not found"
            )

        plan.scheduled_start_date = None
        plan.updated_at = datetime.now()
        plan.updated_by = current_user.id

        await db.commit()
        await db.refresh(plan)

        return {
            "success": True,
            "message": "Shop plan unscheduled successfully",
            "data": {
                "id": plan.id,
                "scheduled_start_date": None,
                "updated_at": plan.updated_at.isoformat(),
                "updated_by": plan.updated_by
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unschedule shop plan: {str(e)}"
        )


@router.put("/plans/{plan_id}/reschedule", response_model=dict)
async def reschedule_shop_plan(
    plan_id: int,
    payload: RescheduleShopPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reschedule date for a shop plan"""
    try:
        result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shop plan with ID {plan_id} not found"
            )

        scheduled_start = payload.scheduled_start.replace(tzinfo=None) if payload.scheduled_start.tzinfo else payload.scheduled_start
        plan.scheduled_start_date = scheduled_start
        plan.updated_at = datetime.now()
        plan.updated_by = current_user.id

        await db.commit()
        await db.refresh(plan)

        return {
            "success": True,
            "message": "Shop plan rescheduled successfully",
            "data": {
                "id": plan.id,
                "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
                "updated_at": plan.updated_at.isoformat(),
                "updated_by": plan.updated_by
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule shop plan: {str(e)}"
        )


async def _serialize_and_group_plans(db: AsyncSession, plans: list[ShopCutPlan]):
    serialized_plans = []
    grouped = {}

    for plan in plans:
        # Fetch related data
        ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
        workstation = ws_result.scalar_one_or_none()
        workstation_name = workstation.name if workstation else None

        user_result = await db.execute(select(User).where(User.id == plan.user_id))
        user = user_result.scalar_one_or_none()

        operator_name = None
        if user:
            operator_name = f"{user.first_name} {user.last_name}".strip() or user.username

        ps_result = await db.execute(select(PlanningSection).where(PlanningSection.id == plan.planning_section_id))
        planning_section = ps_result.scalar_one_or_none()
        plan_name = planning_section.plan_name if planning_section else None

        fab_result = await db.execute(select(Fab).where(Fab.id == plan.fab_id))
        fab = fab_result.scalar_one_or_none()
        fab_type = fab.fab_type if fab else None

        item = {
            "id": plan.id,
            "fab_id": plan.fab_id,
            "fab_type": fab_type,
            "workstation_id": plan.workstation_id,
            "workstation_name": workstation_name,
            "planning_section_id": plan.planning_section_id,
            "plan_name": plan_name,
            "operator_id": plan.user_id,
            "operator_name": operator_name,
            "estimated_hours": plan.estimated_hours,
            "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
            "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "work_percentage": plan.work_percentage,
            "notes": plan.notes,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
        }
        serialized_plans.append(item)

        group_key = plan.scheduled_start_date.date().isoformat() if plan.scheduled_start_date else "unscheduled"
        if group_key not in grouped:
            grouped[group_key] = {
                "date": None if group_key == "unscheduled" else group_key,
                "label": "Unscheduled" if group_key == "unscheduled" else group_key,
                "plans": []
            }
        grouped[group_key]["plans"].append(item)

    grouped_plans = []
    if "unscheduled" in grouped:
        grouped_plans.append(grouped.pop("unscheduled"))
    for key in sorted(grouped.keys()):
        grouped_plans.append(grouped[key])

    return serialized_plans, grouped_plans


def _normalize_naive_dt(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value and value.tzinfo else value


def _validate_month_year(month: int, year: int) -> None:
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    if year < 1900 or year > 9999:
        raise HTTPException(status_code=400, detail="year must be between 1900 and 9999")


def _build_shop_plans_query():
    return (
        select(ShopCutPlan)
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id)
    )


def _apply_shop_plan_filters(
    query,
    *,
    fab_id: Optional[int],
    search_fab_id: Optional[str],
    fab_type: Optional[str],
    workstation_id: Optional[int],
    planning_section_id: Optional[int],
    operator_id: Optional[int],
    status_id: Optional[int],
    cut_type: Optional[str],
):
    if fab_id is not None:
        query = query.where(ShopCutPlan.fab_id == fab_id)

    if search_fab_id:
        query = query.where(cast(ShopCutPlan.fab_id, String).ilike(f"%{search_fab_id.strip()}%"))

    if workstation_id is not None:
        query = query.where(ShopCutPlan.workstation_id == workstation_id)

    if planning_section_id is not None:
        query = query.where(ShopCutPlan.planning_section_id == planning_section_id)

    if operator_id is not None:
        query = query.where(ShopCutPlan.user_id == operator_id)

    if status_id is not None:
        if not hasattr(ShopCutPlan, "status_id"):
            raise HTTPException(status_code=400, detail="status_id filter is not supported by ShopCutPlan model")
        query = query.where(getattr(ShopCutPlan, "status_id") == status_id)

    if cut_type:
        query = query.where(func.lower(PlanningSection.plan_name) == cut_type.strip().lower())

    if fab_type:
        if hasattr(Fab, "fab_type"):
            query = query.where(func.lower(getattr(Fab, "fab_type")) == fab_type.strip().lower())
        elif hasattr(Fab, "type"):
            query = query.where(func.lower(getattr(Fab, "type")) == fab_type.strip().lower())
        else:
            raise HTTPException(status_code=400, detail="fab_type filter is not supported by Fab model")

    return query


def _apply_month_scope(query, month: int, year: int):
    return query.where(
        or_(
            ShopCutPlan.scheduled_start_date.is_(None),
            and_(
                func.extract("month", ShopCutPlan.scheduled_start_date) == month,
                func.extract("year", ShopCutPlan.scheduled_start_date) == year,
            ),
        )
    )


async def _get_total_count(db: AsyncSession, query) -> int:
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    return count_result.scalar() or 0


async def _fetch_ordered_plans(db: AsyncSession, query, skip: int, limit: int):
    result = await db.execute(
        query.order_by(
            ShopCutPlan.scheduled_start_date.is_(None).desc(),
            ShopCutPlan.scheduled_start_date.asc()
        ).offset(skip).limit(limit)
    )
    return result.scalars().all()