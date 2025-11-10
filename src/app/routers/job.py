from typing import List
from sqlmodel import Session
from src.app.utils.config import get_db
from src.app.service.job import JobService
from fastapi import APIRouter, Depends, HTTPException
from src.app.service.property_service import PropertyService
from src.app.utils.helpers import success_response, error_response, call_service
from src.app.database import job as job_models, account as account_models, fab as fab_models, stone_type as stone_type_models, edge as edge_models, stone_thickness as stone_thickness_models, stone_colour as stone_colour_models

router = APIRouter()

# --- Job APIs ---
@router.post("/jobs")
async def create_job(job_name: str, job_number: int, account_id: int, db: Session = Depends(get_db)):
    service = JobService(db)
    job = await call_service(
        service.create_job,
        {"name": job_name, "job_id": job_number, "account_id": account_id},
        created_by=1  # Replace with actual user id
    )
    return success_response(
        data=job,
        message="Job created successfully"
    )

# --- Account APIs ---
@router.get("/accounts")
async def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(account_models.Account).all()
    return success_response(
        data=accounts,
        message="Accounts retrieved successfully"
    )

# --- Stone Thickness APIs ---
@router.get("/stone-thickness")
async def get_stone_thickness(db: Session = Depends(get_db)):
    items = db.query(stone_thickness_models.StoneThickness).all()
    return success_response(
        data=items,
        message="Stone thickness options retrieved successfully"
    )

@router.put("/stone-thickness/{item_id}")
async def update_stone_thickness(item_id: int, name: str, order: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_thickness_models.StoneThickness)
    result = await call_service(
        service.update_item,
        item_id,
        new_name=name,
        new_order=order
    )
    return success_response(
        data=result,
        message="Stone thickness updated successfully"
    )

@router.delete("/stone-thickness/{item_id}")
async def delete_stone_thickness(item_id: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_thickness_models.StoneThickness)
    await call_service(service.delete_item, item_id)
    return success_response(
        data=None,
        message="Stone thickness deleted successfully"
    )

# --- Stone Colour APIs ---
@router.get("/stone-colour")
async def get_stone_colour(db: Session = Depends(get_db)):
    items = db.query(stone_colour_models.StoneColour).all()
    return success_response(
        data=items,
        message="Stone colour options retrieved successfully"
    )

@router.put("/stone-colour/{item_id}")
async def update_stone_colour(item_id: int, name: str, order: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_colour_models.StoneColour)
    result = await call_service(
        service.update_item,
        item_id,
        new_name=name,
        new_order=order
    )
    return success_response(
        data=result,
        message="Stone colour updated successfully"
    )

@router.delete("/stone-colour/{item_id}")
async def delete_stone_colour(item_id: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_colour_models.StoneColour)
    await call_service(service.delete_item, item_id)
    return success_response(
        data=None,
        message="Stone colour deleted successfully"
    )

# --- Edge APIs ---
@router.get("/edges")
async def get_edges(db: Session = Depends(get_db)):
    items = db.query(edge_models.Edge).all()
    return success_response(
        data=items,
        message="Edge options retrieved successfully"
    )

@router.put("/edges/{item_id}")
async def update_edge(item_id: int, name: str, order: int, db: Session = Depends(get_db)):
    service = PropertyService(db, edge_models.Edge)
    result = await call_service(
        service.update_item,
        item_id,
        new_name=name,
        new_order=order
    )
    return success_response(
        data=result,
        message="Edge updated successfully"
    )

@router.delete("/edges/{item_id}")
async def delete_edge(item_id: int, db: Session = Depends(get_db)):
    service = PropertyService(db, edge_models.Edge)
    await call_service(service.delete_item, item_id)
    return success_response(
        data=None,
        message="Edge deleted successfully"
    )

# --- AB Type APIs ---
@router.get("/ab-types")
async def get_ab_types(db: Session = Depends(get_db)):
    items = db.query(stone_type_models.StoneType).all()
    return success_response(
        data=items,
        message="AB types retrieved successfully"
    )

@router.put("/ab-types/{item_id}")
async def update_ab_type(item_id: int, name: str, order: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_type_models.StoneType)
    result = await call_service(
        service.update_item,
        item_id,
        new_name=name,
        new_order=order
    )
    return success_response(
        data=result,
        message="AB type updated successfully"
    )

@router.delete("/ab-types/{item_id}")
async def delete_ab_type(item_id: int, db: Session = Depends(get_db)):
    service = PropertyService(db, stone_type_models.StoneType)
    await call_service(service.delete_item, item_id)
    return success_response(
        data=None,
        message="AB type deleted successfully"
    )

# --- FAB APIs ---
@router.post("/fabs")
async def create_fab(
    job_id: int,
    sales_person_id: int,
    fab_type: str,
    account_id: int,
    stone_type: str,
    stone_color: str,
    stone_thickness: str,
    area: str,
    edge: str,
    total_sqft: str,
    notes: str = None,
    steps: str = None,
    db: Session = Depends(get_db)
):
    service = JobService(db)
    fab_data = {
        "fab_type": fab_type,
        "stone_type": stone_type,
        "stone_color": stone_color,
        "stone_thickness": stone_thickness,
        "area": area,
        "edge": edge,
        "total_sqft": total_sqft,
        "notes": notes,
        "sales_person_id": sales_person_id,
        "steps": steps,
        "account_id": account_id
    }
    result = await call_service(
        service.create_fabid,
        job_id,
        fab_data,
        created_by=1  # Replace with actual user id
    )
    return success_response(
        data=result,
        message="FAB created successfully"
    )

@router.put("/fabs/{fab_id}")
async def update_fab(fab_id: int, update_data: dict, db: Session = Depends(get_db)):
    service = JobService(db)
    result = await call_service(
        service.update_fabid_before_templating,
        fab_id,
        update_data,
        user_id=1  # Replace with actual user id
    )
    return success_response(
        data=result,
        message="FAB updated successfully"
    )

@router.delete("/fabs/{fab_id}")
async def delete_fab(fab_id: int, db: Session = Depends(get_db)):
    fab = db.get(fab_models.Fab, fab_id)
    if not fab:
        raise error_response("FAB not found", 404)
    db.delete(fab)
    db.commit()
    return success_response(
        data=None,
        message="FAB deleted successfully"
    )
