from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from fastapi import APIRouter, Depends, HTTPException, Form
from src.app.interface.generated_schemas import WorkStation
from src.app.utils.helpers import success_response, error_response

router = APIRouter()

@router.post("/workstation", response_model=WorkStation)
def create_workstation(
    planning_section_id: int = Form(...),
    workstation_name: str = Form(...),
    status: str = Form(...),
    assigned_operatives: str = Form(...),
    machines: str = Form(...),
    machine_statuses: str = Form(...),
    db: Session = Depends(get_db),
    created_by: int = 1
):
    existing = db.exec(select(WorkStation).where(WorkStation.workstation_name == workstation_name)).first()
    if existing:
        raise error_response("Workstation name must be unique", 400)
    ws = WorkStation(
        planning_section_id=planning_section_id,
        workstation_name=workstation_name,
        status=status,
        assigned_operatives=assigned_operatives,
        machines=machines,
        machine_statuses=machine_statuses,
        created_by=created_by
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return success_response(ws, "Workstation created successfully")

@router.put("/workstation/{ws_id}", response_model=WorkStation)
def update_workstation(
    ws_id: int,
    planning_section_id: int = Form(...),
    workstation_name: str = Form(...),
    status: str = Form(...),
    assigned_operatives: str = Form(...),
    machines: str = Form(...),
    machine_statuses: str = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    ws = db.get(WorkStation, ws_id)
    if not ws:
        raise error_response("Workstation not found", 404)
    existing = db.exec(select(WorkStation).where(WorkStation.workstation_name == workstation_name, WorkStation.id != ws_id)).first()
    if existing:
        raise error_response("Workstation name must be unique", 400)
    ws.planning_section_id = planning_section_id
    ws.workstation_name = workstation_name
    ws.status = status
    ws.assigned_operatives = assigned_operatives
    ws.machines = machines
    ws.machine_statuses = machine_statuses
    ws.updated_by = updated_by
    ws.updated_at = datetime.now()
    db.commit()
    db.refresh(ws)
    return success_response(ws, "Workstation updated successfully")

@router.delete("/workstation/{ws_id}")
def delete_workstation(ws_id: int, db: Session = Depends(get_db)):
    ws = db.get(WorkStation, ws_id)
    if not ws:
        raise error_response("Workstation not found", 404)
    db.delete(ws)
    db.commit()
    return success_response(None, "Workstation deleted successfully")

@router.get("/workstation/by-name/{workstation_name}", response_model=WorkStation)
def get_workstation_by_name(workstation_name: str, db: Session = Depends(get_db)):
    ws = db.exec(select(WorkStation).where(WorkStation.workstation_name == workstation_name)).first()
    if not ws:
        raise error_response("Workstation not found", 404)
    return success_response(ws, "Workstation retrieved successfully")

@router.get("/workstation/active", response_model=List[WorkStation])
def get_active_workstations(
    planning_section_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = select(WorkStation).where(WorkStation.status == "active")
    if planning_section_id:
        query = query.where(WorkStation.planning_section_id == planning_section_id)
    if search:
        query = query.where(WorkStation.workstation_name.ilike(f"%{search}%"))
    workstations = db.exec(query).all()
    return success_response(workstations, "Active workstations retrieved successfully")
