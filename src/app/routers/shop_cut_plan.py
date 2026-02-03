from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Optional

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.shop_notes import ShopNotes
from src.app.database.user import User
from src.app.interface.business_schemas import (
    ShopCutPlanCreate,
    ShopCutPlanResponse,
    ShopCutPlanStageCreate
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response
from src.app.database.work_station import WorkStation

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
        # Verify FAB exists
        result = await db.execute(select(Fab).where(Fab.id == plan_data.fab_id))
        fab = result.scalar_one_or_none()
        
        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAB with ID {plan_data.fab_id} not found"
            )
        
        # Validate that stages exist
        if not plan_data.stages or len(plan_data.stages) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one stage is required"
            )
        
        created_plans = []
        
        # Create a shop cut plan for each stage
        for stage in plan_data.stages:
            # Validate workstation exists
            ws_result = await db.execute(
                select(WorkStation).where(WorkStation.id == stage.workstation_id)
            )
            workstation = ws_result.scalar_one_or_none()
            
            if not workstation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workstation with ID {stage.workstation_id} not found"
                )
            
            # Validate operators exist
            if not stage.operator_ids or len(stage.operator_ids) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"At least one operator is required for stage '{stage.stage_name}'"
                )
            
            for operator_id in stage.operator_ids:
                # Verify operator exists
                user_result = await db.execute(
                    select(User).where(User.id == operator_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Operator with ID {operator_id} not found"
                    )
                
                # Remove timezone from scheduled_start if present
                scheduled_start = stage.scheduled_start
                if scheduled_start.tzinfo is not None:
                    scheduled_start = scheduled_start.replace(tzinfo=None)
                
                # Validate estimated hours
                if stage.estimated_hours <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Estimated hours must be greater than 0"
                    )
                
                plan = ShopCutPlan(
                    fab_id=plan_data.fab_id,
                    workstation_id=stage.workstation_id,
                    user_id=operator_id,
                    estimated_hours=stage.estimated_hours,
                    scheduled_start_date=scheduled_start,
                    cut_type=stage.cut_type.lower(),  # Changed from stage.stage_name
                    work_percentage=0,
                    created_by=current_user.id,
                    created_at=datetime.now()
                )
                db.add(plan)
                created_plans.append(plan)
        
        # Add shop note
        shop_note = ShopNotes(
            fab_id=plan_data.fab_id,
            note=f"Shop cut plan created with {len(plan_data.stages)} stage(s). Total estimated hours: {plan_data.total_estimated_hours}",
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.add(shop_note)
        
        await db.commit()
        
        # Refresh all plans to get IDs
        for plan in created_plans:
            await db.refresh(plan)
        
        return {
            "success": True,
            "message": f"Shop plans created successfully with {len(created_plans)} plan(s)",
            "data": {
                "fab_id": plan_data.fab_id,
                "total_estimated_hours": plan_data.total_estimated_hours,
                "plans_created": len(created_plans),
                "plans": [
                    {
                        "id": plan.id,
                        "stage_name": plan.cut_type,
                        "workstation_id": plan.workstation_id,
                        "operator_id": plan.user_id,
                        "estimated_hours": plan.estimated_hours,
                        "scheduled_start_date": plan.scheduled_start_date.isoformat(),
                        "work_percentage": plan.work_percentage
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
    workstation_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    cut_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shop cut plans with optional filters"""
    
    query = select(ShopCutPlan)
    
    if fab_id is not None:
        query = query.where(ShopCutPlan.fab_id == fab_id)
    if workstation_id is not None:
        query = query.where(ShopCutPlan.workstation_id == workstation_id)
    if operator_id is not None:
        query = query.where(ShopCutPlan.user_id == operator_id)
    if cut_type:
        query = query.where(ShopCutPlan.cut_type == cut_type.lower())
    
    # Get total count
    count_result = await db.execute(select(func.count(ShopCutPlan.id)).select_from(ShopCutPlan))
    total = count_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(ShopCutPlan.scheduled_start_date)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return {
        "success": True,
        "message": "Shop plans retrieved successfully",
        "data": {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "plans": [
                {
                    "id": plan.id,
                    "fab_id": plan.fab_id,
                    "workstation_id": plan.workstation_id,
                    "operator_id": plan.user_id,
                    "estimated_hours": plan.estimated_hours,
                    "scheduled_start_date": plan.scheduled_start_date.isoformat(),
                    "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
                    "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
                    "work_percentage": plan.work_percentage,
                    "cut_type": plan.cut_type,
                    "notes": plan.notes,
                    "created_at": plan.created_at.isoformat(),
                    "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
                }
                for plan in plans
            ]
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
            "operator_id": plan.user_id,
            "estimated_hours": plan.estimated_hours,
            "scheduled_start_date": plan.scheduled_start_date.isoformat(),
            "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "work_percentage": plan.work_percentage,
            "cut_type": plan.cut_type,
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
    update_data: ShopCutPlanStageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a shop cut plan with stage details"""
    
    try:
        # Get the plan
        result = await db.execute(select(ShopCutPlan).where(ShopCutPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shop plan with ID {plan_id} not found"
            )
        
        # Validate workstation exists
        ws_result = await db.execute(
            select(WorkStation).where(WorkStation.id == update_data.workstation_id)
        )
        workstation = ws_result.scalar_one_or_none()
        
        if not workstation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workstation with ID {update_data.workstation_id} not found"
            )
        
        # Validate operator exists
        user_result = await db.execute(
            select(User).where(User.id == update_data.operator_ids[0])
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operator with ID {update_data.operator_ids[0]} not found"
            )
        
        # Validate estimated hours
        if update_data.estimated_hours <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimated hours must be greater than 0"
            )
        
        # Remove timezone from scheduled_start if present
        scheduled_start = update_data.scheduled_start
        if scheduled_start.tzinfo is not None:
            scheduled_start = scheduled_start.replace(tzinfo=None)
        
        # Update plan fields
        plan.workstation_id = update_data.workstation_id
        plan.user_id = update_data.operator_ids[0]
        plan.estimated_hours = update_data.estimated_hours
        plan.scheduled_start_date = scheduled_start
        plan.cut_type = update_data.cut_type.lower()
        plan.updated_at = datetime.now()
        plan.updated_by = current_user.id
        
        await db.commit()
        await db.refresh(plan)
        
        return {
            "success": True,
            "message": "Shop plan updated successfully",
            "data": {
                "id": plan.id,
                "fab_id": plan.fab_id,
                "cut_type": plan.cut_type,
                "workstation_id": plan.workstation_id,
                "operator_id": plan.user_id,
                "estimated_hours": plan.estimated_hours,
                "scheduled_start_date": plan.scheduled_start_date.isoformat(),
                "work_percentage": plan.work_percentage,
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