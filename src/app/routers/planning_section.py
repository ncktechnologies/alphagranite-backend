from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.interface.generated_schemas import PlanningSection as PlanningSectionSchema
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response, error_response
from src.app.database.work_station import WorkStation
from src.app.middleware.jwt_auth import get_current_user
from src.app.database.user import User

router = APIRouter()


class PlanningSectionCreateRequest(BaseModel):
    plan_name: str
    plan_description: Optional[str] = None
    is_active: bool = True
    status_id: int = 1


class PlanningSectionUpdateRequest(BaseModel):
    plan_name: str
    plan_description: Optional[str] = None
    is_active: Optional[bool] = None
    status_id: int


@router.post("/planning-section", response_model=SuccessResponse[PlanningSectionSchema])  # required
async def create_planning_section(
    payload: PlanningSectionCreateRequest,
    db: AsyncSession = Depends(get_db),
    created_by: int = 1,
):
    if payload.status_id not in (0, 1):
        raise error_response("status_id must be 0 (inactive) or 1 (active)", 400)

    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.plan_name == payload.plan_name)
    )
    if result.scalar_one_or_none():
        raise error_response("Plan name must be unique", 400)

    section = PlanningSectionSchema(
        plan_name=payload.plan_name,
        plan_description=payload.plan_description,
        is_active=payload.is_active,
        status_id=payload.status_id,
        created_by=created_by,
        created_at=datetime.now(),
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return success_response(section, "Planning section created successfully")


@router.put("/planning-section/{section_id}", response_model=SuccessResponse[PlanningSectionSchema])  # required
async def update_planning_section(
    section_id: int,
    payload: PlanningSectionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    updated_by: int = 1,
):
    if payload.status_id not in (0, 1):
        raise error_response("status_id must be 0 (inactive) or 1 (active)", 400)

    section = await db.get(PlanningSectionSchema, section_id)
    if not section:
        raise error_response("Planning section not found", 404)

    result = await db.execute(
        select(PlanningSectionSchema).where(
            PlanningSectionSchema.plan_name == payload.plan_name,
            PlanningSectionSchema.id != section_id,
        )
    )
    if result.scalar_one_or_none():
        raise error_response("Plan name must be unique", 400)

    section.plan_name = payload.plan_name
    section.plan_description = payload.plan_description
    if payload.is_active is not None:
        section.is_active = payload.is_active
    section.status_id = payload.status_id
    section.updated_by = updated_by
    section.updated_at = datetime.now()

    await db.commit()
    await db.refresh(section)
    return success_response(section, "Planning section updated successfully")


@router.get("/planning-section/by-name", response_model=SuccessResponse[PlanningSectionSchema])  # required
async def get_planning_section_by_name(
    plan_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.plan_name == plan_name)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise error_response("Planning section not found", 404)
    return success_response(section, "Planning section retrieved successfully")


@router.get("/planning-section/by-name/{planning_section_name}", response_model=SuccessResponse[PlanningSectionSchema])
async def get_planning_section_by_name_path(
    planning_section_name: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.plan_name == planning_section_name)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise error_response("Planning section not found", 404)
    return success_response(section, "Planning section retrieved successfully")


@router.get("/planning-section/active", response_model=SuccessResponse[List[PlanningSectionSchema]])  # required
async def get_active_planning_sections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.is_active.is_(True))
    )
    sections = result.scalars().all()
    return success_response(sections, "Active planning sections retrieved successfully")


@router.get("/planning-section", response_model=SuccessResponse[List[PlanningSectionSchema]])
async def get_all_planning_sections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanningSectionSchema))
    sections = result.scalars().all()
    return success_response(sections, "Planning sections retrieved successfully")


@router.get(
    "/planning-section/{planning_section_id}/workstations",
    response_model=SuccessResponse[dict],
)
async def get_workstations_by_planning_section(
    planning_section_id: int,
    status_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = await db.get(PlanningSectionSchema, planning_section_id)
    if not section:
        raise error_response("Planning section not found", 404)

    query = select(WorkStation).where(WorkStation.planning_section_id == planning_section_id)

    if status_id is not None:
        query = query.where(WorkStation.status_id == status_id)

    result = await db.execute(query.order_by(WorkStation.name))
    workstations = result.scalars().all()

    return success_response(
        {
            "planning_section_id": planning_section_id,
            "plan_name": section.plan_name,
            "is_active": section.is_active,
            "total": len(workstations),
            "workstations": [
                {
                    "id": ws.id,
                    "name": ws.name,
                    "status_id": ws.status_id,
                    "operator_ids": ws.operator_ids,
                    "created_at": ws.created_at.isoformat(),
                    "created_by": ws.created_by,
                    "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
                    "updated_by": ws.updated_by,
                }
                for ws in workstations
            ]
        },
        "Workstations retrieved successfully",
    )
