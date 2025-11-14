from typing import List
from datetime import datetime
from sqlmodel import Session, select
from src.app.utils.config import get_db
from fastapi import APIRouter, Depends, HTTPException, Form
from src.app.interface.generated_schemas import PlanningSection
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response, error_response

router = APIRouter()

@router.post("/planning-section", response_model=SuccessResponse[PlanningSection])
def create_planning_section(
    plan_name: str = Form(...),
    plan_description: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
    created_by: int = 1
):
    existing = db.exec(select(PlanningSection).where(PlanningSection.plan_name == plan_name)).first()
    if existing:
        raise error_response("Plan name must be unique", 400)
    section = PlanningSection(plan_name=plan_name, plan_description=plan_description, status=status, created_by=created_by)
    db.add(section)
    db.commit()
    db.refresh(section)
    return success_response(section, "Planning section created successfully")

@router.put("/planning-section/{section_id}", response_model=SuccessResponse[PlanningSection])
def update_planning_section(
    section_id: int,
    plan_name: str = Form(...),
    plan_description: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    section = db.get(PlanningSection, section_id)
    if not section:
        raise error_response("Planning section not found", 404)
    existing = db.exec(select(PlanningSection).where(PlanningSection.plan_name == plan_name, PlanningSection.id != section_id)).first()
    if existing:
        raise error_response("Plan name must be unique", 400)
    section.plan_name = plan_name
    section.plan_description = plan_description
    section.status = status
    section.updated_by = updated_by
    section.updated_at = datetime.now()
    db.commit()
    db.refresh(section)
    return success_response(section, "Planning section updated successfully")

@router.delete("/planning-section/{section_id}")
def delete_planning_section(section_id: int, db: Session = Depends(get_db)):
    section = db.get(PlanningSection, section_id)
    if not section:
        raise error_response("Planning section not found", 404)
    db.delete(section)
    db.commit()
    return success_response(None, "Planning section deleted successfully")

@router.get("/planning-section/by-name/{plan_name}", response_model=SuccessResponse[PlanningSection])
def get_planning_section_by_name(plan_name: str, db: Session = Depends(get_db)):
    section = db.exec(select(PlanningSection).where(PlanningSection.plan_name == plan_name)).first()
    if not section:
        raise error_response("Planning section not found", 404)
    return success_response(section, "Planning section retrieved successfully")

@router.get("/planning-section/active", response_model=SuccessResponse[List[PlanningSection]])
def get_active_planning_sections(db: Session = Depends(get_db)):
    sections = db.exec(select(PlanningSection).where(PlanningSection.status == "active")).all()
    return success_response(sections, "Active planning sections retrieved successfully")
