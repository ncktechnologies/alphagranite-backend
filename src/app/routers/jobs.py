from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.database import get_db
from src.app.database.business_job import BusinessJob
from src.app.database.user import User
from src.app.database.account import Account
from src.app.interface.business_schemas import (
    JobCreate, JobUpdate, JobResponse,
)
from src.app.utils.helpers import error_response, success_response
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.service import job_crud

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "create"))
):
    """Create a new job with job name, job number, and account_id"""
    job = await job_crud.create_job(db, job_data, current_user.id)
    return job


@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("jobs", "read"))
):
    """Get list of jobs with optional filtering"""
    jobs = await job_crud.get_jobs(db, skip, limit, account_id, status_id, priority)
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job by ID"""
    job = await job_crud.get_job_by_id(db, job_id)
    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job"""
    job = await job_crud.update_job(db, job_id, job_data, current_user.id)
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job (soft delete by setting status to deleted)"""
    await job_crud.delete_job(db, job_id, current_user.id)
    return None
