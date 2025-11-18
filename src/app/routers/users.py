from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.user import User
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse, success_response, error_response

router = APIRouter()

@router.get("/users/sales-persons", response_model=SuccessResponse[List[dict]])
async def get_sales_persons(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all sales persons with their basic information
    """
    query = select(
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        User.phone
    ).where(
        # Only active users
        User.status == 1
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    query = query.offset(skip).limit(limit).order_by(User.first_name, User.last_name)
    
    result = await db.execute(query)
    users = result.all()
    
    # Convert to list of dicts for JSON serialization
    sales_persons = [
        {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "phone": user.phone
        }
        for user in users
    ]
    
    return success_response(sales_persons, "Sales persons fetched successfully")
