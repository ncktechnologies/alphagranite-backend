from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from src.app.utils.helpers import success_response, error_response
from src.app.database.shop_planning_section import ShopPlanningSection as ShopPlanningSectionModel
from src.app.interface.generated_schemas import ShopPlanningSection as ShopPlanningSectionSchema
from fastapi import APIRouter, Depends, Form, UploadFile

router = APIRouter()

@router.post("/shop-planning-section")
def create_shop_planning_section(
    work_station_id: int = Form(...),
    operator_ids: Optional[str] = Form(None),
    machine: Optional[str] = Form(None),
    scheduled_sqft: Optional[str] = Form(None),
    completed_sqft: Optional[str] = Form(None),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    status_id: int = Form(...),
    db: Session = Depends(get_db),
    created_by: int = 1
):
    section = ShopPlanningSectionModel(
        work_station_id=work_station_id,
        operator_ids=operator_ids,
        machine=machine,
        scheduled_sqft=scheduled_sqft,
        completed_sqft=completed_sqft,
        start_date=start_date,
        end_date=end_date,
        status_id=status_id,
        created_at=datetime.now(),
        updated_by=created_by
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return success_response(section, "Shop planning section created successfully")

@router.put("/shop-planning-section/{section_id}")
def update_shop_planning_section(
    section_id: int,
    work_station_id: int = Form(...),
    operator_ids: Optional[str] = Form(None),
    machine: Optional[str] = Form(None),
    scheduled_sqft: Optional[str] = Form(None),
    completed_sqft: Optional[str] = Form(None),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    status_id: int = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    section = db.get(ShopPlanningSectionModel, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    
    section.work_station_id = work_station_id
    section.operator_ids = operator_ids
    section.machine = machine
    section.scheduled_sqft = scheduled_sqft
    section.completed_sqft = completed_sqft
    section.start_date = start_date
    section.end_date = end_date
    section.status_id = status_id
    section.updated_by = updated_by
    section.updated_at = datetime.now()
    
    db.commit()
    db.refresh(section)
    return success_response(section, "Shop planning section updated successfully")

@router.delete("/shop-planning-section/{section_id}")
def delete_shop_planning_section(section_id: int, db: Session = Depends(get_db)):
    section = db.get(ShopPlanningSectionModel, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    db.delete(section)
    db.commit()
    return success_response(None, "Shop planning section deleted successfully")

@router.get("/shop-planning-section/{section_id}")
def get_shop_planning_section(section_id: int, db: Session = Depends(get_db)):
    section = db.get(ShopPlanningSectionModel, section_id)
    if not section:
        raise error_response("Shop planning section not found", 404)
    return success_response(section, "Shop planning section retrieved successfully")

@router.get("/shop-planning-section")
def list_shop_planning_sections(
    work_station_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    status_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = select(ShopPlanningSectionModel)
    if work_station_id:
        query = query.where(ShopPlanningSectionModel.work_station_id == work_station_id)
    if operator_id:
        query = query.where(ShopPlanningSectionModel.operator_ids.contains(str(operator_id)))
    if status_id:
        query = query.where(ShopPlanningSectionModel.status_id == status_id)
    sections = db.exec(query).all()
    return success_response(sections, "Shop planning section list retrieved successfully")