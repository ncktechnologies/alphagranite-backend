from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.app.database.user import User
from src.app.database.fab_type import FabType
from src.app.interface.business_schemas import FabTypeResponse, FabTypeCreate
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse, success_response
from src.app.database import get_db

router = APIRouter()


@router.get("/fab-types", response_model=List[FabTypeResponse])
async def get_fab_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available fabrication types"""
    result = await db.execute(select(FabType))
    fab_types = result.scalars().all()
    return fab_types


@router.post("/fab-types", response_model=SuccessResponse[FabTypeResponse], status_code=201)
async def create_fab_type(
    fab_type_data: FabTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new fabrication type"""
    # Check if name already exists (case-insensitive)
    result = await db.execute(
        select(FabType).where(FabType.name.ilike(fab_type_data.name))
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Fab type '{fab_type_data.name}' already exists"
        )

    new_fab_type = FabType(
        name=fab_type_data.name,
        description=fab_type_data.description
    )

    db.add(new_fab_type)
    await db.commit()
    await db.refresh(new_fab_type)

    return success_response(new_fab_type, "Fab type created successfully")