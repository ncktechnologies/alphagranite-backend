from datetime import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.interface.generated_schemas import CostOfStone
from src.app.database.status import Status
from src.app.interface.business_schemas import (
    CostOfStoneCreate,
    CostOfStoneUpdate,
    CostOfStoneResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/cost-of-stone", response_model=SuccessResponse[CostOfStoneResponse], status_code=201)
async def create_cost_of_stone(
    cost_data: CostOfStoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create cost of stone calculation for a fab"""
    
    # Check if fab exists
    fab_result = await db.execute(select(Fab).where(Fab.id == cost_data.fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)
    
    # Check if already exists for this fab
    existing = await db.execute(
        select(CostOfStone).where(CostOfStone.fab_id == cost_data.fab_id)
    )
    if existing.scalar_one_or_none():
        raise error_response("Cost of Stone already exists for this fab", 400)
    
    # Create cost of stone
    cost_of_stone = CostOfStone(
        fab_id=cost_data.fab_id,
        stone_color_id=cost_data.stone_color_id,
        stone_type_id=cost_data.stone_type_id,
        total_sqft=cost_data.total_sqft,
        cost_per_sqft=cost_data.cost_per_sqft,
        waste_percentage=cost_data.waste_percentage,
        status_id=1,
        created_at=datetime.now()
    )
    
    # Update fab stage
    fab.current_stage = "cost_of_stones"
    fab.updated_at = datetime.now()
    fab.updated_by = current_user.id
    
    db.add(cost_of_stone)
    await db.commit()
    await db.refresh(cost_of_stone)
    
    return success_response(
        CostOfStoneResponse(
            id=cost_of_stone.id,
            fab_id=cost_of_stone.fab_id,
            stone_color_id=cost_of_stone.stone_color_id,
            stone_type_id=cost_of_stone.stone_type_id,
            total_sqft=cost_of_stone.total_sqft,
            cost_per_sqft=cost_of_stone.cost_per_sqft,
            total_cost=cost_of_stone.total_cost,
            waste_percentage=cost_of_stone.waste_percentage,
            calculated_by=cost_of_stone.calculated_by,
            is_completed=cost_of_stone.is_completed,
            status_id=cost_of_stone.status_id,
            created_at=cost_of_stone.created_at,
            updated_at=cost_of_stone.updated_at,
            updated_by=cost_of_stone.updated_by
        ),
        "Cost of Stone created successfully"
    )


@router.put("/cost-of-stone/{cost_id}", response_model=SuccessResponse[CostOfStoneResponse])
async def update_cost_of_stone(
    cost_id: int,
    update_data: CostOfStoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update cost of stone"""
    
    result = await db.execute(select(CostOfStone).where(CostOfStone.id == cost_id))
    cost_of_stone = result.scalar_one_or_none()
    
    if not cost_of_stone:
        raise error_response("Cost of Stone not found", 404)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(cost_of_stone, key, value)
    
    cost_of_stone.updated_at = datetime.now()
    cost_of_stone.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(cost_of_stone)
    
    return success_response(
        CostOfStoneResponse(
            id=cost_of_stone.id,
            fab_id=cost_of_stone.fab_id,
            stone_color_id=cost_of_stone.stone_color_id,
            stone_type_id=cost_of_stone.stone_type_id,
            total_sqft=cost_of_stone.total_sqft,
            cost_per_sqft=cost_of_stone.cost_per_sqft,
            total_cost=cost_of_stone.total_cost,
            waste_percentage=cost_of_stone.waste_percentage,
            calculated_by=cost_of_stone.calculated_by,
            is_completed=cost_of_stone.is_completed,
            status_id=cost_of_stone.status_id,
            created_at=cost_of_stone.created_at,
            updated_at=cost_of_stone.updated_at,
            updated_by=cost_of_stone.updated_by
        ),
        "Cost of Stone updated successfully"
    )


@router.get("/cost-of-stone/fab/{fab_id}", response_model=SuccessResponse[CostOfStoneResponse])
async def get_cost_of_stone_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cost of stone by fab ID"""
    
    result = await db.execute(select(CostOfStone).where(CostOfStone.fab_id == fab_id))
    cost_of_stone = result.scalar_one_or_none()
    
    if not cost_of_stone:
        raise error_response("Cost of Stone not found for this fab", 404)
    
    return success_response(
        CostOfStoneResponse(
            id=cost_of_stone.id,
            fab_id=cost_of_stone.fab_id,
            stone_color_id=cost_of_stone.stone_color_id,
            stone_type_id=cost_of_stone.stone_type_id,
            total_sqft=cost_of_stone.total_sqft,
            cost_per_sqft=cost_of_stone.cost_per_sqft,
            total_cost=cost_of_stone.total_cost,
            waste_percentage=cost_of_stone.waste_percentage,
            calculated_by=cost_of_stone.calculated_by,
            is_completed=cost_of_stone.is_completed,
            status_id=cost_of_stone.status_id,
            created_at=cost_of_stone.created_at,
            updated_at=cost_of_stone.updated_at,
            updated_by=cost_of_stone.updated_by
        ),
        "Cost of Stone retrieved successfully"
    )
