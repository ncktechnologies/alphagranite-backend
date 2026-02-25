from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Form
from src.app.database import get_db
from src.app.database.work_station import WorkStation
from src.app.database.user import User
from src.app.database.status import Status
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response, error_response
from src.app.middleware.jwt_auth import get_current_user
from sqlalchemy import func

router = APIRouter(
    prefix="/workstation",
    tags=["Workstation"]
)


@router.post("", response_model=SuccessResponse[dict])
async def create_workstation(
    name: str = Form(...),
    status_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workstation"""
    
    # Check if workstation name is unique
    result = await db.execute(select(WorkStation).where(WorkStation.name == name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workstation name must be unique"
        )
    
    # Verify status exists
    status_result = await db.execute(select(Status).where(Status.value_id == status_id))
    status_obj = status_result.scalar_one_or_none()
    
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status ID"
        )
    
    ws = WorkStation(
        name=name,
        status_id=status_id,
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    
    return success_response({
        "id": ws.id,
        "name": ws.name,
        "status_id": ws.status_id,
        "created_at": ws.created_at.isoformat(),
        "created_by": ws.created_by
    }, "Workstation created successfully")


@router.put("/{ws_id}", response_model=SuccessResponse[dict])
async def update_workstation(
    ws_id: int,
    name: Optional[str] = Form(None),
    status_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a workstation"""
    
    result = await db.execute(select(WorkStation).where(WorkStation.id == ws_id))
    ws = result.scalar_one_or_none()
    
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workstation not found"
        )
    
    # Check if new name is unique (if changing name)
    if name and name != ws.name:
        existing = await db.execute(select(WorkStation).where(WorkStation.name == name))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workstation name must be unique"
            )
        ws.name = name
    
    if status_id:
        # Verify status exists
        status_result = await db.execute(select(Status).where(Status.value_id == status_id))
        if not status_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status ID"
            )
        ws.status_id = status_id
    
    ws.updated_at = datetime.now()
    ws.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(ws)
    
    return success_response({
        "id": ws.id,
        "name": ws.name,
        "status_id": ws.status_id,
        "created_at": ws.created_at.isoformat(),
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "updated_by": ws.updated_by
    }, "Workstation updated successfully")


@router.delete("/{ws_id}", response_model=SuccessResponse[dict])
async def delete_workstation(
    ws_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a workstation (soft delete)"""
    
    result = await db.execute(select(WorkStation).where(WorkStation.id == ws_id))
    ws = result.scalar_one_or_none()
    
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workstation not found"
        )
    
    ws.status_id = 0
    ws.updated_at = datetime.now()
    ws.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(ws)
    
    return success_response(
        {
            "id": ws.id,
            "name": ws.name,
            "status_id": ws.status_id,
            "updated_at": ws.updated_at.isoformat(),
            "updated_by": ws.updated_by
        },
        "Workstation deactivated successfully"
    )


@router.get("/by-name/{workstation_name}", response_model=SuccessResponse[dict])
async def get_workstation_by_name(
    workstation_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workstation by name"""
    
    result = await db.execute(select(WorkStation).where(WorkStation.name == workstation_name))
    ws = result.scalar_one_or_none()
    
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workstation not found"
        )
    
    return success_response({
        "id": ws.id,
        "name": ws.name,
        "status_id": ws.status_id,
        "created_at": ws.created_at.isoformat(),
        "created_by": ws.created_by
    }, "Workstation retrieved successfully")


@router.get("", response_model=SuccessResponse[dict])
async def get_all_workstations(
    status_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all workstations with optional filters"""
    
    query = select(WorkStation)
    
    if status_id:
        query = query.where(WorkStation.status_id == status_id)
    
    if search:
        query = query.where(WorkStation.name.ilike(f"%{search}%"))
    
    # Get total count
    count_result = await db.execute(select(func.count(WorkStation.id)))
    total = count_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(WorkStation.name)
    
    result = await db.execute(query)
    workstations = result.scalars().all()
    
    return success_response({
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "per_page": limit,
        "data": [
            {
                "id": ws.id,
                "name": ws.name,
                "status_id": ws.status_id,
                "created_at": ws.created_at.isoformat(),
                "created_by": ws.created_by,
                "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
                "updated_by": ws.updated_by
            }
            for ws in workstations
        ]
    }, "Workstations retrieved successfully")


@router.get("/{ws_id}", response_model=SuccessResponse[dict])
async def get_workstation(
    ws_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific workstation by ID"""
    
    result = await db.execute(select(WorkStation).where(WorkStation.id == ws_id))
    ws = result.scalar_one_or_none()
    
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workstation not found"
        )
    
    return success_response({
        "id": ws.id,
        "name": ws.name,
        "status_id": ws.status_id,
        "created_at": ws.created_at.isoformat(),
        "created_by": ws.created_by,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "updated_by": ws.updated_by
    }, "Workstation retrieved successfully")
