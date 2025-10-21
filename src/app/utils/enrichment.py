from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession 

from src.app.service.file import FileService
from src.app.utils.config import get_settings

async def enrich_employee_with_profile_image(
    db: AsyncSession, 
    employee: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich employee data with profile image URL
    
    Args:
        db: Database session
        employee: Employee data dictionary
        
    Returns:
        Employee data with profile_image_url field
    """
    settings = get_settings()
    
    # Handle both single employee and list of employees
    if not employee:
        return employee
    
    # Create a copy to avoid modifying the original
    if isinstance(employee, dict):
        # Enrich a single employee
        result = {**employee}
        
        # Add profile_image_url field if profile_image_id exists
        if result.get("profile_image_id"):
            file_data = await FileService.get_file(db, result["profile_image_id"])
            if file_data:
                result["profile_image_url"] = file_data.get("url")
            else:
                result["profile_image_url"] = None
        else:
            # Set default profile image
            result["profile_image_url"] = f"{settings.API_BASE_URL}/static/defaults/profile.png"
            
        return result
    
    elif hasattr(employee, "__dict__"):
        # Convert SQLAlchemy model to dict and enrich
        result = {**employee.__dict__}
        
        # Remove SQLAlchemy internal attributes
        if "_sa_instance_state" in result:
            del result["_sa_instance_state"]
        
        # Add profile_image_url field if profile_image_id exists
        if result.get("profile_image_id"):
            file_data = await FileService.get_file(db, result["profile_image_id"])
            if file_data:
                result["profile_image_url"] = file_data.get("url")
            else:
                result["profile_image_url"] = None
        else:
            # Set default profile image
            result["profile_image_url"] = f"{settings.API_BASE_URL}/static/defaults/profile.png"
            
        return result
    
    # If not a dict or model, return as is
    return employee

async def enrich_employees_with_profile_images(
    db: AsyncSession,
    employees: List
) -> List[Dict[str, Any]]:
    """
    Enrich a list of employees with profile image URLs
    
    Args:
        db: Database session
        employees: List of employee objects or dictionaries
        
    Returns:
        List of employees with profile_image_url fields
    """
    if not employees:
        return []
        
    enriched_employees = []
    
    for employee in employees:
        enriched_employee = await enrich_employee_with_profile_image(db, employee)
        enriched_employees.append(enriched_employee)
        
    return enriched_employees