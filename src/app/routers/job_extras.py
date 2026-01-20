import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as async_select
from pydantic import BaseModel

from src.app.database.fab import Fab
from src.app.database.job import Job
from src.app.database import get_db
from src.app.database.drafting import Drafting
from src.app.database.file import File  # ← Add this import
from src.app.interface.generated_schemas import (
    JobTechnicianWorkflow, FinalProgramming, CutList,
    WorkStation, SalesCT, SlabSmith,
)
from src.app.service.drafting import DraftingService
from src.app.service.templating import TemplatingService
from src.app.utils.helpers import success_response, error_response
from fastapi import APIRouter, Depends, Query, Form, UploadFile, File as FastAPIFile

router = APIRouter()

# Get the project root directory (where your app runs from)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Base URL for file access (update with your actual domain/IP)
BASE_URL = os.getenv("BASE_URL", "http://93.114.128.181:8000")


@router.get("/jobs-with-fabs")
def list_jobs_with_fabs(
    search: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = select(Job)
    if search:
        query = query.where(Job.name.ilike(f"%{search}%"))
    if account_id:
        query = query.where(Job.account_id == account_id)
    jobs = db.exec(query).all()
    result = []
    for job in jobs:
        fabs = db.exec(select(Fab).where(Fab.job_id == job.id)).all()
        result.append({"job": job, "fabs": fabs})
    return success_response(result, "Jobs with FABs retrieved successfully")


@router.post("/predraft/complete")
def set_predraft_completed(fab_id: int, completed: bool, notes: Optional[str] = None, db: Session = Depends(get_db), updated_by: int = 1):
    service = TemplatingService(db)
    result = service.set_predraft_completed(fab_id, completed, notes, updated_by)
    if not result:
        raise error_response("FAB not found", 404)
    return success_response(result, "Predraft completed successfully")

@router.post("/predraft/redraft")
def set_predraft_redraft(fab_id: int, redraft_notes: str, db: Session = Depends(get_db), updated_by: int = 1):
    service = TemplatingService(db)
    result = service.set_predraft_redraft(fab_id, redraft_notes, updated_by)
    if not result:
        raise error_response("Templating not found", 404)
    
    fab = db.get(Fab, fab_id)
    if not fab:
        raise error_response("FAB not found", 404)
    fab.state = "templating"
    fab.updated_at = datetime.now()
    fab.updated_by = updated_by
    db.commit()
    db.refresh(fab)
    return success_response({"templating": result, "fab": fab}, "Predraft set to redraft successfully")

class TechnicianClockInput(BaseModel):
    fab_id: int
    technician_id: int
    table_name: str
    started_at: str
    completed_at: str
    total_sqft_done: str
    notes: Optional[str] = None
    pause_reason: Optional[str] = None
    table_id: Optional[int] = None

@router.post("/technician/clock")
async def save_technician_clock(
    clock_data: TechnicianClockInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workflow = JobTechnicianWorkflow(
        fab_id=clock_data.fab_id,
        technician_id=clock_data.technician_id,
        table_name=clock_data.table_name,
        started_at=clock_data.started_at,
        completed_at=clock_data.completed_at,
        total_sqft_done=clock_data.total_sqft_done,
        notes=clock_data.notes,
        pause_reason=clock_data.pause_reason,
        table_id=clock_data.table_id,
        created_at=clock_data.started_at,
        created_by=current_user.id
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return success_response(workflow, "Technician clock saved successfully")

@router.put("/technician/clock/{workflow_id}")
def update_technician_clock(
    workflow_id: int,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    total_sqft_done: Optional[str] = None,
    notes: Optional[str] = None,
    pause_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    workflow = db.get(JobTechnicianWorkflow, workflow_id)
    if not workflow:
        raise error_response("Workflow not found", 404)
    if started_at:
        workflow.started_at = started_at
    if completed_at:
        workflow.completed_at = completed_at
    if total_sqft_done:
        workflow.total_sqft_done = total_sqft_done
    if notes:
        workflow.notes = notes
    if pause_reason:
        workflow.pause_reason = pause_reason
    workflow.created_by = updated_by
    db.commit()
    db.refresh(workflow)
    return success_response(workflow, "Technician clock updated successfully")

@router.delete("/technician/clock/{workflow_id}")
def delete_technician_clock(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.get(JobTechnicianWorkflow, workflow_id)
    if not workflow:
        raise error_response("Workflow not found", 404)
    db.delete(workflow)
    db.commit()
    return success_response(None, "Technician clock deleted successfully")

@router.get("/technician/clockwork")
def list_technician_clockwork(
    drafter_id: int,
    fab_id: int,
    table_name: str,
    db: Session = Depends(get_db)
):
    query = select(JobTechnicianWorkflow).where(
        JobTechnicianWorkflow.technician_id == drafter_id,
        JobTechnicianWorkflow.fab_id == fab_id,
        JobTechnicianWorkflow.table_name == table_name
    )
    result = db.exec(query).all()
    return success_response(result, "Technician clockwork retrieved successfully")

@router.get("/technician/clockwork-table-names")
def get_clockwork_table_names():
    tables = ["templatings", "draftings", "slab_smiths", "final_programmings"]
    return success_response(tables, "Clockwork table names retrieved successfully")

@router.post("/fab/{fab_id}/shop-schedule")
def add_update_shop_schedule(
    fab_id: int,
    shop_schedule_date: str = Form(...),
    move_to_final_programming: bool = Form(False),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    fab = db.get(Fab, fab_id)
    if not fab:
        raise error_response("FAB not found", 404)
    fab.shop_schedule_date = shop_schedule_date
    if move_to_final_programming:
        fab.state = "final_programming"
    fab.updated_at = datetime.now()
    fab.updated_by = updated_by
    db.commit()
    db.refresh(fab)
    return success_response(fab, "Shop schedule updated successfully")

@router.post("/finalprogramming/{fp_id}/files")
async def add_files_to_final_programming(
    fp_id: int, 
    files: List[UploadFile] = FastAPIFile(...), 
    db: AsyncSession = Depends(get_db)
):
    """Upload files to final programming, save to disk and database"""
    
    # Check if final programming exists
    result = await db.execute(async_select(FinalProgramming).where(FinalProgramming.id == fp_id))
    fp = result.scalar_one_or_none()
    
    if not fp:
        raise error_response("FinalProgramming not found", 404)
    
    uploaded_file_ids = []
    uploaded_files_info = []
    
    for file in files:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create full URL for the file
        file_url = f"{BASE_URL}/api/v1/files/download/{unique_filename}"
        
        # Create database record matching the actual files table schema
        file_record = File(
            name=file.filename,
            file_path=str(file_path),
            file_type=file.content_type,
            file_size=str(len(contents)),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(file_record)
        await db.flush()  # Get the ID without committing
        
        uploaded_file_ids.append(file_record.id)
        uploaded_files_info.append({
            "id": file_record.id,
            "filename": file.filename,
            "file_url": file_url,
            "size": len(contents),
            "mime_type": file.content_type,
            "uploaded_at": datetime.now().isoformat()
        })
    
    # Update fp.file_ids with new IDs
    existing_file_ids = fp.file_ids.split(",") if fp.file_ids else []
    existing_file_ids.extend([str(fid) for fid in uploaded_file_ids])
    fp.file_ids = ",".join(existing_file_ids)
    
    await db.commit()
    await db.refresh(fp)
    
    return success_response({
        "file_ids": uploaded_file_ids,
        "files": uploaded_files_info,
        "total_files": len(existing_file_ids)
    }, "Files uploaded successfully")


@router.delete("/finalprogramming/{fp_id}/files/{file_id}")
async def delete_file_from_final_programming(
    fp_id: int, 
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete file from final programming (soft delete in database)"""
    
    # Get final programming
    result = await db.execute(async_select(FinalProgramming).where(FinalProgramming.id == fp_id))
    fp = result.scalar_one_or_none()
    
    if not fp:
        raise error_response("FinalProgramming not found", 404)
    
    # Remove from fp.file_ids
    file_ids = fp.file_ids.split(",") if fp.file_ids else []
    file_id_str = str(file_id)
    
    if file_id_str not in file_ids:
        raise error_response("File not found in final programming", 404)
    
    file_ids.remove(file_id_str)
    fp.file_ids = ",".join(file_ids)
    
    # Soft delete the file record
    file_result = await db.execute(async_select(File).where(File.id == file_id))
    file_record = file_result.scalar_one_or_none()
    
    if file_record:
        file_record.deleted_at = datetime.now()
    
    await db.commit()
    await db.refresh(fp)
    
    return success_response({
        "file_ids": file_ids,
        "total_files": len(file_ids)
    }, "File deleted successfully")

@router.post("/finalprogramming/{fp_id}/update")
def update_final_programming(
    fp_id: int,
    note: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    fp = db.get(FinalProgramming, fp_id)
    if not fp:
        raise error_response("FinalProgramming not found", 404)
    if note:
        fp.note = note
    if status:
        fp.status = status
    fp.updated_at = datetime.now()
    fp.updated_by = updated_by
    db.commit()
    db.refresh(fp)
    return success_response(fp, "Final programming updated successfully")

@router.post("/cutlist/{cutlist_id}/update-details")
def update_cutlist_details(
    cutlist_id: int,
    no_of_pieces: int = Form(...),
    total_sqft: str = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    cutlist = db.get(CutList, cutlist_id)
    if not cutlist:
        raise error_response("CutList not found", 404)
    cutlist.no_of_pieces = no_of_pieces
    cutlist.total_sqft = total_sqft
    cutlist.updated_at = datetime.now()
    cutlist.updated_by = updated_by
    db.commit()
    db.refresh(cutlist)
    return success_response(cutlist, "Cutlist details updated successfully")

@router.post("/salesct/{sct_id}/review-no")
def set_sct_review_no(
    sct_id: int,
    revenue: float = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    sct = db.get(SalesCT, sct_id)
    if not sct:
        raise error_response("SalesCT not found", 404)
    sct.revenue = revenue
    sct.status_id = 2
    sct.review_needed = False
    sct.updated_at = datetime.now()
    sct.updated_by = updated_by
    db.commit()
    db.refresh(sct)
    return success_response(sct, "Sales CT review set to NO successfully")

@router.post("/salesct/{sct_id}/review-yes")
def set_sct_review_yes(
    sct_id: int,
    revision_reason: str = Form(...),
    files: Optional[List[UploadFile]] = None,
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    sct = db.get(SalesCT, sct_id)
    if not sct:
        raise error_response("SalesCT not found", 404)
    sct.review_needed = True
    sct.revision_reason = revision_reason
    file_ids = sct.file_ids.split(",") if sct.file_ids else []
    if files:
        new_file_ids = [f"file_{i+len(file_ids)+1}" for i, _ in enumerate(files)]
        file_ids.extend(new_file_ids)
    sct.file_ids = ",".join(file_ids)
    sct.updated_at = datetime.now()
    sct.updated_by = updated_by
    db.commit()
    db.refresh(sct)
    return success_response(sct, "Sales CT review set to YES successfully")

@router.post("/salesct/{sct_id}/revision-update")
def update_sct_revision(
    sct_id: int,
    revision_type: str = Form(...),
    revision_status: str = Form(...),
    draft_note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    sct = db.get(SalesCT, sct_id)
    if not sct:
        raise error_response("SalesCT not found", 404)
    if not hasattr(sct, "revision_history") or sct.revision_history is None:
        sct.revision_history = []
    sct.revision_history.append({
        "type": revision_type,
        "status": revision_status,
        "date": datetime.now().isoformat(),
        "note": draft_note
    })
    sct.revision_type = revision_type
    sct.revision_status = revision_status
    sct.draft_note = draft_note
    sct.updated_at = datetime.now()
    sct.updated_by = updated_by
    db.commit()
    db.refresh(sct)
    return success_response(sct, "Sales CT revision updated successfully")

@router.post("/slabsmith/{slabsmith_id}/complete")
def mark_slabsmith_completed(slabsmith_id: int, db: Session = Depends(get_db), updated_by: int = 1):
    slabsmith = db.get(SlabSmith, slabsmith_id)
    if not slabsmith:
        raise error_response("SlabSmith not found", 404)
    slabsmith.status_id = 2
    slabsmith.end_date = datetime.now()
    slabsmith.updated_at = datetime.now()
    slabsmith.updated_by = updated_by
    db.commit()
    db.refresh(slabsmith)
    return success_response(slabsmith, "SlabSmith marked as completed successfully")

@router.post("/slabsmith/{slabsmith_id}/files")
async def add_files_to_slabsmith(
    slabsmith_id: int, 
    files: List[UploadFile] = FastAPIFile(...), 
    db: AsyncSession = Depends(get_db)
):
    """Upload files to SlabSmith, save to disk and database"""
    
    # Check if slabsmith exists
    result = await db.execute(async_select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("SlabSmith not found", 404)
    
    uploaded_file_ids = []
    uploaded_files_info = []
    
    for file in files:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create full URL for the file
        file_url = f"{BASE_URL}/api/v1/files/download/{unique_filename}"
        
        # Create database record matching the actual files table schema
        file_record = File(
            name=file.filename,
            file_path=str(file_path),
            file_type=file.content_type,
            file_size=str(len(contents)),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(file_record)
        await db.flush()  # Get the ID without committing
        
        uploaded_file_ids.append(file_record.id)
        uploaded_files_info.append({
            "id": file_record.id,
            "filename": file.filename,
            "file_url": file_url,
            "size": len(contents),
            "mime_type": file.content_type,
            "uploaded_at": datetime.now().isoformat()
        })
    
    # Update slabsmith.file_ids with new IDs
    existing_file_ids = slabsmith.file_ids.split(",") if slabsmith.file_ids else []
    existing_file_ids.extend([str(fid) for fid in uploaded_file_ids])
    slabsmith.file_ids = ",".join(existing_file_ids)
    
    await db.commit()
    await db.refresh(slabsmith)
    
    return success_response({
        "file_ids": uploaded_file_ids,
        "files": uploaded_files_info,
        "total_files": len(existing_file_ids)
    }, "Files uploaded successfully")


@router.delete("/slabsmith/{slabsmith_id}/files/{file_id}")
async def delete_file_from_slabsmith(
    slabsmith_id: int, 
    file_id: int,  # Changed from str to int
    db: AsyncSession = Depends(get_db)
):
    """Delete file from SlabSmith (soft delete in database)"""
    
    # Get slabsmith
    result = await db.execute(async_select(SlabSmith).where(SlabSmith.id == slabsmith_id))
    slabsmith = result.scalar_one_or_none()
    
    if not slabsmith:
        raise error_response("SlabSmith not found", 404)
    
    # Remove from slabsmith.file_ids
    file_ids = slabsmith.file_ids.split(",") if slabsmith.file_ids else []
    file_id_str = str(file_id)
    
    if file_id_str not in file_ids:
        raise error_response("File not found in SlabSmith", 404)
    
    file_ids.remove(file_id_str)
    slabsmith.file_ids = ",".join(file_ids)
    
    # Soft delete the file record
    file_result = await db.execute(async_select(File).where(File.id == file_id))
    file_record = file_result.scalar_one_or_none()
    
    if file_record:
        file_record.deleted_at = datetime.now()
    
    await db.commit()
    await db.refresh(slabsmith)
    
    return success_response({
        "file_ids": file_ids,
        "total_files": len(file_ids)
    }, "File deleted successfully")

@router.post("/drafting/{drafting_id}/files")
async def add_files_to_drafting(
    drafting_id: int, 
    files: List[UploadFile] = FastAPIFile(...), 
    db: AsyncSession = Depends(get_db)
):
    """Upload files to drafting, save to disk and database"""
    
    # Check if drafting exists
    result = await db.execute(async_select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    uploaded_file_ids = []
    uploaded_files_info = []
    
    for file in files:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create full URL for the file
        file_url = f"{BASE_URL}/api/v1/files/download/{unique_filename}"
        
        # Create database record matching the actual files table schema
        file_record = File(
            name=file.filename,                      # ← Changed from filename
            file_path=str(file_path),
            file_type=file.content_type,             # ← Changed from mime_type
            file_size=str(len(contents)),            # ← Convert to string
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(file_record)
        await db.flush()  # Get the ID without committing
        
        uploaded_file_ids.append(file_record.id)
        uploaded_files_info.append({
            "id": file_record.id,
            "filename": file.filename,
            "file_url": file_url,
            "size": len(contents),
            "mime_type": file.content_type,
            "uploaded_at": datetime.now().isoformat()
        })
    
    # Update drafting.file_ids with new IDs
    existing_file_ids = drafting.file_ids.split(",") if drafting.file_ids else []
    existing_file_ids.extend([str(fid) for fid in uploaded_file_ids])
    drafting.file_ids = ",".join(existing_file_ids)
    
    await db.commit()
    await db.refresh(drafting)
    
    return success_response({
        "file_ids": uploaded_file_ids,
        "files": uploaded_files_info,
        "total_files": len(existing_file_ids)
    }, "Files uploaded successfully")


@router.delete("/drafting/{drafting_id}/files/{file_id}")
async def delete_file_from_drafting(
    drafting_id: int, 
    file_id: int,  # Changed from str to int
    db: AsyncSession = Depends(get_db)
):
    """Delete file from drafting (soft delete in database)"""
    
    # Get drafting
    result = await db.execute(async_select(Drafting).where(Drafting.id == drafting_id))
    drafting = result.scalar_one_or_none()
    
    if not drafting:
        raise error_response("Drafting not found", 404)
    
    # Remove from drafting.file_ids
    file_ids = drafting.file_ids.split(",") if drafting.file_ids else []
    file_id_str = str(file_id)
    
    if file_id_str not in file_ids:
        raise error_response("File not found in drafting", 404)
    
    file_ids.remove(file_id_str)
    drafting.file_ids = ",".join(file_ids)
    
    # Soft delete the file record
    file_result = await db.execute(async_select(File).where(File.id == file_id))
    file_record = file_result.scalar_one_or_none()
    
    if file_record:
        file_record.deleted_at = datetime.now()
    
    await db.commit()
    await db.refresh(drafting)
    
    return success_response({
        "file_ids": file_ids,
        "total_files": len(file_ids)
    }, "File deleted successfully")


@router.get("/files/download/{filename}")
async def download_file(
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """Download a file by filename"""
    from fastapi.responses import FileResponse
    
    file_path = UPLOAD_DIR / filename
    
    if not os.path.exists(file_path):
        raise error_response("File not found on disk", 404)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/files/{file_id}")
async def get_file_info(file_id: int, db: AsyncSession = Depends(get_db)):
    """Get file information by ID"""
    
    result = await db.execute(async_select(File).where(File.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise error_response("File not found", 404)
    
    # Generate download URL
    filename = os.path.basename(file_record.file_path)
    file_url = f"{BASE_URL}/api/v1/files/download/{filename}"
    
    return success_response({
        "id": file_record.id,
        "filename": file_record.name,              # ← Changed from filename
        "file_url": file_url,
        "file_size": file_record.file_size,
        "file_type": file_record.file_type,        # ← Changed from mime_type
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
        "updated_at": file_record.updated_at.isoformat() if file_record.updated_at else None
    }, "File info retrieved successfully")


@router.post("/drafting/{drafting_id}/submit-review")
def submit_draft_for_review(
    drafting_id: int,
    file_ids: str = Form(...),
    no_of_piece_drafted: int = Form(...),
    total_sqft_drafted: str = Form(...),
    draft_note: str = Form(...),
    mentions: str = Form(...),
    is_completed: bool = Form(...),
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    service = DraftingService(db)
    file_id_list = file_ids.split(",") if file_ids else []
    mention_list = [int(uid) for uid in mentions.split(",") if uid]
    result = service.submit_draft(
        drafting_id=drafting_id,
        file_ids=file_id_list,
        no_of_piece_drafted=no_of_piece_drafted,
        total_sqft_drafted=total_sqft_drafted,
        draft_note=draft_note,
        mentions=mention_list,
        is_completed=is_completed,
        updated_by=updated_by
    )
    return success_response(result, "Draft submitted for review successfully")

@router.post("/workstation", operation_id="create_workstation_job_extras")
def create_workstation(
    planning_section_id: int = Form(...),
    workstation_name: str = Form(...),
    status: str = Form(...),
    assigned_operatives: str = Form(...),
    machines: str = Form(...),
    machine_statuses: str = Form(...),
    db: Session = Depends(get_db),
    created_by: int = 1
):
    existing = db.exec(select(WorkStation).where(WorkStation.workstation_name == workstation_name)).first()
    if existing:
        raise error_response("Workstation name must be unique", 400)
    ws = WorkStation(
        planning_section_id=planning_section_id,
        workstation_name=workstation_name,
        status=status,
        assigned_operatives=assigned_operatives,
        machines=machines,
        machine_statuses=machine_statuses,
        created_by=created_by
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return success_response(ws, "Workstation created successfully")
