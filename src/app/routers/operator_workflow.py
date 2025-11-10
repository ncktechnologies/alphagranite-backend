from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from fastapi import APIRouter, Depends, Form
from src.app.interface.generated_schemas import OperationWorkflow, ShopPlanningSection
from src.app.utils.helpers import success_response, error_response

router = APIRouter()

@router.post("/operator-workflow")
def create_operator_workflow(
    shop_planning_sections: int = Form(...),
    started_at: str = Form(...),
    finished_at: str = Form(...),
    total_sqft_done: str = Form(...),
    reason_for_pause: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    workflow = OperationWorkflow(
        shop_planning_sections=shop_planning_sections,
        started_at=datetime.fromisoformat(started_at),
        finished_at=datetime.fromisoformat(finished_at),
        total_sqft_done=total_sqft_done,
        reason_for_pause=reason_for_pause,
        notes=notes,
        created_at=datetime.now(),
        updated_by=updated_by
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return success_response(workflow, "Operator workflow created successfully")

@router.put("/operator-workflow/{workflow_id}")
def update_operator_workflow(
    workflow_id: int,
    shop_planning_sections: int = Form(...),
    started_at: str = Form(...),
    finished_at: str = Form(...),
    total_sqft_done: str = Form(...),
    reason_for_pause: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    workflow = db.get(OperationWorkflow, workflow_id)
    if not workflow:
        raise error_response("Operator workflow not found", 404)
    workflow.shop_planning_sections = shop_planning_sections
    workflow.started_at = datetime.fromisoformat(started_at)
    workflow.finished_at = datetime.fromisoformat(finished_at)
    workflow.total_sqft_done = total_sqft_done
    workflow.reason_for_pause = reason_for_pause
    workflow.notes = notes
    workflow.updated_by = updated_by
    workflow.updated_at = datetime.now()
    db.commit()
    db.refresh(workflow)
    return success_response(workflow, "Operator workflow updated successfully")

@router.delete("/operator-workflow/{workflow_id}")
def delete_operator_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(OperationWorkflow, workflow_id)
    if not workflow:
        raise error_response("Operator workflow not found", 404)
    db.delete(workflow)
    db.commit()
    return success_response(None, "Operator workflow deleted successfully")

@router.get("/operator-workflow/{workflow_id}")
def get_operator_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(OperationWorkflow, workflow_id)
    if not workflow:
        raise error_response("Operator workflow not found", 404)
    return success_response(workflow, "Operator workflow retrieved successfully")

@router.get("/operator-workflow")
def list_operator_workflows(
    shop_planning_sections: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = select(OperationWorkflow)
    if shop_planning_sections:
        query = query.where(OperationWorkflow.shop_planning_sections == shop_planning_sections)
    workflows = db.exec(query).all()
    return success_response(workflows, "Operator workflows retrieved successfully")
