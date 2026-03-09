from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, cast, String
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel
from collections import Counter

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.shop_notes import ShopNotes
from src.app.database.user import User
from src.app.interface.business_schemas import (
    ShopCutPlanCreate,
    ShopCutPlanStageCreate,
    ShopCutPlanUpdate,
    ShopPlanSuggestionsRequest,
    EarliestAvailabilityRequest,
    EarliestAvailabilityItem
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response
from src.app.database.work_station import WorkStation
from src.app.database.planning_section import PlanningSection
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account

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

        # Prevent duplicate planning_section_id in the same payload
        section_ids = [stage.planning_section_id for stage in plan_data.stages]
        section_counts = Counter(section_ids)
        duplicate_sections_in_payload = sorted([sid for sid, cnt in section_counts.items() if cnt > 1])
        if duplicate_sections_in_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This Planning Section has already been added. Please select a different Planning Section."
            )

        # Prevent duplicate planning against existing records
        existing_result = await db.execute(
            select(ShopCutPlan.planning_section_id)
            .where(
                ShopCutPlan.fab_id == plan_data.fab_id,
                ShopCutPlan.planning_section_id.in_(section_ids)
            )
            .distinct()
        )
        existing_sections = sorted([row[0] for row in existing_result.all()])
        if existing_sections:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Duplicate planning not allowed: FAB {plan_data.fab_id} already has plan(s) "
                    f"for planning_section_id(s): {existing_sections}"
                )
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

            # Enforce one plan per (fab_id, planning_section_id)
            if len(stage.operator_ids) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Only one operator is allowed per stage. "
                        "A FAB cannot have more than one plan for the same planning_section_id."
                    )
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

    fab_cache: Dict[int, Optional[Fab]] = {}
    job_cache: Dict[int, Optional[BusinessJob]] = {}
    account_cache: Dict[int, Optional[Account]] = {}

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

        if plan.fab_id not in fab_cache:
            fab_result = await db.execute(select(Fab).where(Fab.id == plan.fab_id))
            fab_cache[plan.fab_id] = fab_result.scalar_one_or_none()

        fab = fab_cache.get(plan.fab_id)
        fab_type = fab.fab_type if fab else None

        account_name = None
        business_job_payload = None
        job_name = None
        job_number = None

        if fab and getattr(fab, "job_id", None):
            job_id = fab.job_id

            if job_id not in job_cache:
                job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
                job_cache[job_id] = job_result.scalar_one_or_none()

            job = job_cache.get(job_id)
            if job:
                job_name = job.name
                job_number = job.job_number

                if job.account_id:
                    if job.account_id not in account_cache:
                        account_result = await db.execute(select(Account).where(Account.id == job.account_id))
                        account_cache[job.account_id] = account_result.scalar_one_or_none()

                    account = account_cache.get(job.account_id)
                    account_name = account.name if account else None

                business_job_payload = _serialize_business_job(job, account_name=account_name)

        item = {
            "id": plan.id,
            "fab_id": plan.fab_id,
            "fab_type": fab_type,
            "account_name": account_name,
            "job_name": job_name,
            "job_number": job_number,
            "business_job": business_job_payload,  # full BusinessJob data
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



#Auto Scheduler Endpoint - Dry Run for Available Slots
@router.post("/plans/suggestions", response_model=dict)
async def suggest_shop_plan_slots(
    request: ShopPlanSuggestionsRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan_data = request.plan_data
        window_start = _normalize_naive_dt(request.window_start)
        window_end = _normalize_naive_dt(request.window_end)
        slot_minutes = request.slot_minutes
        max_suggestions_per_stage = request.max_suggestions_per_stage

        # Basic window validation
        window_start = _normalize_naive_dt(window_start)
        window_end = _normalize_naive_dt(window_end)

        if window_start >= window_end:
            raise HTTPException(status_code=400, detail="window_start must be before window_end")
        if slot_minutes <= 0:
            raise HTTPException(status_code=400, detail="slot_minutes must be > 0")
        if max_suggestions_per_stage <= 0:
            raise HTTPException(status_code=400, detail="max_suggestions_per_stage must be > 0")

        # Reuse create validations
        if plan_data.status_id not in (0, 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status_id must be 0 (inactive) or 1 (active)"
            )

        fab_result = await db.execute(select(Fab).where(Fab.id == plan_data.fab_id))
        fab = fab_result.scalar_one_or_none()
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

        section_ids = [stage.planning_section_id for stage in plan_data.stages]
        section_counts = Counter(section_ids)
        duplicate_sections_in_payload = sorted([sid for sid, cnt in section_counts.items() if cnt > 1])
        if duplicate_sections_in_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This Planning Section has already been added. Please select a different Planning Section."
            )

        existing_result = await db.execute(
            select(ShopCutPlan.planning_section_id)
            .where(
                ShopCutPlan.fab_id == plan_data.fab_id,
                ShopCutPlan.planning_section_id.in_(section_ids)
            )
            .distinct()
        )
        existing_sections = sorted([row[0] for row in existing_result.all()])
        if existing_sections:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Duplicate planning not allowed: FAB {plan_data.fab_id} already has plan(s) "
                    f"for planning_section_id(s): {existing_sections}"
                )
            )

        # Stage-level validations and prep
        stage_meta = []
        workstation_ids = set()
        operator_ids = set()
        max_duration_hours = 0.0

        for stage in plan_data.stages:
            ws_result = await db.execute(select(WorkStation).where(WorkStation.id == stage.workstation_id))
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

            if len(stage.operator_ids) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Only one operator is allowed per stage. "
                        "A FAB cannot have more than one plan for the same planning_section_id."
                    )
                )

            operator_id = stage.operator_ids[0]
            user_result = await db.execute(select(User).where(User.id == operator_id))
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Operator with ID {operator_id} not found"
                )

            ps_result = await db.execute(select(PlanningSection).where(PlanningSection.id == stage.planning_section_id))
            planning_section = ps_result.scalar_one_or_none()
            if not planning_section:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Planning section with ID {stage.planning_section_id} not found"
                )

            est_hours = float(stage.estimated_hours or 0)
            if est_hours <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"estimated_hours must be > 0 for planning_section_id={stage.planning_section_id}"
                )

            max_duration_hours = max(max_duration_hours, est_hours)
            workstation_ids.add(stage.workstation_id)
            operator_ids.add(operator_id)

            stage_meta.append({
                "planning_section_id": stage.planning_section_id,
                "plan_name": planning_section.plan_name,
                "workstation_id": stage.workstation_id,
                "workstation_name": workstation.name,
                "operator_id": operator_id,
                "operator_name": (f"{user.first_name} {user.last_name}".strip() or user.username),
                "estimated_hours": est_hours,
            })

        # Pull potentially conflicting plans in one query
        # Include plans starting before window_start (up to max duration) that can overlap into window.
        fetch_from = window_start - timedelta(hours=max_duration_hours)

        conflict_query = (
            select(ShopCutPlan)
            .where(
                ShopCutPlan.scheduled_start_date.is_not(None),
                ShopCutPlan.scheduled_start_date < window_end,
                ShopCutPlan.scheduled_start_date >= fetch_from,
                or_(
                    ShopCutPlan.workstation_id.in_(list(workstation_ids)),
                    ShopCutPlan.user_id.in_(list(operator_ids)),
                    ShopCutPlan.fab_id == plan_data.fab_id
                )
            )
        )
        conflict_rows = (await db.execute(conflict_query)).scalars().all()

        busy_by_ws: Dict[int, List[Tuple[datetime, datetime]]] = {}
        busy_by_user: Dict[int, List[Tuple[datetime, datetime]]] = {}
        busy_by_fab: List[Tuple[datetime, datetime]] = []

        for p in conflict_rows:
            p_start = _normalize_naive_dt(p.scheduled_start_date)
            duration_hours = float(p.estimated_hours or 0)
            if not p_start or duration_hours <= 0:
                continue
            p_end = p_start + timedelta(hours=duration_hours)

            busy_by_ws.setdefault(p.workstation_id, []).append((p_start, p_end))
            busy_by_user.setdefault(p.user_id, []).append((p_start, p_end))
            if p.fab_id == plan_data.fab_id:
                busy_by_fab.append((p_start, p_end))

        # Build suggestions per stage
        suggestions = []
        for meta in stage_meta:
            candidates = _build_candidate_ranges(
                window_start=window_start,
                window_end=window_end,
                duration_hours=meta["estimated_hours"],
                slot_minutes=slot_minutes
            )

            available = []
            ws_busy = busy_by_ws.get(meta["workstation_id"], [])
            user_busy = busy_by_user.get(meta["operator_id"], [])

            for c_start, c_end in candidates:
                ws_conflict = any(_intervals_overlap(c_start, c_end, b_start, b_end) for b_start, b_end in ws_busy)
                if ws_conflict:
                    continue

                user_conflict = any(_intervals_overlap(c_start, c_end, b_start, b_end) for b_start, b_end in user_busy)
                if user_conflict:
                    continue

                fab_conflict = any(_intervals_overlap(c_start, c_end, b_start, b_end) for b_start, b_end in busy_by_fab)
                if fab_conflict:
                    continue

                available.append({
                    "start": c_start.isoformat(),
                    "end": c_end.isoformat()
                })

                if len(available) >= max_suggestions_per_stage:
                    break

            suggestions.append({
                "planning_section_id": meta["planning_section_id"],
                "plan_name": meta["plan_name"],
                "workstation_id": meta["workstation_id"],
                "workstation_name": meta["workstation_name"],
                "operator_id": meta["operator_id"],
                "operator_name": meta["operator_name"],
                "estimated_hours": meta["estimated_hours"],
                "available_ranges": available
            })

        return {
            "success": True,
            "message": "Suggestions generated",
            "data": {
                "fab_id": plan_data.fab_id,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "slot_minutes": slot_minutes,
                "max_suggestions_per_stage": max_suggestions_per_stage,
                "suggestions": suggestions
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan suggestions: {str(e)}"
        )





def _intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and end_a > start_b


def _build_candidate_ranges(
    window_start: datetime,
    window_end: datetime,
    duration_hours: float,
    slot_minutes: int
) -> List[Tuple[datetime, datetime]]:
    duration = timedelta(hours=float(duration_hours))
    if duration.total_seconds() <= 0:
        return []

    out: List[Tuple[datetime, datetime]] = []
    cursor = window_start
    step = timedelta(minutes=slot_minutes)

    while cursor + duration <= window_end:
        out.append((cursor, cursor + duration))
        cursor += step

    return out


def _serialize_business_job(job: Optional[BusinessJob], account_name: Optional[str] = None) -> Optional[dict]:
    if not job:
        return None

    return {
        "id": job.id,
        "name": job.name,
        "job_number": job.job_number,
        "account_id": job.account_id,
        "account_name": account_name,
        "description": job.description,
        "priority": job.priority,
        "start_date": job.start_date.isoformat() if job.start_date else None,
        "due_date": job.due_date.isoformat() if job.due_date else None,
        "project_value": str(job.project_value) if job.project_value is not None else None,
        "status_id": job.status_id,
        "created_by": job.created_by,
        "sq_ft": job.sq_ft,
        "sales_person_id": job.sales_person_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "updated_by": job.updated_by,
        "need_to_invoice": job.need_to_invoice,
        "invoice_note": job.invoice_note,
        "invoiced_at": job.invoiced_at.isoformat() if job.invoiced_at else None,
    }


async def _serialize_and_group_plans(db: AsyncSession, plans: list[ShopCutPlan]):
    serialized_plans = []
    grouped = {}

    fab_cache: Dict[int, Optional[Fab]] = {}
    job_cache: Dict[int, Optional[BusinessJob]] = {}
    account_cache: Dict[int, Optional[Account]] = {}

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

        if plan.fab_id not in fab_cache:
            fab_result = await db.execute(select(Fab).where(Fab.id == plan.fab_id))
            fab_cache[plan.fab_id] = fab_result.scalar_one_or_none()

        fab = fab_cache.get(plan.fab_id)
        fab_type = fab.fab_type if fab else None

        account_name = None
        business_job_payload = None
        job_name = None
        job_number = None

        if fab and getattr(fab, "job_id", None):
            job_id = fab.job_id

            if job_id not in job_cache:
                job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
                job_cache[job_id] = job_result.scalar_one_or_none()

            job = job_cache.get(job_id)
            if job:
                job_name = job.name
                job_number = job.job_number

                if job.account_id:
                    if job.account_id not in account_cache:
                        account_result = await db.execute(select(Account).where(Account.id == job.account_id))
                        account_cache[job.account_id] = account_result.scalar_one_or_none()

                    account = account_cache.get(job.account_id)
                    account_name = account.name if account else None

                business_job_payload = _serialize_business_job(job, account_name=account_name)

        item = {
            "id": plan.id,
            "fab_id": plan.fab_id,
            "fab_type": fab_type,
            "account_name": account_name,
            "job_name": job_name,
            "job_number": job_number,
            "business_job": business_job_payload,  # full BusinessJob data
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


#Auto Scheduler Endpoint - Dry Run for Available Slots
@router.post("/plans/earliest-availability", response_model=dict)
async def get_earliest_availability(
    payload: EarliestAvailabilityRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if not payload.requests:
            raise HTTPException(status_code=400, detail="requests must not be empty")
        if payload.slot_minutes <= 0:
            raise HTTPException(status_code=400, detail="slot_minutes must be > 0")
        if payload.search_horizon_days <= 0:
            raise HTTPException(status_code=400, detail="search_horizon_days must be > 0")
        if payload.max_proposals_per_request <= 0:
            raise HTTPException(status_code=400, detail="max_proposals_per_request must be > 0")

        start_from = _normalize_naive_dt(payload.start_from) if payload.start_from else datetime.now().replace(second=0, microsecond=0)
        start_from = _align_to_slot(start_from, payload.slot_minutes)
        search_end = start_from + timedelta(days=payload.search_horizon_days)
        step = timedelta(minutes=payload.slot_minutes)

        operator_ids = {r.operator_id for r in payload.requests}
        workstation_ids = {r.workstation_id for r in payload.requests}

        # Validate operators/workstations exist
        user_rows = (await db.execute(select(User.id).where(User.id.in_(list(operator_ids))))).all()
        ws_rows = (await db.execute(select(WorkStation.id).where(WorkStation.id.in_(list(workstation_ids))))).all()
        valid_users = {r[0] for r in user_rows}
        valid_ws = {r[0] for r in ws_rows}

        missing_users = sorted(operator_ids - valid_users)
        missing_ws = sorted(workstation_ids - valid_ws)
        if missing_users:
            raise HTTPException(status_code=404, detail=f"Operator(s) not found: {missing_users}")
        if missing_ws:
            raise HTTPException(status_code=404, detail=f"Workstation(s) not found: {missing_ws}")

        # Validate planning sections and build id->name map
        section_ids = {r.planning_section_id for r in payload.requests}
        ps_rows = (await db.execute(
            select(PlanningSection.id, PlanningSection.plan_name)
            .where(PlanningSection.id.in_(list(section_ids)))
        )).all()
        ps_map = {row[0]: row[1] for row in ps_rows}

        missing_sections = sorted(section_ids - set(ps_map.keys()))
        if missing_sections:
            raise HTTPException(status_code=404, detail=f"Planning section(s) not found: {missing_sections}")

        # Pull relevant scheduled plans once
        conflict_query = (
            select(ShopCutPlan)
            .where(
                ShopCutPlan.scheduled_start_date.is_not(None),
                ShopCutPlan.scheduled_start_date < search_end,
                or_(
                    ShopCutPlan.workstation_id.in_(list(workstation_ids)),
                    ShopCutPlan.user_id.in_(list(operator_ids)),
                ),
            )
        )
        conflict_rows = (await db.execute(conflict_query)).scalars().all()

        busy_by_ws: Dict[int, List[Tuple[datetime, datetime]]] = {}
        busy_by_user: Dict[int, List[Tuple[datetime, datetime]]] = {}

        for p in conflict_rows:
            p_start = _normalize_naive_dt(p.scheduled_start_date)
            dur_hours = float(p.estimated_hours or 0)
            if not p_start or dur_hours <= 0:
                continue
            p_end = p_start + timedelta(hours=dur_hours)
            busy_by_ws.setdefault(p.workstation_id, []).append((p_start, p_end))
            busy_by_user.setdefault(p.user_id, []).append((p_start, p_end))

        # Merge intervals per resource
        for ws_id, intervals in busy_by_ws.items():
            busy_by_ws[ws_id] = _merge_intervals(intervals)
        for user_id, intervals in busy_by_user.items():
            busy_by_user[user_id] = _merge_intervals(intervals)

        results = []
        for req in payload.requests:
            if float(req.estimated_hours or 0) <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"estimated_hours must be > 0 for operator_id={req.operator_id}, workstation_id={req.workstation_id}"
                )

            duration = timedelta(hours=float(req.estimated_hours))
            combined_busy = _merge_intervals(
                (busy_by_ws.get(req.workstation_id, []) + busy_by_user.get(req.operator_id, []))
            )

            proposals = []
            cursor = start_from

            while cursor + duration <= search_end and len(proposals) < payload.max_proposals_per_request:
                candidate_end = cursor + duration
                overlap = _first_overlap(cursor, candidate_end, combined_busy)

                if overlap is None:
                    proposals.append({
                        "start": cursor.isoformat(),
                        "end": candidate_end.isoformat()
                    })
                    cursor = cursor + step
                else:
                    cursor = _align_to_slot(max(cursor + step, overlap[1]), payload.slot_minutes)

            results.append({
                "planning_section_id": req.planning_section_id,
                "plan_name": ps_map.get(req.planning_section_id),
                "operator_id": req.operator_id,
                "workstation_id": req.workstation_id,
                "estimated_hours": float(req.estimated_hours),
                "proposed_ranges": proposals
            })

        return {
            "success": True,
            "message": "Earliest availability calculated",
            "data": {
                "start_from": start_from.isoformat(),
                "search_end": search_end.isoformat(),
                "slot_minutes": payload.slot_minutes,
                "results": results
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate earliest availability: {str(e)}"
        )



def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = [ordered[0]]

    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _first_overlap(
    start: datetime,
    end: datetime,
    intervals: List[Tuple[datetime, datetime]]
) -> Optional[Tuple[datetime, datetime]]:
    for b_start, b_end in intervals:
        if _intervals_overlap(start, end, b_start, b_end):
            return (b_start, b_end)
    return None


def _align_to_slot(value: datetime, slot_minutes: int) -> datetime:
    value = value.replace(second=0, microsecond=0)
    remainder = value.minute % slot_minutes
    if remainder == 0:
        return value
    return value + timedelta(minutes=(slot_minutes - remainder))