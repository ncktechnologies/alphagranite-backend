from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Path, Query, HTTPException, statusest, BackgroundTasks, Path, Query, HTTPException, status

from src.app.utils.config import get_db

from src.app.service.file import FileService
from src.app.service.employee import EmployeeService
# Employee router handles operations related to employees
# Note: Employees are stored in the same 'users' table as regular users,
# they are differentiated by roles and permissions
from src.app.utils.helpers import success_response, call_service
from src.app.utils.enrichment import enrich_employee_with_profile_image, enrich_employees_with_profile_images
from src.app.interface.employee_schemas import EmployeeCreate, EmployeeListResponse, EmployeeResponse, EmployeeStatusUpdate, EmployeeUpdate

employee_router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={404: {"description": "Not found"}},
)

@employee_router.post("")
async def create_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    department: int = Form(...),
    gender: str = Form(None),
    home_address: str = Form(None),
    role_id: int = Form(None),
    profile_image: UploadFile = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Create a new employee with optional profile image
    - Requires authentication
    - Generates a unique username
    - Sets a random temporary password
    - Sends email with login credentials
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Create employee data object from form data
    data = EmployeeCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        department=department,
        gender=gender,
        home_address=home_address,
        role_id=role_id
    )
    
    # Handle profile image upload if provided
    profile_image_id = None
    if profile_image:
        # Upload the profile image
        file_data = await call_service(
            FileService.upload_file,
            db=db,
            file=profile_image,
            current_user=current_user["user_id"]
        )
        data.profile_image_id = file_data.id
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.create_employee,
        db=db,
        data=data,
        current_user_id=current_user["user_id"],
        background_tasks=background_tasks
    )
    
    # Enrich employee with profile image URL
    enriched_employee = await enrich_employee_with_profile_image(db, result)
    
    return success_response(
        data=enriched_employee,
        message="Employee created successfully"
    )

@employee_router.get("/{employee_id}")
async def get_employee(
    request: Request,
    employee_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get employee details by ID
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    employee = await call_service(
        EmployeeService.get_employee,
        db=db,
        employee_id=employee_id
    )
    
    # Enrich employee with profile image URL
    enriched_employee = await enrich_employee_with_profile_image(db, employee)
    
    return success_response(
        data=enriched_employee,
        message="Employee details retrieved successfully"
    )

@employee_router.put("/{employee_id}")
async def update_employee(
    request: Request,
    employee_id: int = Path(..., ge=1),
    first_name: str = Form(None),
    last_name: str = Form(None),
    email: str = Form(None),
    phone_number: str = Form(None),
    department_id: int = Form(None),
    gender: str = Form(None),
    home_address: str = Form(None),
    role_id: int = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Update employee details with optional profile image upload
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Create employee update object from form data
    data = EmployeeUpdate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        department_id=department_id,
        gender=gender,
        home_address=home_address,
        role_id=role_id
    )
    
    # Handle profile image upload if provided
    profile_image_id = None
    if profile_image:
        # Upload the profile image
        file_data = await call_service(
            FileService.upload_file,
            db=db,
            file=profile_image,
            current_user=current_user["user_id"]
        )
        profile_image_id = file_data.id
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.update_employee,
        db=db,
        employee_id=employee_id,
        data=data,
        current_user_id=current_user["user_id"],
        profile_image_id=profile_image_id
    )
    
    # Enrich employee with profile image URL
    enriched_employee = await enrich_employee_with_profile_image(db, result)
    
    return success_response(
        data=enriched_employee,
        message="Employee updated successfully"
    )

@employee_router.patch("/{employee_id}/status")
async def update_employee_status(
    request: Request,
    data: EmployeeStatusUpdate,
    background_tasks: BackgroundTasks,
    employee_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Update employee status
    Status codes:
    1 - Active
    2 - Inactive
    3 - Deleted
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.update_employee_status,
        db=db,
        employee_id=employee_id,
        status_id=data.status,
        current_user_id=current_user["user_id"],
        background_tasks=background_tasks
    )
    
    # Get status name for message
    status_names = {1: "Active", 2: "Inactive", 3: "Deleted"}
    status_name = status_names.get(data.status, "Updated")
    
    return success_response(
        data=result,
        message=f"Employee status changed to {status_name} successfully"
    )

@employee_router.delete("/{employee_id}")
async def delete_employee(
    request: Request,
    background_tasks: BackgroundTasks,
    employee_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Delete an employee (sets status to deleted)
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service to update status to deleted (3)
    await call_service(
        EmployeeService.update_employee_status,
        db=db,
        employee_id=employee_id,
        status_id=3,  # 3 = Deleted
        current_user_id=current_user["user_id"],
        background_tasks=background_tasks
    )
    
    return success_response(
        data=None,
        message="Employee deleted successfully"
    )

@employee_router.get("")
async def get_employees(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for name, email or username"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID (1=Active, 2=Inactive, 3=Deleted)"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    email: Optional[str] = Query(None, description="Filter by exact email address"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    sort_by: Optional[str] = Query("id", description="Field to sort by (id, first_name, last_name, email, created_at)"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    db: Session = Depends(get_db)
):
    """
    Get list of employees with pagination and filtering
    
    This endpoint returns a paginated list of employees with various filtering options.
    You can adjust the number of items per page using the limit parameter.
    
    Filter options include:
    - Search by name/email/username
    - Filter by department, status, role
    - Filter by exact email or phone
    - Sort by various fields in ascending or descending order
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.get_employees,
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id,
        status_id=status_id,
        role_id=role_id,
        email=email,
        phone=phone,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Enrich employees with profile image URLs
    if result["data"]:
        employees_data = result["data"]
        enriched_employees = await enrich_employees_with_profile_images(db, employees_data)
        result["data"] = enriched_employees
    
    return success_response(
        data=result,
        message="Employees retrieved successfully"
    )

@employee_router.get("/check-email/{email}")
async def check_email_unique(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check if email is unique
    Returns {"unique": true/false}
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    # Note: is_email_unique is likely not async, so we don't use call_service
    is_unique = EmployeeService.is_email_unique(db, email)
    
    return success_response(
        data={"unique": is_unique},
        message="Email uniqueness check completed"
    )