from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from src.app.utils.helpers import success_response, error_response
from src.app.interface.generated_schemas import ShopPlanningSection
from fastapi import APIRouter, Depends, Form, UploadFile, File as FastAPIFile, UploadFile, File as FastAPIFile

router = APIRouter()

@router.post("/shop-planning-section")
def create_shop_planning_section(
    planning_section_id: int = Form(...),
    workstation_ids: str = Form(...),  # comma-separated, ordered
    total_sqft: float = Form(...),
    machine_ids: Optional[str] = Form(None),  # comma-separated, ordered to match workstations
    operator_ids: str = Form(...),  # comma-separated, ordered to match workstations, can be multiple per ws
    note: Optional[str] = Form(None),
    scheduled_hours: str = Form(...),  # comma-separated, ordered to match workstations
    fab_id: Optional[int] = Form(None),
    scheduled_start_date: Optional[datetime] = Form(None),
    files: Optional[List[UploadFile]] = None,
    db: Session = Depends(get_db),
    created_by: int = 1
):
    file_ids = []
    if files:
        file_ids = [f"file_{i+1}" for i, _ in enumerate(files)]
    section = ShopPlanningSection(
        planning_section_id=planning_section_id,
        workstation_ids=workstation_ids,
        total_sqft=total_sqft,
        machine_ids=machine_ids,
        operator_ids=operator_ids,
        note=note,
        scheduled_hours=scheduled_hours,
        file_ids=','.join(file_ids),
        fab_id=fab_id,
        scheduled_start_date=scheduled_start_date,
        created_by=created_by
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return success_response(section, "Shop planning section created successfully")


@router.put("/shop-planning-section/{section_id}")
def update_shop_planning_section(
    section_id: int,
    planning_section_id: int = Form(...),
    workstation_ids: str = Form(...),
    total_sqft: float = Form(...),
    machine_ids: str = Form(...),
    operator_ids: str = Form(...),
    note: Optional[str] = Form(None),
    scheduled_hours: str = Form(...),
    files: Optional[List[UploadFile]] = None,
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    section = db.get(ShopPlanningSection, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    file_ids = section.file_ids.split(',') if section.file_ids else []
    if files:
        new_file_ids = [f"file_{i+len(file_ids)+1}" for i, _ in enumerate(files)]
        file_ids.extend(new_file_ids)
    section.planning_section_id = planning_section_id
    section.workstation_ids = workstation_ids
    section.total_sqft = total_sqft
    section.machine_ids = machine_ids
    section.operator_ids = operator_ids
    section.note = note
    section.scheduled_hours = scheduled_hours
    section.file_ids = ','.join(file_ids)
    section.updated_by = updated_by
    section.updated_at = datetime.now()
    db.commit()
    db.refresh(section)
    return success_response(section, "Shop planning section updated successfully")

@router.delete("/shop-planning-section/{section_id}")
def delete_shop_planning_section(section_id: int, db: Session = Depends(get_db)):
    section = db.get(ShopPlanningSection, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    db.delete(section)
    db.commit()
    return success_response(None, "Shop planning section deleted successfully")

@router.get("/shop-planning-section/{section_id}")
def get_shop_planning_section(section_id: int, db: Session = Depends(get_db)):
    section = db.get(ShopPlanningSection, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    return success_response(section, "Shop planning section retrieved successfully")

@router.get("/shop-planning-section")
def list_shop_planning_sections(
    planning_section_id: Optional[int] = None,
    workstation_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    fab_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = select(ShopPlanningSection)
    if planning_section_id:
        query = query.where(ShopPlanningSection.planning_section_id == planning_section_id)
    if workstation_id:
        query = query.where(ShopPlanningSection.workstation_ids.contains(str(workstation_id)))
    if operator_id:
        query = query.where(ShopPlanningSection.operator_ids.contains(str(operator_id)))
    if fab_id:
        query = query.where(ShopPlanningSection.fab_id == fab_id)
    sections = db.exec(query).all()
    return success_response(sections, "Shop planning section list retrieved successfully")