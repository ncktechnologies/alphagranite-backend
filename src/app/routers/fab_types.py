from typing import List
from fastapi import APIRouter, Depends
from src.app.database.user import User
from src.app.interface.business_schemas import FabTypeResponse
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()

# Predefined fab types - can be moved to database later
FAB_TYPES = [
    {"name": "Kitchen Countertop", "description": "Standard kitchen counter fabrication"},
    {"name": "Bathroom Vanity", "description": "Bathroom vanity top fabrication"},
    {"name": "Island Top", "description": "Kitchen island countertop fabrication"},
    {"name": "Bar Top", "description": "Bar counter fabrication"},
    {"name": "Fireplace Surround", "description": "Decorative fireplace stone work"},
    {"name": "Backsplash", "description": "Kitchen or bathroom backsplash"},
    {"name": "Shower Walls", "description": "Shower enclosure stone walls"},
    {"name": "Floor Tiles", "description": "Natural stone floor installation"},
    {"name": "Custom Design", "description": "Custom fabrication project"},
    {"name": "Repair/Restoration", "description": "Repair or restoration work"}
]


@router.get("/fab-types", response_model=List[FabTypeResponse])
async def get_fab_types(
    current_user: User = Depends(get_current_user)
):
    """Get list of available fabrication types"""
    return FAB_TYPES