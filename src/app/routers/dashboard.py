from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query

from src.app.database import get_db
from src.app.database.fab import Fab
from src.app.database.business_job import BusinessJob
from src.app.database.user import User
from src.app.database.templating import Templating
from src.app.interface.response_wrappers import SuccessResponse, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.get("/dashboard", response_model=SuccessResponse[dict])
async def get_dashboard(
    time_period: str = Query("all", description="Time period: 'all', 'today', 'this_week', 'this_month'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard data with KPIs, charts, and recent jobs"""
    
    # Determine date range based on time_period
    end_date = datetime.now()
    if time_period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_period == "this_week":
        start_date = end_date - timedelta(days=end_date.weekday())
    elif time_period == "this_month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # all
        start_date = None
    
    # Build query conditions
    date_filter = [Fab.created_at >= start_date] if start_date else []
    
    # 1. Total FABs count
    total_fabs_query = select(func.count(Fab.id)).where(and_(*date_filter)) if date_filter else select(func.count(Fab.id))
    total_fabs_result = await db.execute(total_fabs_query)
    total_fabs = total_fabs_result.scalar() or 0
    
    # 2. Pending Installations (status_id = 1, current_stage = install_scheduling or install_completion)
    pending_installations_query = select(func.count(Fab.id)).where(
        and_(
            Fab.status_id == 1,
            or_(Fab.current_stage == "install_scheduling", Fab.current_stage == "install_completion"),
            *date_filter
        )
    )
    pending_installations_result = await db.execute(pending_installations_query)
    pending_installations = pending_installations_result.scalar() or 0
    
    # 3. Average Revisions - Calculate average number of revisions per FAB
    revisions_query = select(
        func.avg(func.coalesce(Fab.revised, 0))
    ).where(and_(*date_filter)) if date_filter else select(
        func.avg(func.coalesce(Fab.revised, 0))
    )
    revisions_result = await db.execute(revisions_query)
    avg_revisions = revisions_result.scalar() or 0
    
    # 4. Completion Rate - Completed FABs / Total FABs
    completed_fabs_query = select(func.count(Fab.id)).where(
        and_(
            Fab.current_stage == "install_completion",
            Fab.status_id == 3,  # Completed status
            *date_filter
        )
    )
    completed_fabs_result = await db.execute(completed_fabs_query)
    completed_fabs = completed_fabs_result.scalar() or 0
    completion_rate = round((completed_fabs / total_fabs * 100) if total_fabs > 0 else 0, 2)
    
    # 5. Overall Statistics - FABs by status
    status_query = select(
        Fab.current_stage,
        func.count(Fab.id).label("count")
    ).group_by(Fab.current_stage)
    if date_filter:
        status_query = status_query.where(and_(*date_filter))
    
    status_result = await db.execute(status_query)
    status_rows = status_result.all()
    
    # Categorize stages into: Completed, In Progress, Paused
    stage_categories = {
        "Completed": ["install_completion"],
        "In Progress": ["templating", "pre_draft_review", "drafting", "sales_ct", "slab_smith_request", 
                       "final_programming", "wj_programming", "cut_list", "wj_scheduling", 
                       "resurface_scheduling", "cost_of_stone", "install_scheduling"],
        "Paused": ["revision"]
    }
    
    status_breakdown = {
        "Completed": 0,
        "In Progress": 0,
        "Paused": 0
    }
    
    for stage, count in status_rows:
        for category, stages in stage_categories.items():
            if stage in stages:
                status_breakdown[category] += count
                break
    
    # 6. Finance Data
    revenue_installed_query = select(func.sum(Fab.revenue)).where(
        and_(
            Fab.current_stage == "install_completion",
            Fab.revenue.isnot(None),
            *date_filter
        )
    )
    revenue_installed_result = await db.execute(revenue_installed_query)
    revenue_installed = float(revenue_installed_result.scalar() or 0)
    
    revenue_templated_query = select(func.sum(Fab.revenue)).where(
        and_(
            Fab.template_received == True,
            Fab.revenue.isnot(None),
            *date_filter
        )
    )
    revenue_templated_result = await db.execute(revenue_templated_query)
    revenue_templated = float(revenue_templated_result.scalar() or 0)
    
    gp_query = select(func.sum(Fab.gp)).where(
        and_(
            Fab.gp.isnot(None),
            *date_filter
        )
    )
    gp_result = await db.execute(gp_query)
    gross_profit = float(gp_result.scalar() or 0)
    
    # 7. Newly Assigned FABs (recent assignments)
    newly_assigned_query = select(
        Fab.id,
        Fab.fab_type,
        User.first_name,
        User.last_name,
        Fab.current_stage,
        BusinessJob.name.label("job_name"),
        Fab.created_at
    ).select_from(Fab)\
        .join(User, Fab.sales_person_id == User.id, isouter=True)\
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)\
        .where(Fab.drafter_id.isnot(None))\
        .order_by(Fab.drafter_assigned_at.desc())\
        .limit(10)
    
    newly_assigned_result = await db.execute(newly_assigned_query)
    newly_assigned_rows = newly_assigned_result.all()
    
    newly_assigned_fabs = [
        {
            "fab_id": row[0],
            "fab_type": row[1],
            "assigned_to": f"{row[2]} {row[3]}" if row[2] else "Unassigned",
            "stage": row[4],
            "job_name": row[5],
            "created_at": row[6].isoformat() if row[6] else None
        }
        for row in newly_assigned_rows
    ]
    
    # 8. Paused Jobs (on hold)
    paused_jobs_query = select(
        Fab.id,
        Fab.fab_type,
        Fab.current_stage,
        BusinessJob.name.label("job_name"),
        Fab.status_id
    ).select_from(Fab)\
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)\
        .where(
            and_(
                Fab.status_id == 0,  # On-hold status
                *date_filter
            )
        )\
        .order_by(Fab.updated_at.desc())\
        .limit(10)
    
    paused_result = await db.execute(paused_jobs_query)
    paused_rows = paused_result.all()
    
    paused_jobs = [
        {
            "fab_id": row[0],
            "fab_type": row[1],
            "stage": row[2],
            "job_name": row[3],
            "status": "On Hold"
        }
        for row in paused_rows
    ]
    
    # 9. Performance Overview - FABs completed per month (last 12 months)
    twelve_months_ago = end_date - timedelta(days=365)
    performance_query = select(
        func.date_trunc("month", Fab.created_at).label("month"),
        func.count(Fab.id).label("count")
    ).where(
        and_(
            Fab.current_stage == "install_completion",
            Fab.created_at >= twelve_months_ago
        )
    ).group_by(func.date_trunc("month", Fab.created_at))\
        .order_by(func.date_trunc("month", Fab.created_at))
    
    performance_result = await db.execute(performance_query)
    performance_rows = performance_result.all()
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    performance_data = [0] * 12  # Initialize with 0 for all months
    
    for row in performance_rows:
        if row[0]:
            month_index = row[0].month - 1
            performance_data[month_index] = row[1]
    
    # 10. Recent Jobs (latest FABs)
    recent_jobs_query = select(
        Fab.id,
        Fab.fab_type,
        Fab.created_at,
        BusinessJob.name.label("job_name"),
        BusinessJob.job_number,
        User.first_name,
        User.last_name,
        Fab.current_stage,
        Fab.status_id
    ).select_from(Fab)\
        .join(BusinessJob, Fab.job_id == BusinessJob.id, isouter=True)\
        .join(User, Fab.sales_person_id == User.id, isouter=True)\
        .order_by(Fab.created_at.desc())\
        .limit(5)
    
    recent_result = await db.execute(recent_jobs_query)
    recent_rows = recent_result.all()
    
    recent_jobs = [
        {
            "fab_id": row[0],
            "fab_type": row[1],
            "created_at": row[2].isoformat() if row[2] else None,
            "job_name": row[3],
            "job_number": row[4],
            "salesperson": f"{row[5]} {row[6]}" if row[5] else "Unassigned",
            "stage": row[7],
            "status": "Completed" if row[8] == 3 else "Active" if row[8] == 1 else "On Hold"
        }
        for row in recent_rows
    ]
    
    # Build response
    dashboard_data = {
        "kpis": {
            "total_fabs": total_fabs,
            "pending_installations": pending_installations,
            "average_revisions": round(float(avg_revisions), 2),
            "completion_rate": completion_rate
        },
        "overall_statistics": {
            "completed": status_breakdown["Completed"],
            "in_progress": status_breakdown["In Progress"],
            "paused": status_breakdown["Paused"],
            "total": total_fabs,
            "completion_percentage": completion_rate
        },
        "finance": {
            "revenue_installed": round(revenue_installed, 2),
            "revenue_templated": round(revenue_templated, 2),
            "gross_profit": round(gross_profit, 2)
        },
        "newly_assigned_fabs": newly_assigned_fabs,
        "paused_jobs": paused_jobs,
        "performance_overview": {
            "months": months,
            "data": performance_data
        },
        "recent_jobs": recent_jobs,
        "time_period": time_period
    }
    
    return success_response(dashboard_data, "Dashboard data retrieved successfully")