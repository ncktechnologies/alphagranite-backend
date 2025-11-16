from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, Query

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.job import Job
from src.app.database.fab import Fab
from src.app.database.account import Account
from src.app.database.stone_type import StoneType
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.edge import Edge
from src.app.interface.business_schemas import (
    JobWithFabsResponse,
    FabDetailResponse,
    TableNamesResponse,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import success_response

router = APIRouter()


@router.get("/jobs-with-fabs", response_model=SuccessResponse[List[JobWithFabsResponse]])
async def list_jobs_with_fabs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_id: int = Query(None, description="Filter by account ID"),
    status_id: int = Query(None, description="Filter by status ID"),
    priority: str = Query(None, description="Filter by priority"),
    search: str = Query(None, description="Search by job name or job number"),
    fab_type: str = Query(None, description="Filter by fab type"),
    current_stage: str = Query(None, description="Filter by fab current stage"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List jobs with their associated fabs and fab details.
    Includes filtering and search functionality.
    """
    
    # Build job query with filters
    job_query = select(Job)
    
    if account_id is not None:
        job_query = job_query.where(Job.account_id == account_id)
    if status_id is not None:
        job_query = job_query.where(Job.status_id == status_id)
    if priority:
        job_query = job_query.where(Job.priority == priority)
    if search:
        search_term = f"%{search}%"
        job_query = job_query.where(
            (Job.name.ilike(search_term)) | 
            (Job.job_number.ilike(search_term))
        )
    
    # Apply pagination
    job_query = job_query.offset(skip).limit(limit).order_by(Job.created_at.desc())
    
    result = await db.execute(job_query)
    jobs = result.scalars().all()
    
    # Build response with fabs
    response_data = []
    
    for job in jobs:
        # Get account name
        account_result = await db.execute(select(Account).where(Account.id == job.account_id))
        account = account_result.scalar_one_or_none()
        
        # Get fabs for this job
        fab_query = select(Fab).where(Fab.job_id == job.id)
        
        # Apply fab filters if provided
        if fab_type:
            fab_query = fab_query.where(Fab.fab_type.ilike(f"%{fab_type}%"))
        if current_stage:
            fab_query = fab_query.where(Fab.current_stage == current_stage)
        
        fab_result = await db.execute(fab_query)
        fabs = fab_result.scalars().all()
        
        # Build fab detail responses
        fab_details = []
        for fab in fabs:
            # Get related data
            stone_type = await db.execute(select(StoneType).where(StoneType.id == fab.stone_type_id))
            stone_color = await db.execute(select(StoneColor).where(StoneColor.id == fab.stone_color_id))
            stone_thickness = await db.execute(select(StoneThickness).where(StoneThickness.id == fab.stone_thickness_id))
            edge = await db.execute(select(Edge).where(Edge.id == fab.edge_id))
            sales_person = await db.execute(select(User).where(User.id == fab.sales_person_id))
            
            stone_type_obj = stone_type.scalar_one_or_none()
            stone_color_obj = stone_color.scalar_one_or_none()
            stone_thickness_obj = stone_thickness.scalar_one_or_none()
            edge_obj = edge.scalar_one_or_none()
            sales_person_obj = sales_person.scalar_one_or_none()
            
            fab_detail = FabDetailResponse(
                id=fab.id,
                job_id=fab.job_id,
                fab_type=fab.fab_type,
                sales_person_id=fab.sales_person_id,
                stone_type_id=fab.stone_type_id,
                stone_color_id=fab.stone_color_id,
                stone_thickness_id=fab.stone_thickness_id,
                edge_id=fab.edge_id,
                input_area=fab.input_area,
                total_sqft=fab.total_sqft,
                notes=fab.notes,
                template_needed=fab.template_needed,
                drafting_needed=fab.drafting_needed,
                slab_smith_cust_needed=fab.slab_smith_cust_needed,
                slab_smith_ag_needed=fab.slab_smith_ag_needed,
                sct_needed=fab.sct_needed,
                final_programming_needed=fab.final_programming_needed,
                current_stage=fab.current_stage,
                status_id=fab.status_id,
                created_at=fab.created_at,
                created_by=fab.created_by,
                updated_at=fab.updated_at,
                updated_by=fab.updated_by,
                stone_type_name=stone_type_obj.name if stone_type_obj else None,
                stone_color_name=stone_color_obj.name if stone_color_obj else None,
                stone_thickness_value=stone_thickness_obj.thickness if stone_thickness_obj else None,
                edge_name=edge_obj.name if edge_obj else None,
                sales_person_name=sales_person_obj.username if sales_person_obj else None,
            )
            fab_details.append(fab_detail)
        
        job_with_fabs = JobWithFabsResponse(
            id=job.id,
            name=job.name,
            job_number=job.job_number,
            account_id=job.account_id,
            account_name=account.name if account else None,
            priority=job.priority,
            status_id=job.status_id,
            created_at=job.created_at,
            fabs=fab_details
        )
        response_data.append(job_with_fabs)
    
    return success_response(response_data, "Jobs with fabs fetched successfully")


@router.get("/table-names", response_model=SuccessResponse[TableNamesResponse])
async def get_table_names(
    current_user: User = Depends(get_current_user)
):
    """
    Return list of table names useful for clockwork context.
    e.g., 'templatings', 'draftings', etc.
    """
    
    table_names = [
        "templatings",
        "draftings",
        "slab_smiths",
        "sales_cts",
        "final_programmings",
        "cut_list"
    ]
    
    return success_response(
        TableNamesResponse(table_names=table_names),
        "Table names fetched successfully"
    )
