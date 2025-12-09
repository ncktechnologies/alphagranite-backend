import logging
from typing import Optional
from sqlalchemy.orm import Session
from src.app.database.user import User
from src.app.utils.config import get_db
from fastapi import File, Form, UploadFile
from src.app.service.file import FileService
from src.app.routers.auth import get_current_user
from src.app.service.employee import EmployeeService
from src.app.utils.permissions import PermissionChecker
# Employee router handles operations related to employees
# Note: Employees are stored in the same 'users' table as regular users,
# they are differentiated by roles and permissions
from src.app.utils.helpers import success_response, call_service
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Path, Query, HTTPException, status, Body 
from src.app.utils.enrichment import enrich_employee_with_profile_image, enrich_employees_with_profile_images
from src.app.interface.employee_schemas import (
    EmployeeCreate, EmployeeListResponse, EmployeeResponse, EmployeeStatusUpdate, 
    EmployeeUpdate, EmployeeActivateToggle, BulkEmployeeActivateRequest, BulkStatusResult,
)

employee_router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={404: {"description": "Not found"}},
)

@employee_router.post("")
async def create_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    department: int = Form(...),
    phone: str = Form(None),
    gender: str = Form(None),
    home_address: str = Form(None),
    role_id: Optional[int] = Form(None),
    profile_image: UploadFile = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: User = Depends(PermissionChecker("employees", "create"))
):
    """
    Create a new employee with optional profile image
    - Requires authentication
    - Requires department assignment
    - Generates a unique username
    - Sets a random temporary password
    - Sends email with login credentials
    """
    
    # Validate required fields
    if not email or email == "string" or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email address is required")
    if not first_name or first_name == "string":
        raise HTTPException(status_code=400, detail="Valid first name is required")
    if not last_name or last_name == "string":
        raise HTTPException(status_code=400, detail="Valid last name is required")
    
    # Debug logging for profile_image
    print(f"[CREATE ROUTER] profile_image received: {profile_image}")
    print(f"[CREATE ROUTER] profile_image type: {type(profile_image)}")
    print(f"[CREATE ROUTER] profile_image is UploadFile: {isinstance(profile_image, UploadFile)}")
    print(f"[CREATE ROUTER] profile_image has 'file' attribute: {hasattr(profile_image, 'file')}")
    if profile_image:
        print(f"[CREATE ROUTER] profile_image attributes: {dir(profile_image)}")
    
    # Handle profile image upload if provided
    profile_image_id = None
    if profile_image and  hasattr(profile_image, 'file'):
        print(f"[CREATE ROUTER] Uploading profile image: {profile_image.filename}")
        file_data = await call_service(
            FileService.upload_file,
            db=db,
            file=profile_image,
            user_id=current_user.id
        )
        profile_image_id = file_data["id"] if file_data else None
        print(f"[CREATE ROUTER] Profile image uploaded with ID: {profile_image_id}")
    
    # Create employee data object from form data (including profile_image_id and role_id)
    data = EmployeeCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone if phone and phone != "string" else None,
        department=department,
        gender=gender if gender and gender != "string" else None,
        home_address=home_address if home_address and home_address != "string" else None,
        profile_image_id=profile_image_id,
        role_id=role_id
    )
    
    print(f"[CREATE ROUTER] EmployeeCreate data object created with profile_image_id: {data.profile_image_id}")
    
    # Create the employee
    result = await call_service(
        EmployeeService.create_employee,
        db=db,
        data=data,
        current_user_id=current_user.id,
        profile_image_id=profile_image_id,
        background_tasks=background_tasks
    )
    # Diagnostic log: show what the service returned before enrichment
    logger = logging.getLogger("employee_router")
    logger.info(f"[ROUTER] create_employee service result: type={type(result)} repr={result!r}")
    logger.info(f"[ROUTER] profile_image_id in data: {data.profile_image_id}, passed to service: {data.profile_image_id}")

    # Extract employee and password from result
    employee = result["employee"]
    generated_password = result["password"]
    
    # Enrich employee with profile image URL
    enriched_employee = await enrich_employee_with_profile_image(db, employee)
    
    # Add generated password to response
    enriched_employee["password"] = generated_password
    
    return success_response(
        data=enriched_employee,
        message="Employee created successfully. Password has been generated and sent to employee's email."
    )

@employee_router.get("/{employee_id}")
async def get_employee(
    employee_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("employees", "read")),
    db: Session = Depends(get_db)
):
    """
    Get employee details by ID
    """
    
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
    employee_id: int = Path(..., ge=1),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    home_address: Optional[str] = Form(None),
    role_id: Optional[str] = Form(None),
    profile_image: UploadFile = File(None),
    current_user: User = Depends(PermissionChecker("employees", "update")),
    db: Session = Depends(get_db)
):
    """
    Update employee details with optional profile image upload
    """
    
    # Debug logging
    print(f"\n{'='*80}")
    print(f"[UPDATE ROUTER] Received update request for employee {employee_id}")
    print(f"[UPDATE ROUTER] Raw home_address: '{home_address}'")
    print(f"{'='*80}\n")
    
    # Convert empty strings to None
    dep_id = int(department_id) if department_id not in (None, "", "null") else None
    r_id = int(role_id) if role_id not in (None, "", "null") else None
    
    # Handle profile image upload if provided
    profile_image_id = None
    if profile_image and profile_image.filename:
        if profile_image.size > 0:
            print(f"[UPDATE ROUTER] Uploading profile image: {profile_image.filename}")
            file_data = await call_service(
                FileService.upload_file,
                db=db,
                file=profile_image,
                user_id=current_user.id
            )
            profile_image_id = file_data["id"]
            print(f"[UPDATE ROUTER] Profile image uploaded with ID: {profile_image_id}")
    
    # Build update dict ONLY with fields that were actually provided
    update_dict = {}
    
    if first_name not in (None, "", "null"):
        update_dict["first_name"] = first_name
    if last_name not in (None, "", "null"):
        update_dict["last_name"] = last_name
    if email not in (None, "", "null"):
        update_dict["email"] = email
    if phone_number not in (None, "", "null"):
        update_dict["phone_number"] = phone_number
    if dep_id is not None:
        update_dict["department_id"] = dep_id
    if gender not in (None, "", "null"):
        update_dict["gender"] = gender
    if home_address not in (None, "", "null"):  # ← This is the key fix!
        update_dict["home_address"] = home_address
        print(f"[UPDATE ROUTER] Adding home_address to update: '{home_address}'")
    if r_id is not None:
        update_dict["role_id"] = r_id
    if profile_image_id is not None:
        update_dict["profile_image_id"] = profile_image_id
    
    # Create update data object using parse_obj to only set provided fields
    data = EmployeeUpdate(**update_dict)
    
    print(f"\n[UPDATE ROUTER] EmployeeUpdate Schema:")
    print(f"  - Update dict: {update_dict}")
    print(f"  - Exclude unset: {data.model_dump(exclude_unset=True)}")
    print(f"  - home_address in data: '{data.home_address if hasattr(data, 'home_address') else 'NOT SET'}'")
    
    # Call service using helper for error handling
    print(f"\n[UPDATE ROUTER] Calling EmployeeService.update_employee...")
    result = await call_service(
        EmployeeService.update_employee,
        db=db,
        employee_id=employee_id,
        data=data,
        current_user_id=current_user.id,
        profile_image_id=profile_image_id
    )
    
    print(f"\n[UPDATE ROUTER] Service returned:")
    print(f"  - Type: {type(result)}")
    if hasattr(result, 'home_address'):
        print(f"  - home_address: '{result.home_address}'")
    
    # Enrich employee with profile image URL
    enriched_employee = await enrich_employee_with_profile_image(db, result)
    
    print(f"\n[UPDATE ROUTER] Final response:")
    print(f"  - home_address: '{enriched_employee.get('home_address')}'")
    print(f"{'='*80}\n")
    
    return success_response(
        data=enriched_employee,
        message="Employee updated successfully"
    )

@employee_router.patch("/{employee_id}/status")
async def update_employee_status(
    data: EmployeeStatusUpdate,
    background_tasks: BackgroundTasks,
    employee_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("employees", "update")),
    db: Session = Depends(get_db)
):
    """
    Update employee status
    Status codes:
    1 - Active
    2 - Inactive
    3 - Deleted
    """
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.update_employee_status,
        db=db,
        employee_id=employee_id,
        status_id=data.status,
        current_user_id=current_user.id,
        background_tasks=background_tasks
    )
    
    # Get status name for message
    status_names = {1: "Active", 2: "Inactive", 3: "Deleted"}
    status_name = status_names.get(data.status, "Updated")
    
    return success_response(
        data=result,
        message=f"Employee status changed to {status_name} successfully"
    )

@employee_router.patch("/{employee_id}/activate")
async def toggle_employee_activation(
    data: EmployeeActivateToggle,
    background_tasks: BackgroundTasks,
    employee_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("employees", "update")),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate an employee
    - active=true: Sets status to Active (1)
    - active=false: Sets status to Inactive (2)
    """
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.toggle_employee_active_status,
        db=db,
        employee_id=employee_id,
        active=data.active,
        current_user_id=current_user.id,
        background_tasks=background_tasks
    )
    
    # Status message for response
    status_action = "activated" if data.active else "deactivated"
    
    return success_response(
        data=result,
        message=f"Employee {status_action} successfully"
    )

@employee_router.post("/bulk-activate")
async def bulk_toggle_employee_activation(
    data: BulkEmployeeActivateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(PermissionChecker("employees", "update")),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate multiple employees at once
    
    Request body:
    {
      "employee_ids": [1, 2, 3],
      "active": true  # true to activate, false to deactivate
    }
    
    Returns:
    {
      "success": [1, 2],  # IDs successfully updated
      "failed": [3],       # IDs that failed
      "message": "Updated 2 of 3 employees to active"
    }
    """
    
    # Call service using helper for error handling
    result = await call_service(
        EmployeeService.bulk_toggle_employee_active_status,
        db=db,
        employee_ids=data.employee_ids,
        active=data.active,
        current_user_id=current_user.id,
        background_tasks=background_tasks
    )
    
    # Status action for message
    status_action = "activated" if data.active else "deactivated"
    
    return success_response(
        data=result,
        message=f"Bulk {status_action} {len(result['success'])} employees"
    )

@employee_router.delete("/{employee_id}")
async def delete_employee(
    background_tasks: BackgroundTasks,
    employee_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("employees", "delete")),
    db: Session = Depends(get_db)
):
    """
    Delete an employee (sets status to deleted)
    """
    
    # Call service to update status to deleted (3)
    await call_service(
        EmployeeService.update_employee_status,
        db=db,
        employee_id=employee_id,
        status_id=3,  # 3 = Deleted
        current_user_id=current_user.id,
        background_tasks=background_tasks
    )
    
    return success_response(
        data=None,
        message="Employee deleted successfully"
    )

@employee_router.get("")
async def get_employees(
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
    current_user: User = Depends(PermissionChecker("employees", "read")),
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
    email: str,
    current_user: User = Depends(PermissionChecker("employees", "read")),
    db: Session = Depends(get_db)
):
    """
    Check if email is unique
    Returns {"unique": true/false}
    """
    
    is_unique = await EmployeeService.is_email_unique(db, email)
    
    return success_response(
        data={"unique": is_unique},
        message="Email uniqueness check completed"
    )