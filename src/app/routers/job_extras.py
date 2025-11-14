from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from src.app.utils.config import get_db
from src.app.service.job import JobService
from src.app.database.templating import Templating
from src.app.interface.generated_schemas import (
    JobTechnicianWorkflow, FinalProgramming, CutList,
    WorkStation, SalesCT, SlabSmith, Drafting, PlanningSection,
)
from src.app.service.drafting import DraftingService
from src.app.service.templating import TemplatingService
from src.app.utils.helpers import success_response, error_response
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File as FastAPIFile

router = APIRouter()

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

@router.post("/templating/schedule")
def schedule_templating(
    fab_id: int,
    technician_id: int,
    schedule_start_date: str,
    schedule_due_date: str,
    total_sqft: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    created_by: int = 1
):
    service = TemplatingService(db)
    result = service.schedule_template(
        fab_id=fab_id,
        technician_id=technician_id,
        schedule_start_date=schedule_start_date,
        schedule_due_date=schedule_due_date,
        total_sqft=total_sqft,
        notes=notes,
        created_by=created_by
    )
    return success_response(result, "Templating scheduled successfully")

@router.post("/templating/unschedule")
def unschedule_templating(
    templating_id: int,
    db: Session = Depends(get_db),
    updated_by: int = 1
):
    templating = db.get(Templating, templating_id)
    if not templating:
        raise error_response("Templating not found", 404)
    templating.is_templating_schedule = False
    templating.updated_by = updated_by
    db.commit()
    db.refresh(templating)
    return success_response(templating, "Templating unscheduled successfully")

@router.post("/templating/mark-received")
def mark_templated_received(fab_id: int, db: Session = Depends(get_db), updated_by: int = 1):
    service = TemplatingService(db)
    result = service.mark_templated_received_and_move_to_predraft(fab_id, updated_by)
    if not result:
        raise error_response("Templating or FAB not found", 404)
    return success_response(result, "Templating marked as received successfully")

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

@router.post("/technician/clock")
def save_technician_clock(
    fab_id: int,
    technician_id: int,
    table_name: str,
    started_at: str,
    completed_at: str,
    total_sqft_done: str,
    notes: Optional[str] = None,
    pause_reason: Optional[str] = None,
    table_id: int = None,
    db: Session = Depends(get_db),
    created_by: int = 1
):
    workflow = JobTechnicianWorkflow(
        fab_id=fab_id,
        technician_id=technician_id,
        table_name=table_name,
        started_at=started_at,
        completed_at=completed_at,
        total_sqft_done=total_sqft_done,
        notes=notes,
        pause_reason=pause_reason,
        table_id=table_id,
        created_at=started_at,
        created_by=created_by
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
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
def add_files_to_final_programming(fp_id: int, files: List[UploadFile] = FastAPIFile(...), db: Session = Depends(get_db)):
    fp = db.get(FinalProgramming, fp_id)
    if not fp:
        raise error_response("FinalProgramming not found", 404)
    file_ids = fp.file_ids.split(",") if fp.file_ids else []
    new_file_ids = [f"file_{i+len(file_ids)+1}" for i, _ in enumerate(files)]
    file_ids.extend(new_file_ids)
    fp.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(fp)
    return success_response({"file_ids": file_ids}, "Files added successfully")

@router.delete("/finalprogramming/{fp_id}/files/{file_id}")
def delete_file_from_final_programming(fp_id: int, file_id: str, db: Session = Depends(get_db)):
    fp = db.get(FinalProgramming, fp_id)
    if not fp:
        raise error_response("FinalProgramming not found", 404)
    file_ids = fp.file_ids.split(",") if fp.file_ids else []
    if file_id not in file_ids:
        raise error_response("File not found in final programming", 404)
    file_ids.remove(file_id)
    fp.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(fp)
    return success_response({"file_ids": file_ids}, "File deleted successfully")

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
def add_files_to_slabsmith(slabsmith_id: int, files: List[UploadFile] = FastAPIFile(...), db: Session = Depends(get_db)):
    slabsmith = db.get(SlabSmith, slabsmith_id)
    if not slabsmith:
        raise error_response("SlabSmith not found", 404)
    file_ids = slabsmith.file_ids.split(",") if slabsmith.file_ids else []
    new_file_ids = [f"file_{i+len(file_ids)+1}" for i, _ in enumerate(files)]
    file_ids.extend(new_file_ids)
    slabsmith.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(slabsmith)
    return success_response({"file_ids": file_ids}, "Files added to SlabSmith successfully")

@router.delete("/slabsmith/{slabsmith_id}/files/{file_id}")
def delete_file_from_slabsmith(slabsmith_id: int, file_id: str, db: Session = Depends(get_db)):
    slabsmith = db.get(SlabSmith, slabsmith_id)
    if not slabsmith:
        raise error_response("SlabSmith not found", 404)
    file_ids = slabsmith.file_ids.split(",") if slabsmith.file_ids else []
    if file_id not in file_ids:
        raise error_response("File not found in slabsmith", 404)
    file_ids.remove(file_id)
    slabsmith.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(slabsmith)
    return success_response({"file_ids": file_ids}, "File deleted from SlabSmith successfully")

@router.post("/drafting/{drafting_id}/files")
def add_files_to_drafting(drafting_id: int, files: List[UploadFile] = FastAPIFile(...), db: Session = Depends(get_db)):
    drafting = db.get(Drafting, drafting_id)
    if not drafting:
        raise error_response("Drafting not found", 404)
    file_ids = drafting.file_ids.split(",") if drafting.file_ids else []
    new_file_ids = [f"file_{i+len(file_ids)+1}" for i, _ in enumerate(files)]
    file_ids.extend(new_file_ids)
    drafting.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(drafting)
    return success_response({"file_ids": file_ids}, "Files added to drafting successfully")

@router.delete("/drafting/{drafting_id}/files/{file_id}")
def delete_file_from_drafting(drafting_id: int, file_id: str, db: Session = Depends(get_db)):
    drafting = db.get(Drafting, drafting_id)
    if not drafting:
        raise error_response("Drafting not found", 404)
    file_ids = drafting.file_ids.split(",") if drafting.file_ids else []
    if file_id not in file_ids:
        raise error_response("File not found in drafting", 404)
    file_ids.remove(file_id)
    drafting.file_ids = ",".join(file_ids)
    db.commit()
    db.refresh(drafting)
    return success_response({"file_ids": file_ids}, "File deleted from drafting successfully")

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
