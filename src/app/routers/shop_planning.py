from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from fastapi import APIRouter, Depends, Form
from src.app.interface.generated_schemas import ShopPlanning
from src.app.utils.helpers import success_response, error_response

router = APIRouter()

@router.post("/shop-planning")
def create_shop_planning(
    job_id: int = Form(...),
    fab_ids: str = Form(...),  # comma-separated FABIDs
    planning_section_ids: str = Form(...),  # comma-separated planning section IDs in order
    start_datetime: str = Form(...),
    db: Session = Depends(get_db),
    created_by: int = 1
):
    shop_plan = ShopPlanning(
        job_id=job_id,
        fab_ids=fab_ids,
        planning_section_ids=planning_section_ids,
        start_datetime=start_datetime,
        created_by=created_by
    )
    db.add(shop_plan)
    db.commit()
    db.refresh(shop_plan)
    return success_response(shop_plan, "Shop planning created successfully")

@router.put("/shop-planning/{shop_plan_id}")
def update_shop_planning(
    shop_plan_id: int,
    job_id: int = Form(...),
    fab_ids: str = Form(...),
    planning_section_ids: str = Form(...),
    start_datetime: str = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    shop_plan = db.get(ShopPlanning, shop_plan_id)
    if not shop_plan:
        raise error_response("Shop planning not found", 404)
    shop_plan.job_id = job_id
    shop_plan.fab_ids = fab_ids
    shop_plan.planning_section_ids = planning_section_ids
    shop_plan.start_datetime = start_datetime
    shop_plan.updated_by = updated_by
    shop_plan.updated_at = datetime.now()
    db.commit()
    db.refresh(shop_plan)
    return success_response(shop_plan, "Shop planning updated successfully")

@router.delete("/shop-planning/{shop_plan_id}")
def delete_shop_planning(shop_plan_id: int, db: Session = Depends(get_db)):
    shop_plan = db.get(ShopPlanning, shop_plan_id)
    if not shop_plan:
        raise error_response("Shop planning not found", 404)
    db.delete(shop_plan)
    db.commit()
    return success_response(None, "Shop planning deleted successfully")

@router.get("/shop-planning/{shop_plan_id}")
def get_shop_planning(shop_plan_id: int, db: Session = Depends(get_db)):
    shop_plan = db.get(ShopPlanning, shop_plan_id)
    if not shop_plan:
        raise error_response("Shop planning not found", 404)
    return success_response(shop_plan, "Shop planning retrieved successfully")

@router.get("/shop-planning")
async def list_shop_planning(
    job_id: Optional[int] = None,
    fab_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = select(ShopPlanning)
    if job_id:
        query = query.where(ShopPlanning.job_id == job_id)
    if fab_id:
        query = query.where(ShopPlanning.fab_ids.contains(str(fab_id)))
    if search:
        query = query.where(ShopPlanning.planning_section_ids.ilike(f"%{search}%"))
    plans = (await db.execute(query)).scalars().all()
    return success_response(plans, "Shop planning list retrieved successfully")
