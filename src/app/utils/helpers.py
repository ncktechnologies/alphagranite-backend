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
    """Normalize a datetime to aware UTC for database storage.

    Name kept for backwards compatibility; SQLModel now requires aware values.
    """
    return to_utc(dt)

# Add this utility
def utc_now() -> datetime:
    """Current UTC time, timezone-aware (SQLModel requires aware datetimes)."""
    return datetime.now(timezone.utc)


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize any datetime to aware UTC; naive input is assumed to be UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

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