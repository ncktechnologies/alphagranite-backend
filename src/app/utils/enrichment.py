from sqlalchemy import select
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.service.file import FileService
from src.app.utils.config import get_settings

async def enrich_employee_with_profile_image(
    db: AsyncSession, 
    employee: Dict[str, Any]
) -> Dict[str, Any]:
    import logging
    logger = logging.getLogger("employee_enrichment")
    settings = get_settings()
    
    if not employee:
        logger.warning("[ENRICH] No employee data provided.")
        return employee
    
    logger.info(f"[ENRICH] Input employee type: {type(employee)}, value: {employee!r}")
    
    result = None
    if isinstance(employee, dict):
        result = {**employee}
        logger.info(f"[ENRICH] Enriching employee dict: keys={result.keys()}, profile_image_id={result.get('profile_image_id')}")
    elif hasattr(employee, "__dict__"):
        result = {**employee.__dict__}
        logger.info(f"[ENRICH] Enriching employee object: profile_image_id={result.get('profile_image_id')}")
        if "_sa_instance_state" in result:
            del result["_sa_instance_state"]
    else:
        logger.warning("[ENRICH] Employee is neither dict nor object with __dict__.")
        return employee

    # Remove sensitive fields
    sensitive_fields = ["password", "failed_login_attempts", "is_locked", "locked_at", "is_first_login"]
    for field in sensitive_fields:
        if field in result:
            del result[field]

    # Add status name
    if result.get("status"):
        from src.app.database.status import Status
        status_result = await db.execute(select(Status).where(Status.value_id == result["status"]))
        status_obj = status_result.scalars().first()
        result["status_name"] = status_obj.name if status_obj else None

    # Add department name
    if result.get("department"):
        from src.app.database.department import Department
        dept_result = await db.execute(select(Department).where(Department.id == result["department"]))
        dept_obj = dept_result.scalars().first()
        result["department_name"] = dept_obj.name if dept_obj else None

    # Add profile_image_url
    if result.get("profile_image_id"):
        logger.info(f"[ENRICH] Fetching file for profile_image_id: {result['profile_image_id']}")
        file_data = await FileService.get_file(db, result["profile_image_id"])
        logger.info(f"[ENRICH] File data: {file_data}")
        if file_data and file_data.get("url"):
            result["profile_image_url"] = file_data.get("url")
        else:
            # If file not found, use default
            logger.warning(f"[ENRICH] File not found for profile_image_id: {result['profile_image_id']}, using default")
            result["profile_image_url"] = f"{settings.API_BASE_URL}/static/defaults/profile.png"
    else:
        logger.info("[ENRICH] No profile_image_id, using default profile image URL.")
        result["profile_image_url"] = f"{settings.API_BASE_URL}/static/defaults/profile.png"

    logger.info(f"[ENRICH] Final enriched employee: {result}")
    return result

async def enrich_employees_with_profile_images(
    db: AsyncSession,
    employees: List
) -> List[Dict[str, Any]]:
    if not employees:
        return []
        
    enriched_employees = []
    
    for employee in employees:
        enriched_employee = await enrich_employee_with_profile_image(db, employee)
        enriched_employees.append(enriched_employee)
        
    return enriched_employees
