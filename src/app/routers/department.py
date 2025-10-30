import math
import math
from src.app.database.user import User
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.department import Department
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Request
from src.app.interface.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentSummary,
    DepartmentWithUsers,
    DepartmentStatusChange,
    DepartmentListResponse,
    DepartmentUsersResponse,
)
from src.app.utils.config import get_db
from src.app.routers.auth import get_current_user
from src.app.service.department import DepartmentService
from src.app.utils.helpers import success_response, call_service

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
    dependencies=[Depends(get_current_user)],
)

@router.post(
    "", 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department"
)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new department with the given name and description
    
    - **name**: Required - Unique department name
    - **description**: Optional - Department description
    """
    # Use call_service to handle errors
    department = await call_service(
        DepartmentService.create_department, 
        db=db, 
        data=data, 
        user_id=current_user.id
    )
    
    # Get department with users for the response
    department_details = await call_service(
        DepartmentService.get_department_details,
        db=db, 
        department_id=department.id
    )
    
    return success_response(
        data=department_details,
        message="Department created successfully"
    )

@router.put(
    "/{department_id}",
    summary="Update a department"
)
async def update_department(
    data: DepartmentUpdate,
    department_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing department's details
    
    - **name**: Optional - New department name (must be unique)
    - **description**: Optional - New department description
    """
    # Use call_service to handle errors
    department = await call_service(
        DepartmentService.update_department,
        db=db, 
        department_id=department_id,
        data=data, 
        user_id=current_user.id
    )
    
    # Get department with users for the response
    department_details = await call_service(
        DepartmentService.get_department_details,
        db=db, 
        department_id=department.id
    )
    
    return success_response(
        data=department_details,
        message="Department updated successfully"
    )

@router.patch(
    "/{department_id}/status",
    summary="Change department status"
)
async def change_department_status(
    data: DepartmentStatusChange,
    department_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the status of a department
    
    - **status**: Required - New status value
    
    Note: Cannot change status if department has users assigned.
    """
    # Use call_service to handle errors
    department = await call_service(
        DepartmentService.change_department_status,
        db=db, 
        department_id=department_id,
        status_data=data, 
        user_id=current_user.id
    )
    
    # Get department with users for the response
    department_details = await call_service(
        DepartmentService.get_department_details,
        db=db, 
        department_id=department.id
    )
    
    return success_response(
        data=department_details,
        message=f"Department status changed successfully"
    )

@router.delete(
    "/{department_id}",
    summary="Delete a department"
)
async def delete_department(
    department_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a department (soft delete by changing status)
    
    
    Note: Cannot delete if department has users assigned.
    """
    result = await call_service(
        DepartmentService.delete_department,
        db=db, 
        department_id=department_id, 
        user_id=current_user.id
    )
    
    return success_response(
        data=None,
        message=result["message"]
    )

@router.get(
    "", 
    summary="List all departments"
)
async def list_departments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[int] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all departments with summary information:
    
    - Department name and description
    - Number of members
    - Sample of up to 5 users with profile photos
    
    Results can be filtered by department status and paginated.
    """
    departments, total = await call_service(
        DepartmentService.get_departments_list,
        db=db, 
        page=page, 
        size=size, 
        status_filter=status
    )
    
    # Calculate pagination values
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    response_data = {
        "items": departments,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }
    
    return success_response(
        data=response_data,
        message="Departments retrieved successfully"
    )

@router.get(
    "/{department_id}", 
    summary="Get department details"
)
async def get_department(
    department_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific department including all users
    """
    department = await call_service(
        DepartmentService.get_department_details,
        db=db, 
        department_id=department_id
    )
    
    return success_response(
        data=department,
        message="Department details retrieved successfully"
    )

@router.get(
    "/{department_id}/users",
    summary="List users in a department"
)
async def list_department_users(
    department_id: int = Path(..., gt=0),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: Optional[str] = Query(None, description="Sort order (asc or desc)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of users in a department with detailed information:
    
    - Department name and description
    - List of users with personal details
    
    Results can be:
    - Filtered by gender
    - Searched by first name, last name, or email
    - Sorted by various fields
    - Paginated with customizable page size
    """
    result = await call_service(
        DepartmentService.get_department_users,
        db=db, 
        department_id=department_id, 
        page=page, 
        size=size, 
        search=search, 
        gender=gender, 
        sort_by=sort_by, 
        sort_order=sort_order
    )
    
    department_info, users, total, total_pages = result
    
    response_data = {
        **department_info,
        "users": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }
    
    return success_response(
        data=response_data,
        message="Department users retrieved successfully"
    )