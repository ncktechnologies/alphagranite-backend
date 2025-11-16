from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from src.app.database import get_db
from src.app.database.user import User
from src.app.database.fab import Fab
from src.app.database.templating import Templating
from src.app.database.drafting import Drafting
from src.app.database.slab_smith import SlabSmith
from src.app.database.sales_ct import SalesCT
from src.app.database.stone_type import StoneType
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.edge import Edge
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.get("/fab/{fab_id}/details", response_model=SuccessResponse[dict])
async def get_fab_detail_by_stage(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Display a fab's details based on the status and stage it is in.
    Returns fab info plus relevant stage-specific data (templating, drafting, etc.)
    """
    
    # Get fab
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = fab_result.scalar_one_or_none()
    
    if not fab:
        raise error_response("Fab not found", 404)
    
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
    
    # Base fab data
    fab_data = {
        "id": fab.id,
        "job_id": fab.job_id,
        "fab_type": fab.fab_type,
        "sales_person_id": fab.sales_person_id,
        "sales_person_name": sales_person_obj.username if sales_person_obj else None,
        "stone_type_id": fab.stone_type_id,
        "stone_type_name": stone_type_obj.name if stone_type_obj else None,
        "stone_color_id": fab.stone_color_id,
        "stone_color_name": stone_color_obj.name if stone_color_obj else None,
        "stone_thickness_id": fab.stone_thickness_id,
        "stone_thickness_value": stone_thickness_obj.thickness if stone_thickness_obj else None,
        "edge_id": fab.edge_id,
        "edge_name": edge_obj.name if edge_obj else None,
        "input_area": fab.input_area,
        "total_sqft": fab.total_sqft,
        "notes": fab.notes,
        "template_needed": fab.template_needed,
        "drafting_needed": fab.drafting_needed,
        "slab_smith_cust_needed": fab.slab_smith_cust_needed,
        "slab_smith_ag_needed": fab.slab_smith_ag_needed,
        "sct_needed": fab.sct_needed,
        "final_programming_needed": fab.final_programming_needed,
        "current_stage": fab.current_stage,
        "status_id": fab.status_id,
        "created_at": fab.created_at,
        "created_by": fab.created_by,
        "updated_at": fab.updated_at,
        "updated_by": fab.updated_by,
    }
    
    # Add stage-specific data based on current_stage
    stage_data = None
    
    if fab.current_stage == "templatings":
        templating_result = await db.execute(select(Templating).where(Templating.fab_id == fab_id))
        templating = templating_result.scalar_one_or_none()
        if templating:
            stage_data = {
                "type": "templating",
                "id": templating.id,
                "technician_id": templating.technician_id,
                "schedule_start_date": templating.schedule_start_date,
                "schedule_due_date": templating.schedule_due_date,
                "total_sqft": templating.total_sqft,
                "notes": templating.notes,
                "is_templating_schedule": templating.is_templating_schedule,
                "status_id": templating.status_id,
                "created_at": templating.created_at,
                "updated_at": templating.updated_at,
            }
    
    elif fab.current_stage == "draftings":
        drafting_result = await db.execute(select(Drafting).where(Drafting.fab_id == fab_id))
        drafting = drafting_result.scalar_one_or_none()
        if drafting:
            stage_data = {
                "type": "drafting",
                "id": drafting.id,
                "drafter_id": drafting.drafter_id,
                "scheduled_start_date": drafting.scheduled_start_date,
                "scheduled_end_date": drafting.scheduled_end_date,
                "drafter_start_date": drafting.drafter_start_date,
                "drafter_end_date": drafting.drafter_end_date,
                "total_sqft_required_to_draft": drafting.total_sqft_required_to_draft,
                "total_sqft_drafted": drafting.total_sqft_drafted,
                "no_of_piece_drafted": drafting.no_of_piece_drafted,
                "draft_note": drafting.draft_note,
                "mentions": drafting.mentions,
                "file_ids": drafting.file_ids,
                "is_redrafting": drafting.is_redrafting,
                "status_id": drafting.status_id,
                "created_at": drafting.created_at,
                "updated_at": drafting.updated_at,
            }
    
    elif fab.current_stage == "slab_smiths":
        slabsmith_result = await db.execute(select(SlabSmith).where(SlabSmith.fab_id == fab_id))
        slabsmith = slabsmith_result.scalar_one_or_none()
        if slabsmith:
            stage_data = {
                "type": "slab_smith",
                "id": slabsmith.id,
                "slab_smith_type": slabsmith.slab_smith_type,
                "drafter_id": slabsmith.drafter_id,
                "start_date": slabsmith.start_date,
                "end_date": slabsmith.end_date,
                "total_sqft_completed": slabsmith.total_sqft_completed,
                "file_ids": slabsmith.file_ids,
                "status_id": slabsmith.status_id,
                "created_at": slabsmith.created_at,
                "updated_at": slabsmith.updated_at,
            }
    
    elif fab.current_stage == "sales_cts":
        sales_ct_result = await db.execute(select(SalesCT).where(SalesCT.fab_id == fab_id))
        sales_ct = sales_ct_result.scalar_one_or_none()
        if sales_ct:
            stage_data = {
                "type": "sales_ct",
                "id": sales_ct.id,
                "is_revision_needed": sales_ct.is_revision_needed,
                "is_revision_completed": sales_ct.is_revision_completed,
                "no_of_revisions": sales_ct.no_of_revisions,
                "current_revision_count": sales_ct.current_revision_count,
                "status_id": sales_ct.status_id,
                "created_at": sales_ct.created_at,
                "updated_at": sales_ct.updated_at,
            }
    
    fab_data["stage_data"] = stage_data
    
    return success_response(fab_data, "Fab details fetched successfully")
