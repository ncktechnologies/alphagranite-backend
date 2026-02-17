from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.interface.generated_schemas import PlanningSection as PlanningSectionSchema
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response, error_response

router = APIRouter()

@router.post("/planning-section", response_model=SuccessResponse[PlanningSectionSchema])
async def create_planning_section(
    name: str = Form(...),
    description: str = Form(...),
    status_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    created_by: int = 1
):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.name == name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise error_response("Plan name must be unique", 400)

    section = PlanningSectionSchema(
        name=name,
        description=description,
        status_id=status_id,
        created_by=created_by,
        created_at=datetime.now()
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return success_response(section, "Planning section created successfully")

@router.put("/planning-section/{section_id}", response_model=SuccessResponse[PlanningSectionSchema])
async def update_planning_section(
    section_id: int,
    name: str = Form(...),
    description: str = Form(...),
    status_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    updated_by: int = 1
):
    section = await db.get(PlanningSectionSchema, section_id)
    if not section:
        raise error_response("Planning section not found", 404)

    result = await db.execute(
        select(PlanningSectionSchema).where(
            PlanningSectionSchema.name == name,
            PlanningSectionSchema.id != section_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise error_response("Plan name must be unique", 400)

    section.name = name
    section.description = description
    section.status_id = status_id
    section.updated_by = updated_by
    section.updated_at = datetime.now()

    await db.commit()
    await db.refresh(section)
    return success_response(section, "Planning section updated successfully")

@router.get("/planning-section/by-name/{name}", response_model=SuccessResponse[PlanningSectionSchema])
async def get_planning_section_by_name(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.name == name)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise error_response("Planning section not found", 404)
    return success_response(section, "Planning section retrieved successfully")

@router.get("/planning-section/active", response_model=SuccessResponse[List[PlanningSectionSchema]])
async def get_active_planning_sections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlanningSectionSchema).where(PlanningSectionSchema.status_id == 1)
    )
    sections = result.scalars().all()
    return success_response(sections, "Active planning sections retrieved successfully")
