from typing import List
from fastapi import APIRouter, Depends
from src.app.database.user import User
from src.app.interface.business_schemas import FabTypeResponse
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()

# Predefined fab types - can be moved to database later
FAB_TYPES = [
    {"name": "standard", "description": "Standard fabrication"},
    {"name": "fab only", "description": "Fabrication only"},
    {"name": "ag redo", "description": "Alpha Granit redo"},
    {"name": "cust redo", "description": "Customer redo"},
    {"name": "resurface", "description": "Resurface existing work"},
    {"name": "fast track", "description": "Fast track priority fabrication"}
]


@router.get("/fab-types", response_model=List[FabTypeResponse])
async def get_fab_types(
    current_user: User = Depends(get_current_user)
):
    """Get list of available fabrication types"""
    return FAB_TYPES