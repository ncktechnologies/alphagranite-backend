from fastapi import status
from fastapi.responses import JSONResponse
from pydantic.generics import GenericModel
from typing import TypeVar, Generic, Optional, Any, Dict, Union, List


T = TypeVar("T")


class SuccessResponse(GenericModel, Generic[T]):
    """Generic success wrapper used across the API.

    Fields:
    - success: always True for successful responses
    - message: a human readable message
    - data: the payload (can be None)
    """
    success: bool = True
    message: str
    data: Optional[T] = None


def success_response(
    data: Any = None, 
    message: str = "Operation completed successfully",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response.
    
    Args:
        data: The data to include in the response
        message: A human-readable message describing the result
        status_code: HTTP status code (default: 200)
        
    Returns:
        JSONResponse: A FastAPI JSONResponse with the standardized format
    """
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    return JSONResponse(content=response_data, status_code=status_code)


def error_response(
    message: str, 
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        message: A human-readable error message
        status_code: HTTP status code (default: 400)
        errors: Optional dictionary of field-specific error messages
        
    Returns:
        JSONResponse: A FastAPI JSONResponse with the error details
    """
    response_data = {
        "success": False,
        "message": message,
    }
    
    if errors:
        response_data["errors"] = errors
    
    return JSONResponse(content=response_data, status_code=status_code)
