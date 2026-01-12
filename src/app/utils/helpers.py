from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable, TypeVar, Awaitable
from fastapi import HTTPException
from pydantic import ValidationError
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> HTTPException:
    """Create standardized error response"""
    error_data = {
        "success": False,
        "message": message,
        "details": details
    }
    return HTTPException(status_code=status_code, detail=error_data)

async def call_service(
    service_func: Callable[..., Awaitable[T]], 
    *args, 
    **kwargs
) -> T:
    """
    Call service function with error handling middleware
    """
    try:
        result = await service_func(*args, **kwargs)
        return result
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Pydantic validation error: {str(e)}")
        raise error_response(f"Validation failed: {str(e)}", 422)
    except ValueError as e:
        logger.error(f"Value error in service call: {str(e)}")
        raise error_response(f"Invalid data: {str(e)}", 422)
    except Exception as e:
        logger.error(f"Unexpected error in service call: {str(e)}")
        raise error_response("Internal server error", 500)

def strip_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert datetime to UTC and remove timezone info for database storage.
    PostgreSQL stores timestamps without timezone by default.
    """
    if dt is None:
        return None
    
    # If timezone-aware, convert to UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    
    # Remove timezone info for database storage
    return dt.replace(tzinfo=None)

# Add this utility
def utc_now() -> datetime:
    """Get current UTC time as naive datetime for database storage"""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 format string with UTC timezone.
    Returns format: 2024-01-15T14:30:00Z
    """
    if dt is None:
        return None
    
    # If naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if not already
        dt = dt.astimezone(timezone.utc)
    
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')