"""
Health check router
"""
from sqlalchemy import text
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from ..interface.schemas import HealthResponse, DatabaseHealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@router.get("/db", response_model=DatabaseHealthResponse)
async def database_health(db: Session = Depends(get_db)):
    """
    Database health check endpoint
    
    Tests the database connection by executing a simple query
    """
    try:
        # Execute a simple query to check if database is responding
        db.execute(text("SELECT 1"))
        return DatabaseHealthResponse(
            status="ok",
            database=True,
            message="Database connection successful"
        )
    except Exception as e:
        # Return error if database connection fails
        return DatabaseHealthResponse(
            status="error",
            database=False,
            message=f"Database connection failed: {str(e)}"
        )