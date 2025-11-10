"""
Health check router
"""
from sqlalchemy import text
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from ..interface.schemas import HealthResponse, DatabaseHealthResponse
from ..utils.helpers import success_response, error_response

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint"""
    return success_response(
        data={"status": "ok"},
        message="Health check passed"
    )


@router.get("/db")
async def database_health(db: Session = Depends(get_db)):
    """
    Database health check endpoint
    
    Tests the database connection by executing a simple query
    """
    try:
        # Execute a simple query to check if database is responding
        db.execute(text("SELECT 1"))
        return success_response(
            data={
                "status": "ok",
                "database": True
            },
            message="Database connection successful"
        )
    except Exception as e:
        # Return error if database connection fails
        raise error_response(
            message=f"Database connection failed: {str(e)}",
            status_code=503
        )