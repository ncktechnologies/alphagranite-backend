from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, cast, String
from datetime import datetime, timezone, timedelta, date
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
    ShopCutPlanTimerActionRequest,
    EarliestAvailabilityRequest,
    EarliestAvailabilityItem
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response
from src.app.database.work_station import WorkStation
from src.app.database.planning_section import PlanningSection
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.database.shop_cut_plan_timer_session import ShopCutPlanTimerSession
from src.app.database.shop_cut_plan_timer_event import ShopCutPlanTimerEvent
from src.app.database.role import Role
from src.app.database.user_role import UserRole

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

        # Validate that incoming sequence numbers don't duplicate existing ones for this FAB
        incoming_sequences = [stage.sequence for stage in plan_data.stages]
        existing_seq_result = await db.execute(
            select(ShopCutPlan.sequence).where(ShopCutPlan.fab_id == plan_data.fab_id)
        )
        existing_sequences = {row[0] for row in existing_seq_result.fetchall()}
        duplicate_sequences = [seq for seq in incoming_sequences if seq in existing_sequences]
        if duplicate_sequences:
            seq_list = ", ".join(str(s) for s in sorted(duplicate_sequences))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sequence {seq_list} already exists for this FAB. Please assign a unique sequence."
            )

        # Validate that stages are ordered by sequence chronologically
        if len(plan_data.stages) > 1:
            stages_by_seq = sorted(plan_data.stages, key=lambda s: s.sequence)
            for i in range(len(stages_by_seq) - 1):
                curr = stages_by_seq[i]
                nxt = stages_by_seq[i + 1]
                curr_start = curr.scheduled_start.replace(tzinfo=None) if curr.scheduled_start.tzinfo else curr.scheduled_start
                nxt_start = nxt.scheduled_start.replace(tzinfo=None) if nxt.scheduled_start.tzinfo else nxt.scheduled_start
                if curr_start > nxt_start:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Sequence {curr.sequence} must be scheduled before Sequence {nxt.sequence}",
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
            _validate_manual_schedule_interval(scheduled_start, stage.estimated_hours)

            await _assert_no_shop_plan_conflicts(
                db,
                plan_id=0,
                fab_id=plan_data.fab_id,
                workstation_id=stage.workstation_id,
                operator_id=stage.operator_ids[0],
                scheduled_start=scheduled_start,
                estimated_hours=stage.estimated_hours,
            )

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
                    sequence=stage.sequence,
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

        plans_payload = []
        for plan in created_plans:
            ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
            plan_workstation = ws_result.scalar_one_or_none()

            user_result = await db.execute(select(User).where(User.id == plan.user_id))
            plan_operator = user_result.scalar_one_or_none()

            scheduled_end = _compute_lunch_adjusted_end(plan.scheduled_start_date, plan.estimated_hours) if plan.scheduled_start_date else None

            plans_payload.append({
                "id": plan.id,
                "sequence": plan.sequence,
                "workstation_id": plan.workstation_id,
                "workstation_name": plan_workstation.name if plan_workstation else None,
                "planning_section_id": plan.planning_section_id,
                "operator_id": plan.user_id,
                "operator_name": (f"{plan_operator.first_name} {plan_operator.last_name}".strip() or plan_operator.username) if plan_operator else None,
                "estimated_hours": plan.estimated_hours,
                "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
                "scheduled_end_date": _compute_schedule_end_time_iso(plan.scheduled_start_date, plan.estimated_hours),
                "scheduled_time": _format_scheduled_time_range(plan.scheduled_start_date, scheduled_end),
                "work_percentage": plan.work_percentage,
                "notes": plan.notes,
            })

        return {
            "success": True,
            "message": f"Shop plans created successfully with {len(created_plans)} plan(s)",
            "data": {
                "fab_id": plan_data.fab_id,
                "status_id": plan_data.status_id,
                "plans_created": len(created_plans),
                "plans": plans_payload
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
    search: Optional[str] = Query(None, description="Search value"),
    type: Optional[str] = Query(None, description="Field to apply search to: fab_id, job_number, job_name"),
    view: str = "week",
    reference_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    normalized_view = (view or "week").strip().lower()
    if reference_date is not None:
        target_date = reference_date
    elif month is not None or year is not None:
        now = datetime.now()
        target_month = month or now.month
        target_year = year or now.year
        _validate_month_year(target_month, target_year)
        target_date = date(target_year, target_month, 1)
    else:
        target_date = date.today()

    range_start, range_end = _build_calendar_window(normalized_view, target_date)

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
        search=search,
        type=type,
    )
    query = query.where(
        ShopCutPlan.scheduled_start_date.is_not(None),
        ShopCutPlan.scheduled_start_date < range_end,
    )

    plans = await _fetch_all_ordered_plans(db, query)
    plans = [plan for plan in plans if _task_overlaps_window(plan, range_start, range_end)]
    total = len(plans)
    paginated_plans = plans[skip:skip + limit]
    serialized_plans, grouped_plans = await _serialize_and_group_plans(db, paginated_plans)

    return {
        "success": True,
        "message": "Shop plans retrieved successfully",
        "data": {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "month": target_date.month,
            "year": target_date.year,
            "view": normalized_view,
            "reference_date": target_date.isoformat(),
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


@router.get("/plans/fab/{fab_id}/exists", response_model=dict)
async def has_shop_plans_for_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check whether a FAB has any existing shop cut plans."""
    existing_plan_id = (
        await db.execute(
            select(ShopCutPlan.id)
            .where(ShopCutPlan.fab_id == fab_id)
            .limit(1)
        )
    ).scalar_one_or_none()

    return {
        "success": True,
        "message": "Shop plan existence checked successfully",
        "data": {
            "fab_id": fab_id,
            "has_shop_cut_plans": existing_plan_id is not None,
        },
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

    work_percentage, total_actual_hours, total_actual_seconds = await _recalculate_shop_plan_work_percentage(
        db=db,
        plan=plan,
        as_of=datetime.now().replace(second=0, microsecond=0),
    )
    
    ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
    workstation = ws_result.scalar_one_or_none()
    
    user_result = await db.execute(select(User).where(User.id == plan.user_id))
    operator = user_result.scalar_one_or_none()
    return {
        "success": True,
        "message": "Shop plan retrieved successfully",
        "data": {
            "id": plan.id,
            "fab_id": plan.fab_id,
            "sequence": plan.sequence,
            "workstation_id": plan.workstation_id,
            "workstation_name": workstation.name if workstation else None,
            "planning_section_id": plan.planning_section_id,
            "operator_id": plan.user_id,
            "operator_name": (f"{operator.first_name} {operator.last_name}".strip() or operator.username) if operator else None,
            "estimated_hours": plan.estimated_hours,
            "total_actual_seconds": total_actual_seconds,
            "total_actual_hours": total_actual_hours,
            "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
            "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "work_percentage": work_percentage,
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
        _validate_manual_schedule_interval(scheduled_start, stage.estimated_hours)
        await _assert_no_shop_plan_conflicts(
            db,
            plan_id=plan.id,
            fab_id=plan.fab_id,
            workstation_id=stage.workstation_id,
            operator_id=stage.operator_ids[0],
            scheduled_start=scheduled_start,
            estimated_hours=stage.estimated_hours,
        )

        plan.workstation_id = stage.workstation_id
        plan.planning_section_id = stage.planning_section_id
        plan.user_id = stage.operator_ids[0]
        plan.sequence = stage.sequence
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
                "sequence": plan.sequence,
                "workstation_id": plan.workstation_id,
                "planning_section_id": plan.planning_section_id,
                "operator_id": plan.user_id,
                "operator_name": (f"{user.first_name} {user.last_name}".strip() or user.username) if user else None,
                "estimated_hours": plan.estimated_hours,
                "workstation_name": workstation.name if workstation else None,
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
        _validate_manual_schedule_interval(scheduled_start, plan.estimated_hours)
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


async def _can_manage_shop_cut_plan_timer(db: AsyncSession, current_user: User, plan: ShopCutPlan) -> bool:
    if current_user.id == plan.user_id:
        return True

    if getattr(current_user, "is_super_admin", False):
        return True

    roles_result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    role_names = {str(r[0]).strip().lower() for r in roles_result.all() if r[0]}
    return any(name in role_names for name in {"admin", "administrator", "supervisor"})


async def _recalculate_shop_plan_work_percentage(
    db: AsyncSession,
    plan: ShopCutPlan,
    as_of: datetime,
) -> Tuple[int, float, int]:
    totals_result = await db.execute(
        select(func.coalesce(func.sum(ShopCutPlanTimerSession.total_work_seconds), 0))
        .where(ShopCutPlanTimerSession.shop_cut_plan_id == plan.id)
    )
    stored_seconds = int(totals_result.scalar() or 0)

    running_result = await db.execute(
        select(ShopCutPlanTimerSession)
        .where(
            ShopCutPlanTimerSession.shop_cut_plan_id == plan.id,
            ShopCutPlanTimerSession.status == "running",
            ShopCutPlanTimerSession.current_run_start_at.is_not(None),
        )
    )
    running_sessions = running_result.scalars().all()

    in_progress_seconds = 0
    for session in running_sessions:
        run_start = _normalize_naive_dt(session.current_run_start_at)
        if run_start and as_of > run_start:
            in_progress_seconds += int((as_of - run_start).total_seconds())

    total_actual_seconds = max(0, stored_seconds + in_progress_seconds)
    total_actual_hours = total_actual_seconds / 3600.0

    estimated_hours = float(plan.estimated_hours or 0)
    if estimated_hours <= 0:
        work_percentage = 0
    else:
        work_percentage = min(100, int((total_actual_hours / estimated_hours) * 100))

    return work_percentage, round(total_actual_hours, 4), total_actual_seconds


@router.post("/plans/{plan_id}/timer/action", response_model=dict)
async def manage_shop_cut_plan_timer(
    plan_id: int,
    payload: ShopCutPlanTimerActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        action = (payload.action or "").strip().lower()
        if action not in {"start", "pause", "resume", "stop"}:
            raise HTTPException(status_code=400, detail="action must be one of: start, pause, resume, stop")

        action_ts = _normalize_naive_dt(payload.timestamp) if payload.timestamp else datetime.now().replace(second=0, microsecond=0)

        plan_result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Shop plan with ID {plan_id} not found")

        if not await _can_manage_shop_cut_plan_timer(db, current_user, plan):
            raise HTTPException(status_code=403, detail="Not authorized to control this timer")

        active_result = await db.execute(
            select(ShopCutPlanTimerSession)
            .where(
                ShopCutPlanTimerSession.shop_cut_plan_id == plan_id,
                ShopCutPlanTimerSession.operator_id == plan.user_id,
                ShopCutPlanTimerSession.status.in_(["running", "paused"]),
            )
            .order_by(ShopCutPlanTimerSession.created_at.desc())
            .limit(1)
        )
        active_session = active_result.scalars().first()

        if action == "start":
            if active_session:
                raise HTTPException(status_code=400, detail="An active timer session already exists")

            session = ShopCutPlanTimerSession(
                shop_cut_plan_id=plan_id,
                operator_id=plan.user_id,
                status="running",
                session_start_at=action_ts,
                current_run_start_at=action_ts,
                total_work_seconds=0,
                total_pause_seconds=0,
                created_at=datetime.now(),
                created_by=current_user.id,
            )
            db.add(session)
            await db.flush()

            db.add(
                ShopCutPlanTimerEvent(
                    session_id=session.id,
                    shop_cut_plan_id=plan_id,
                    operator_id=plan.user_id,
                    action="start",
                    event_at=action_ts,
                    note=payload.note,
                )
            )

            if not plan.actual_start_date:
                plan.actual_start_date = action_ts

        elif action == "pause":
            if not active_session or active_session.status != "running":
                raise HTTPException(status_code=400, detail="No running timer session found to pause")

            run_start = _normalize_naive_dt(active_session.current_run_start_at)
            if not run_start:
                raise HTTPException(status_code=400, detail="Timer session is missing current_run_start_at")

            elapsed = int(max(0, (action_ts - run_start).total_seconds()))
            active_session.total_work_seconds = int(active_session.total_work_seconds or 0) + elapsed
            active_session.status = "paused"
            active_session.current_run_start_at = None
            active_session.current_pause_start_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = current_user.id

            db.add(
                ShopCutPlanTimerEvent(
                    session_id=active_session.id,
                    shop_cut_plan_id=plan_id,
                    operator_id=plan.user_id,
                    action="pause",
                    event_at=action_ts,
                    note=payload.note,
                )
            )

        elif action == "resume":
            if not active_session or active_session.status != "paused":
                raise HTTPException(status_code=400, detail="No paused timer session found to resume")

            pause_start = _normalize_naive_dt(active_session.current_pause_start_at)
            if pause_start and action_ts > pause_start:
                pause_elapsed = int((action_ts - pause_start).total_seconds())
                active_session.total_pause_seconds = int(active_session.total_pause_seconds or 0) + max(0, pause_elapsed)

            active_session.status = "running"
            active_session.current_pause_start_at = None
            active_session.current_run_start_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = current_user.id

            db.add(
                ShopCutPlanTimerEvent(
                    session_id=active_session.id,
                    shop_cut_plan_id=plan_id,
                    operator_id=plan.user_id,
                    action="resume",
                    event_at=action_ts,
                    note=payload.note,
                )
            )

        else:
            if not active_session or active_session.status not in {"running", "paused"}:
                raise HTTPException(status_code=400, detail="No active timer session found to stop")

            if active_session.status == "running":
                run_start = _normalize_naive_dt(active_session.current_run_start_at)
                if run_start and action_ts > run_start:
                    elapsed = int((action_ts - run_start).total_seconds())
                    active_session.total_work_seconds = int(active_session.total_work_seconds or 0) + max(0, elapsed)

            if active_session.status == "paused":
                pause_start = _normalize_naive_dt(active_session.current_pause_start_at)
                if pause_start and action_ts > pause_start:
                    pause_elapsed = int((action_ts - pause_start).total_seconds())
                    active_session.total_pause_seconds = int(active_session.total_pause_seconds or 0) + max(0, pause_elapsed)

            active_session.status = "stopped"
            active_session.current_run_start_at = None
            active_session.current_pause_start_at = None
            active_session.stopped_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = current_user.id

            db.add(
                ShopCutPlanTimerEvent(
                    session_id=active_session.id,
                    shop_cut_plan_id=plan_id,
                    operator_id=plan.user_id,
                    action="stop",
                    event_at=action_ts,
                    note=payload.note,
                )
            )

            plan.actual_end_date = action_ts

        work_percentage, total_actual_hours, total_actual_seconds = await _recalculate_shop_plan_work_percentage(
            db=db,
            plan=plan,
            as_of=action_ts,
        )

        target_session = session if action == "start" else active_session
        if target_session:
            target_session.work_percentage = work_percentage

        ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
        workstation = ws_result.scalar_one_or_none()

        operator_result = await db.execute(select(User).where(User.id == plan.user_id))
        operator = operator_result.scalar_one_or_none()

        plan.work_percentage = work_percentage
        plan.updated_at = datetime.now()
        plan.updated_by = current_user.id

        await db.commit()

        return {
            "success": True,
            "message": f"Timer {action} successful",
            "data": {
                "shop_cut_plan_id": plan.id,
                "operator_id": plan.user_id,
                "operator_name": (f"{operator.first_name} {operator.last_name}".strip() or operator.username) if operator else None,
                "workstation_id": plan.workstation_id,
                "workstation_name": workstation.name if workstation else None,
                "action": action,
                "note": payload.note,
                "timestamp": action_ts.isoformat(),
                "total_actual_seconds": total_actual_seconds,
                "total_actual_hours": total_actual_hours,
                "estimated_hours": float(plan.estimated_hours or 0),
                "work_percentage": plan.work_percentage,
            }
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process timer action: {str(e)}")


@router.get("/plans/{plan_id}/timer", response_model=dict)
async def get_shop_cut_plan_timer_state(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan_result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Shop plan with ID {plan_id} not found")

    if not await _can_manage_shop_cut_plan_timer(db, current_user, plan):
        raise HTTPException(status_code=403, detail="Not authorized to view this timer")

    latest_result = await db.execute(
        select(ShopCutPlanTimerSession)
        .where(
            ShopCutPlanTimerSession.shop_cut_plan_id == plan_id,
            ShopCutPlanTimerSession.operator_id == plan.user_id,
        )
        .order_by(ShopCutPlanTimerSession.created_at.desc())
        .limit(1)
    )
    latest = latest_result.scalars().first()

    now_ts = datetime.now().replace(second=0, microsecond=0)
    work_percentage, total_actual_hours, total_actual_seconds = await _recalculate_shop_plan_work_percentage(
        db=db,
        plan=plan,
        as_of=now_ts,
    )

    ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
    workstation = ws_result.scalar_one_or_none()

    operator_result = await db.execute(select(User).where(User.id == plan.user_id))
    operator = operator_result.scalar_one_or_none()

    return {
        "success": True,
        "message": "Timer state retrieved successfully",
        "data": {
            "shop_cut_plan_id": plan.id,
            "operator_id": plan.user_id,
            "operator_name": (f"{operator.first_name} {operator.last_name}".strip() or operator.username) if operator else None,
            "workstation_id": plan.workstation_id,
            "workstation_name": workstation.name if workstation else None,
            "session": {
                "id": latest.id,
                "status": latest.status,
                "session_start_at": latest.session_start_at.isoformat() if latest.session_start_at else None,
                "current_run_start_at": latest.current_run_start_at.isoformat() if latest.current_run_start_at else None,
                "current_pause_start_at": latest.current_pause_start_at.isoformat() if latest.current_pause_start_at else None,
                "stopped_at": latest.stopped_at.isoformat() if latest.stopped_at else None,
                "work_percentage": int(latest.work_percentage or 0),
            } if latest else None,
            "total_actual_seconds": total_actual_seconds,
            "total_actual_hours": total_actual_hours,
            "estimated_hours": float(plan.estimated_hours or 0),
            "work_percentage": work_percentage,
        }
    }


@router.get("/plans/{plan_id}/timer/history", response_model=dict)
async def get_shop_cut_plan_timer_history(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan_result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Shop plan with ID {plan_id} not found")

    if not await _can_manage_shop_cut_plan_timer(db, current_user, plan):
        raise HTTPException(status_code=403, detail="Not authorized to view this timer history")

    sessions_result = await db.execute(
        select(ShopCutPlanTimerSession)
        .where(
            ShopCutPlanTimerSession.shop_cut_plan_id == plan_id,
            ShopCutPlanTimerSession.operator_id == plan.user_id,
        )
        .order_by(ShopCutPlanTimerSession.created_at.asc())
    )
    sessions = sessions_result.scalars().all()

    events_result = await db.execute(
        select(ShopCutPlanTimerEvent)
        .where(
            ShopCutPlanTimerEvent.shop_cut_plan_id == plan_id,
            ShopCutPlanTimerEvent.operator_id == plan.user_id,
        )
        .order_by(ShopCutPlanTimerEvent.event_at.asc())
    )
    events = events_result.scalars().all()

    ws_result = await db.execute(select(WorkStation).where(WorkStation.id == plan.workstation_id))
    workstation = ws_result.scalar_one_or_none()

    operator_result = await db.execute(select(User).where(User.id == plan.user_id))
    operator = operator_result.scalar_one_or_none()

    return {
        "success": True,
        "message": "Timer history retrieved successfully",
        "data": {
            "shop_cut_plan_id": plan_id,
            "operator_id": plan.user_id,
            "operator_name": (f"{operator.first_name} {operator.last_name}".strip() or operator.username) if operator else None,
            "workstation_id": plan.workstation_id,
            "workstation_name": workstation.name if workstation else None,
            "sessions": [
                {
                    "id": s.id,
                    "status": s.status,
                    "session_start_at": s.session_start_at.isoformat() if s.session_start_at else None,
                    "current_run_start_at": s.current_run_start_at.isoformat() if s.current_run_start_at else None,
                    "current_pause_start_at": s.current_pause_start_at.isoformat() if s.current_pause_start_at else None,
                    "stopped_at": s.stopped_at.isoformat() if s.stopped_at else None,
                    "total_work_seconds": int(s.total_work_seconds or 0),
                    "total_pause_seconds": int(s.total_pause_seconds or 0),
                    "work_percentage": int(s.work_percentage or 0),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ],
            "events": [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "action": e.action,
                    "event_at": e.event_at.isoformat() if e.event_at else None,
                    "note": e.note,
                }
                for e in events
            ],
        }
    }


async def _serialize_and_group_plans(db: AsyncSession, plans: list[ShopCutPlan]):
    serialized_plans = []
    grouped = {}

    fab_cache: Dict[int, Optional[Fab]] = {}
    job_cache: Dict[int, Optional[BusinessJob]] = {}
    account_cache: Dict[int, Optional[Account]] = {}

    current_plan_stage_by_fab = await _get_current_plan_stage_by_fab(
        db,
        [plan.fab_id for plan in plans if plan.fab_id is not None],
    )

    for plan in plans:
        work_percentage, total_actual_hours, total_actual_seconds = await _recalculate_shop_plan_work_percentage(
            db=db,
            plan=plan,
            as_of=datetime.now().replace(second=0, microsecond=0),
        )

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
            "current_plan_stage": current_plan_stage_by_fab.get(plan.fab_id),
            "fab_type": fab_type,
            "account_name": account_name,
            "job_name": job_name,
            "job_number": job_number,
            "business_job": business_job_payload,  # full BusinessJob data
            "sequence": plan.sequence,
            "workstation_id": plan.workstation_id,
            "workstation_name": workstation_name,
            "planning_section_id": plan.planning_section_id,
            "plan_name": plan_name,
            "operator_id": plan.user_id,
            "operator_name": operator_name,
            "estimated_hours": plan.estimated_hours,
            "total_actual_seconds": total_actual_seconds,
            "total_actual_hours": total_actual_hours,
            "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
            "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "work_percentage": work_percentage,
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


async def _get_current_plan_stage_by_fab(db: AsyncSession, fab_ids: List[int]) -> Dict[int, Optional[str]]:
    if not fab_ids:
        return {}

    unique_fab_ids = sorted(set(fab_ids))
    plans_result = await db.execute(
        select(ShopCutPlan)
        .where(ShopCutPlan.fab_id.in_(unique_fab_ids))
        .order_by(ShopCutPlan.fab_id.asc(), ShopCutPlan.sequence.asc(), ShopCutPlan.id.asc())
    )
    all_plans = plans_result.scalars().all()

    section_ids = {p.planning_section_id for p in all_plans if p.planning_section_id is not None}
    planning_section_map: Dict[int, str] = {}
    if section_ids:
        sections_result = await db.execute(
            select(PlanningSection.id, PlanningSection.plan_name).where(PlanningSection.id.in_(section_ids))
        )
        planning_section_map = {sid: name for sid, name in sections_result.all() if sid is not None and name}

    plans_by_fab: Dict[int, List[ShopCutPlan]] = {}
    for plan in all_plans:
        if plan.fab_id is None:
            continue
        plans_by_fab.setdefault(plan.fab_id, []).append(plan)

    result: Dict[int, Optional[str]] = {}
    now_floor = datetime.now().replace(second=0, microsecond=0)

    for fab_id, fab_plans in plans_by_fab.items():
        current_stage_name: Optional[str] = None
        for plan in fab_plans:
            work_percentage, _, _ = await _recalculate_shop_plan_work_percentage(
                db=db,
                plan=plan,
                as_of=now_floor,
            )
            if int(work_percentage or 0) < 100:
                current_stage_name = planning_section_map.get(plan.planning_section_id)
                break

        result[fab_id] = current_stage_name

    for fab_id in unique_fab_ids:
        result.setdefault(fab_id, None)

    return result


def _normalize_naive_dt(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value and value.tzinfo else value

def _compute_lunch_adjusted_end(start: datetime, hours: float) -> datetime:
    """Return the real end time, automatically adding the 1-hour lunch gap when
    the job interval crosses the 12:00 PM – 1:00 PM break."""
    naive_end = start + timedelta(hours=hours)
    lunch_start, lunch_end = _lunch_window_for_day(start)
    if start < lunch_start < naive_end:
        naive_end += (lunch_end - lunch_start)
    return naive_end


def _compute_business_rollover_end(start: datetime, hours: float) -> datetime:
    """Return the end time after consuming working hours across business days.

    The calculation honors the 7 AM - 4 PM workday, skips the 12 PM - 1 PM
    lunch break, and continues any remaining duration on the next business day.
    """
    remaining_seconds = float(hours) * 3600
    if remaining_seconds <= 0:
        return start

    cursor = _next_business_start(start)

    while True:
        day_start, day_end = _business_window_for_day(cursor)
        lunch_start, lunch_end = _lunch_window_for_day(cursor)

        if cursor < day_start:
            cursor = day_start
            continue

        if lunch_start <= cursor < lunch_end:
            cursor = lunch_end
            continue

        if cursor >= day_end:
            next_day = (cursor + timedelta(days=1)).replace(
                hour=BUSINESS_START_HOUR,
                minute=0,
                second=0,
                microsecond=0,
            )
            cursor = _next_business_start(next_day)
            continue

        block_end = lunch_start if cursor < lunch_start else day_end
        available_seconds = (block_end - cursor).total_seconds()

        if remaining_seconds <= available_seconds:
            return cursor + timedelta(seconds=remaining_seconds)

        remaining_seconds -= available_seconds

        if block_end == lunch_start:
            cursor = lunch_end
        else:
            next_day = (cursor + timedelta(days=1)).replace(
                hour=BUSINESS_START_HOUR,
                minute=0,
                second=0,
                microsecond=0,
            )
            cursor = _next_business_start(next_day)


def _compute_schedule_end_time_iso(
    scheduled_start: Optional[datetime],
    estimated_hours: Optional[float]
) -> Optional[str]:
    if not scheduled_start or estimated_hours is None:
        return None
    try:
        return _compute_lunch_adjusted_end(scheduled_start, float(estimated_hours)).isoformat()
    except (TypeError, ValueError):
        return None


def _format_scheduled_time_range(
    start: Optional[datetime],
    end: Optional[datetime]
) -> Optional[str]:
    """Format scheduled time range as human-readable string.
    
    Same day:     "Apr 10, 10:00 AM – 2:30 PM"
    Different day: "Apr 10, 10:00 AM – Apr 11, 2:30 PM"
    """
    if not start or not end:
        return None
    
    try:
        # Normalize to naive datetimes if needed
        if start.tzinfo:
            start = start.replace(tzinfo=None)
        if end.tzinfo:
            end = end.replace(tzinfo=None)
        
        # Format time portion (e.g., "10:00 AM", "2:30 PM")
        start_time = start.strftime("%-I:%M %p").lstrip("0")  # "10:00 AM" or "2:30 PM" (not "02:30")
        end_time = end.strftime("%-I:%M %p").lstrip("0")
        
        # Format date portion (e.g., "Apr 10")
        start_date = start.strftime("%b %-d").replace(" 0", " ")  # "Apr 10" not "Apr 010"
        end_date = end.strftime("%b %-d").replace(" 0", " ")
        
        # Check if same day
        if start.date() == end.date():
            return f"{start_date}, {start_time} – {end_time}"
        else:
            return f"{start_date}, {start_time} – {end_date}, {end_time}"
    except (TypeError, ValueError, AttributeError):
        return None


def _validate_month_year(month: int, year: int) -> None:
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    if year < 1900 or year > 9999:
        raise HTTPException(status_code=400, detail="year must be between 1900 and 9999")


def _build_calendar_window(view: str, reference_date: date) -> tuple[datetime, datetime]:
    start_of_day = datetime.combine(reference_date, datetime.min.time())

    if view == "day":
        return start_of_day, start_of_day + timedelta(days=1)

    if view == "week":
        week_start = start_of_day - timedelta(days=reference_date.weekday())
        return week_start, week_start + timedelta(days=7)

    if view == "month":
        month_start = start_of_day.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        return month_start, next_month

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="view must be one of: day, week, month")


def _task_overlaps_window(plan: ShopCutPlan, range_start: datetime, range_end: datetime) -> bool:
    if not plan.scheduled_start_date:
        return False

    task_start = plan.scheduled_start_date
    if plan.estimated_hours is None:
        task_end = task_start
    else:
        try:
            task_end = task_start + timedelta(hours=float(plan.estimated_hours))
        except (TypeError, ValueError):
            task_end = task_start

    return task_start < range_end and task_end >= range_start


def _build_shop_plans_query():
    return (
        select(ShopCutPlan)
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
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
    search: Optional[str],
    type: Optional[str],
):
    if fab_id is not None:
        query = query.where(ShopCutPlan.fab_id == fab_id)

    if search_fab_id:
        query = query.where(cast(ShopCutPlan.fab_id, String).ilike(f"%{search_fab_id.strip()}%"))

    search_value = search.strip() if isinstance(search, str) else search
    search_type = type.strip().lower() if isinstance(type, str) else None
    if search_value and search_type:
        if search_type == "fab_id":
            query = query.where(cast(ShopCutPlan.fab_id, String) == search_value)
        elif search_type == "job_number":
            query = query.where(cast(BusinessJob.job_number, String) == search_value)
        elif search_type == "job_name":
            query = query.where(BusinessJob.name.ilike(f"%{search_value}%"))

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


async def _fetch_all_ordered_plans(db: AsyncSession, query):
    result = await db.execute(
        query.order_by(
            ShopCutPlan.scheduled_start_date.asc(),
            ShopCutPlan.sequence.asc(),
            ShopCutPlan.id.asc(),
        )
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

        # Stage-level validations and prep
        stage_meta = []
        workstation_ids = set()
        operator_ids = set()
        max_duration_hours = 0.0

        # Sort stages by declared sequence before building stage_meta
        sorted_stages = sorted(plan_data.stages, key=lambda s: s.sequence)
        for stage in sorted_stages:
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
                "sequence": stage.sequence,
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

        # Build N complete sequences, each being a fully chained set of stages.
        # Stage i+1 in a sequence is constrained to start at or after stage i ends.
        sequences: List[dict] = []
        first_stage_cursor = _next_business_start(_align_to_slot(window_start, slot_minutes))
        _MAX_ATTEMPTS = max_suggestions_per_stage * 50  # safety cap

        attempts = 0
        while len(sequences) < max_suggestions_per_stage and first_stage_cursor < window_end:
            attempts += 1
            if attempts > _MAX_ATTEMPTS:
                break

            sequence_stages: List[dict] = []
            valid = True
            stage_cursor = first_stage_cursor

            for meta in stage_meta:
                stage_window = max(window_start, stage_cursor)
                ws_busy = busy_by_ws.get(meta["workstation_id"], [])
                user_busy = busy_by_user.get(meta["operator_id"], [])

                slot: Optional[Tuple[datetime, datetime]] = None
                for c_start, c_end in _build_candidate_ranges(stage_window, window_end, meta["estimated_hours"], slot_minutes):
                    if any(_intervals_overlap(c_start, c_end, b_s, b_e) for b_s, b_e in ws_busy):
                        continue
                    if any(_intervals_overlap(c_start, c_end, b_s, b_e) for b_s, b_e in user_busy):
                        continue
                    if any(_intervals_overlap(c_start, c_end, b_s, b_e) for b_s, b_e in busy_by_fab):
                        continue
                    slot = (c_start, c_end)
                    break

                if slot is None:
                    valid = False
                    break

                sequence_stages.append({
                    "sequence": meta["sequence"],
                    "planning_section_id": meta["planning_section_id"],
                    "plan_name": meta["plan_name"],
                    "workstation_id": meta["workstation_id"],
                    "workstation_name": meta["workstation_name"],
                    "operator_id": meta["operator_id"],
                    "operator_name": meta["operator_name"],
                    "estimated_hours": meta["estimated_hours"],
                    "start": slot[0].isoformat(),
                    "end": slot[1].isoformat(),
                })
                stage_cursor = slot[1]  # next stage starts exactly where this one ends

            if valid and sequence_stages:
                sequences.append({
                    "sequence_index": len(sequences),
                    "stages": sequence_stages,
                })
                # Advance stage-1 starting point by one slot for the next sequence
                stage1_start = datetime.fromisoformat(sequence_stages[0]["start"])
                first_stage_cursor = _next_business_start(
                    _align_to_slot(stage1_start + timedelta(minutes=slot_minutes), slot_minutes)
                )
            else:
                # No valid complete sequence from this cursor; skip ahead
                first_stage_cursor = _next_business_start(
                    _align_to_slot(first_stage_cursor + timedelta(minutes=slot_minutes), slot_minutes)
                )

        return {
            "success": True,
            "message": "Suggestions generated",
            "data": {
                "fab_id": plan_data.fab_id,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "slot_minutes": slot_minutes,
                "max_suggestions_per_stage": max_suggestions_per_stage,
                "suggestions": sequences,
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


BUSINESS_START_HOUR = 7
BUSINESS_END_HOUR = 16
LUNCH_BREAK_START_HOUR = 12
LUNCH_BREAK_END_HOUR = 13
BUSINESS_WEEKDAYS = {0, 1, 2, 3, 4}  # Monday-Friday


def _is_business_day(value: datetime) -> bool:
    return value.weekday() in BUSINESS_WEEKDAYS


def _business_window_for_day(value: datetime) -> Tuple[datetime, datetime]:
    start = value.replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
    end = value.replace(hour=BUSINESS_END_HOUR, minute=0, second=0, microsecond=0)
    return start, end


def _lunch_window_for_day(value: datetime) -> Tuple[datetime, datetime]:
    lunch_start = value.replace(hour=LUNCH_BREAK_START_HOUR, minute=0, second=0, microsecond=0)
    lunch_end = value.replace(hour=LUNCH_BREAK_END_HOUR, minute=0, second=0, microsecond=0)
    return lunch_start, lunch_end


def _overlaps_lunch(start: datetime, end: datetime) -> bool:
    lunch_start, lunch_end = _lunch_window_for_day(start)
    return _intervals_overlap(start, end, lunch_start, lunch_end)


def _next_business_start(value: datetime) -> datetime:
    cursor = value.replace(second=0, microsecond=0)

    while not _is_business_day(cursor):
        cursor = (cursor + timedelta(days=1)).replace(second=0, microsecond=0)

    day_start, day_end = _business_window_for_day(cursor)
    if cursor < day_start:
        return day_start
    if cursor >= day_end:
        next_day = (cursor + timedelta(days=1)).replace(
            hour=BUSINESS_START_HOUR,
            minute=0,
            second=0,
            microsecond=0,
        )
        return _next_business_start(next_day)

    lunch_start, lunch_end = _lunch_window_for_day(cursor)
    if lunch_start <= cursor < lunch_end:
        return lunch_end

    return cursor


def _is_valid_business_interval(start: datetime, end: datetime) -> bool:
    if end <= start:
        return False
    if not _is_business_day(start):
        return False
    if not _is_business_day(end):
        return False
    if start.date() != end.date():
        return False

    day_start, day_end = _business_window_for_day(start)
    if not (start >= day_start and end <= day_end):
        return False

    lunch_start, lunch_end = _lunch_window_for_day(start)
    if lunch_start <= start < lunch_end:
        return False
    if lunch_start < end <= lunch_end:
        return False

    return True


def _validate_manual_schedule_interval(start: Optional[datetime], estimated_hours: Optional[float]) -> None:
    """Validate a manually supplied schedule start time.

    Rules:
    - scheduled_start is required
    - scheduled_start must not fall within the 12:00 PM – 1:00 PM lunch break
    """
    if start is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_start is required",
        )

    lunch_start, lunch_end = _lunch_window_for_day(start)
    if lunch_start <= start < lunch_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_start cannot fall within the lunch break (12:00 PM – 1:00 PM). Please choose a time before 12:00 PM or at 1:00 PM or later.",
        )


def _is_valid_business_start(start: datetime) -> bool:
    if not _is_business_day(start):
        return False

    day_start, day_end = _business_window_for_day(start)
    if not (day_start <= start < day_end):
        return False

    lunch_start, lunch_end = _lunch_window_for_day(start)
    return not (lunch_start <= start < lunch_end)


def _advance_after_invalid_interval(cursor: datetime, slot_minutes: int) -> datetime:
    """
    Advance cursor after an invalid candidate interval by one slot,
    then snap to the next weekday if needed.
    """
    lunch_start, lunch_end = _lunch_window_for_day(cursor)
    if lunch_start <= cursor < lunch_end:
        next_cursor = lunch_end
    else:
        next_cursor = cursor + timedelta(minutes=slot_minutes)
    next_cursor = _align_to_slot(next_cursor, slot_minutes)
    return _next_business_start(next_cursor)


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
    cursor = _next_business_start(window_start)
    cursor = _align_to_slot(cursor, slot_minutes)
    cursor = _next_business_start(cursor)
    step = timedelta(minutes=slot_minutes)

    while cursor + duration <= window_end:
        candidate_end = cursor + duration

        if _is_valid_business_interval(cursor, candidate_end):
            out.append((cursor, candidate_end))
            cursor += step
            continue

        cursor = _advance_after_invalid_interval(cursor, slot_minutes)

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

        ordered_requests = sorted(payload.requests, key=lambda r: r.sequence)
        sequences = [r.sequence for r in ordered_requests]
        if any(seq <= 0 for seq in sequences):
            raise HTTPException(status_code=400, detail="sequence must be greater than 0")
        if len(sequences) != len(set(sequences)):
            raise HTTPException(status_code=400, detail="sequence values must be unique")

        start_from = _normalize_naive_dt(payload.start_from) if payload.start_from else datetime.now().replace(second=0, microsecond=0)
        start_from = _align_to_slot(start_from, payload.slot_minutes)
        start_from = _next_business_start(start_from)
        start_from = _align_to_slot(start_from, payload.slot_minutes)
        start_from = _next_business_start(start_from)
        search_end = start_from + timedelta(days=payload.search_horizon_days)
        step = timedelta(minutes=payload.slot_minutes)

        operator_ids = {r.operator_id for r in ordered_requests}
        workstation_ids = {r.workstation_id for r in ordered_requests}

        # Validate operators/workstations exist and build id->name maps
        user_rows = (
            await db.execute(
                select(User.id, User.first_name, User.last_name, User.username)
                .where(User.id.in_(list(operator_ids)))
            )
        ).all()
        ws_rows = (
            await db.execute(
                select(WorkStation.id, WorkStation.name)
                .where(WorkStation.id.in_(list(workstation_ids)))
            )
        ).all()
        valid_users = {r[0] for r in user_rows}
        valid_ws = {r[0] for r in ws_rows}
        user_name_map = {
            row[0]: (f"{(row[1] or '').strip()} {(row[2] or '').strip()}".strip() or (row[3] or None))
            for row in user_rows
        }
        ws_name_map = {row[0]: row[1] for row in ws_rows}

        missing_users = sorted(operator_ids - valid_users)
        missing_ws = sorted(workstation_ids - valid_ws)
        if missing_users:
            raise HTTPException(status_code=404, detail=f"Operator(s) not found: {missing_users}")
        if missing_ws:
            raise HTTPException(status_code=404, detail=f"Workstation(s) not found: {missing_ws}")

        # Validate planning sections and build id->name map
        section_ids = {r.planning_section_id for r in ordered_requests}
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
            p_end = _compute_lunch_adjusted_end(p_start, dur_hours)
            busy_by_ws.setdefault(p.workstation_id, []).append((p_start, p_end))
            busy_by_user.setdefault(p.user_id, []).append((p_start, p_end))

        # Merge intervals per resource
        for ws_id, intervals in busy_by_ws.items():
            busy_by_ws[ws_id] = _merge_intervals(intervals)
        for user_id, intervals in busy_by_user.items():
            busy_by_user[user_id] = _merge_intervals(intervals)

        results = []
        # Stage requests are chained in request order. Stage N starts on/after
        # Stage N-1 earliest proposed end.
        dependency_start = start_from
        chain_blocked = False

        for req in ordered_requests:
            duration_hours = float(req.estimated_hours or 0)
            if duration_hours <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"estimated_hours must be > 0 for operator_id={req.operator_id}, workstation_id={req.workstation_id}"
                )

            combined_busy = _merge_intervals(
                (busy_by_ws.get(req.workstation_id, []) + busy_by_user.get(req.operator_id, []))
            )

            proposals = []
            if not chain_blocked:
                cursor = _align_to_slot(max(start_from, dependency_start), payload.slot_minutes)
                cursor = _next_business_start(cursor)
            else:
                cursor = search_end

            while cursor < search_end and len(proposals) < payload.max_proposals_per_request:
                candidate_end = _compute_business_rollover_end(cursor, duration_hours)
                if candidate_end > search_end:
                    break

                if not _is_valid_business_start(cursor):
                    cursor = _advance_after_invalid_interval(cursor, payload.slot_minutes)
                    continue

                overlap = _first_overlap(cursor, candidate_end, combined_busy)

                if overlap is None:
                    proposals.append({
                        "start": cursor.isoformat(),
                        "end": candidate_end.isoformat(),
                        "scheduled_time": _format_scheduled_time_range(cursor, candidate_end)
                    })
                    cursor = cursor + step
                    cursor = _align_to_slot(cursor, payload.slot_minutes)
                    cursor = _next_business_start(cursor)
                else:
                    cursor = _align_to_slot(max(cursor + step, overlap[1]), payload.slot_minutes)
                    cursor = _next_business_start(cursor)

            if proposals:
                dependency_start = datetime.fromisoformat(proposals[0]["end"])
            else:
                chain_blocked = True

            results.append({
                "sequence": req.sequence,
                "planning_section_id": req.planning_section_id,
                "plan_name": ps_map.get(req.planning_section_id),
                "operator_id": req.operator_id,
                "operator_name": user_name_map.get(req.operator_id),
                "workstation_id": req.workstation_id,
                "workstation_name": ws_name_map.get(req.workstation_id),
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


async def _assert_no_shop_plan_conflicts(
    db: AsyncSession,
    *,
    plan_id: int,
    fab_id: int,
    workstation_id: int,
    operator_id: int,
    scheduled_start: datetime,
    estimated_hours: float,
) -> None:
    proposed_end = _compute_lunch_adjusted_end(scheduled_start, float(estimated_hours))

    conflict_result = await db.execute(
        select(ShopCutPlan).where(
            ShopCutPlan.id != plan_id,
            ShopCutPlan.workstation_id == workstation_id,
            ShopCutPlan.scheduled_start_date.is_not(None),
            ShopCutPlan.scheduled_start_date < proposed_end,
        )
    )
    conflicting_plans = conflict_result.scalars().all()

    for other_plan in conflicting_plans:
        other_start = _normalize_naive_dt(other_plan.scheduled_start_date)
        other_hours = float(other_plan.estimated_hours or 0)
        if not other_start or other_hours <= 0:
            continue

        other_end = _compute_lunch_adjusted_end(other_start, other_hours)

        if _intervals_overlap(scheduled_start, proposed_end, other_start, other_end):
            readable_start_time = other_start.strftime("%I:%M %p").lstrip("0")
            readable_end_time = other_end.strftime("%I:%M %p").lstrip("0")
            readable_date = other_start.strftime("%b %d, %Y")
            conflicting_fab_id = other_plan.fab_id
            conflicting_workstation_id = other_plan.workstation_id
            conflicting_workstation_name = None
            if conflicting_workstation_id is not None:
                ws_result = await db.execute(
                    select(WorkStation.name).where(WorkStation.id == conflicting_workstation_id)
                )
                conflicting_workstation_name = ws_result.scalar_one_or_none()
        
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This schedule update conflicts with an existing plan scheduled "
                    f"from {readable_start_time} to {readable_end_time} on {readable_date}. "
                    f"Conflicting FAB ID: {conflicting_fab_id}. "
                    f"Conflicting Workstation ID: {conflicting_workstation_id}. "
                    f"Conflicting Workstation Name: {conflicting_workstation_name}. "
                    "Please choose a different time slot."
                ),
            )


async def _build_duplicate_section_conflict_detail(
    db: AsyncSession,
    *,
    fab_id: int,
    section_ids: List[int],
) -> dict:
    rows = (
        await db.execute(
            select(
                ShopCutPlan.id,
                ShopCutPlan.planning_section_id,
                PlanningSection.plan_name,
                ShopCutPlan.scheduled_start_date,
                ShopCutPlan.workstation_id,
                WorkStation.name,
                ShopCutPlan.user_id,
                User.first_name,
                User.last_name,
                User.username,
            )
            .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id)
            .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id)
            .join(User, User.id == ShopCutPlan.user_id)
            .where(
                ShopCutPlan.fab_id == fab_id,
                ShopCutPlan.planning_section_id.in_(section_ids),
            )
            .order_by(ShopCutPlan.planning_section_id.asc(), ShopCutPlan.id.asc())
        )
    ).all()

    conflicting_plans = []
    for row in rows:
        first_name = (row[7] or "").strip()
        last_name = (row[8] or "").strip()
        username = (row[9] or "").strip()
        operator_name = f"{first_name} {last_name}".strip() or username or None

        conflicting_plans.append(
            {
                "plan_id": row[0],
                "planning_section_id": row[1],
                "planning_section_name": row[2],
                "scheduled_start_date": row[3].isoformat() if row[3] else None,
                "workstation_id": row[4],
                "workstation_name": row[5],
                "operator_id": row[6],
                "operator_name": operator_name,
            }
        )

    section_names = sorted({p["planning_section_name"] for p in conflicting_plans if p["planning_section_name"]})
    section_label = ", ".join(section_names) if section_names else "selected planning section"

    return {
        "message": (
            f"A plan already exists for this job in the {section_label} section. "
            "Please choose a different planning section or update the existing plan."
        ),
        "conflict_type": "duplicate_planning_section_for_fab",
        "fab_id": fab_id,
        "conflicting_plans": conflicting_plans,
    }