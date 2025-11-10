from typing import Optional
from datetime import datetime
from sqlmodel import Session, select
from src.app.service.background import send_email
from src.app.database.templating import Templating
from src.app.database import fab as fab_models, job as job_models

class TemplatingService:
    def mark_templated_received_and_move_to_predraft(self, fab_id: int, updated_by: int):
        templating = self.db.exec(
            select(Templating).where(Templating.fab_id == fab_id)
        ).first()
        if not templating:
            return None
        templating.is_templating_received = True
        templating.updated_at = datetime.now()
        templating.updated_by = updated_by
        # Move FAB to predraft review state
        fab = self.db.exec(
            select(fab_models.Fab).where(fab_models.Fab.id == fab_id)
        ).first()
        if fab:
            fab.curremt_stage = "pre_draft_review"
            fab.updated_at = datetime.now()
            fab.updated_by = updated_by
            self.db.add(fab)
        self.db.add(templating)
        self.db.commit()
        self.db.refresh(templating)
        return templating

    def set_predraft_completed(self, fab_id: int, completed: bool, notes: Optional[str], updated_by: int):
        fab = self.db.exec(
            select(fab_models.Fab).where(fab_models.Fab.id == fab_id)
        ).first()
        if not fab:
            return None
        if completed:
            fab.curremt_stage = "drafting"
        else:
            fab.curremt_stage = "pre_draft_review"
        fab.updated_at = datetime.now()
        fab.updated_by = updated_by
        if notes:
            fab.notes = notes
        self.db.add(fab)
        self.db.commit()
        self.db.refresh(fab)
        return fab

    def set_predraft_redraft(self, fab_id: int, redraft_notes: str, updated_by: int):
        templating = self.db.exec(
            select(Templating).where(Templating.fab_id == fab_id)
        ).first()
        if not templating:
            return None
        templating.is_redrafting = True
        templating.redraft_notes = redraft_notes
        templating.updated_at = datetime.now()
        templating.updated_by = updated_by
        self.db.add(templating)
        self.db.commit()
        self.db.refresh(templating)
        return templating
    def __init__(self, db: Session):
        self.db = db

    def schedule_template(self, fab_id: int, technician_id: int, schedule_start_date: datetime, schedule_due_date: datetime, total_sqft: str, notes: Optional[str], created_by: int):
        # Create templating record
        templating = Templating(
            fab_id=fab_id,
            is_templating_schedule=True,
            schedule_start_date=schedule_start_date,
            schedule_due_date=schedule_due_date,
            technician_id=technician_id,
            total_sqft=total_sqft,
            status_id=1,  # e.g. scheduled
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_by=created_by,
            notes=notes
        )
        self.db.add(templating)
        self.db.commit()
        self.db.refresh(templating)
        # Notify technician
        try:
            send_email(
                to_email="technician@example.com",  # Replace with actual technician email
                subject="New Templating Assignment",
                body=f"You have been assigned to template FABID {fab_id} starting {schedule_start_date}."
            )
        except Exception:
            pass
        # TODO: Audit trail
        return templating

    def mark_template_received(self, templating_id: int, updated_by: int):
        templating = self.db.get(Templating, templating_id)
        if not templating:
            return None
        templating.is_templating_received = True
        templating.updated_at = datetime.now()
        templating.updated_by = updated_by
        self.db.commit()
        self.db.refresh(templating)
        # Notify project coordinator
        try:
            send_email(
                to_email="coordinator@example.com",  # Replace with actual coordinator email
                subject="Template Received",
                body=f"Template for FABID {templating.fab_id} has been received."
            )
        except Exception:
            pass
        # TODO: Audit trail
        return templating

    def reschedule_template(self, templating_id: int, new_technician_id: int, new_start: datetime, new_due: datetime, updated_by: int):
        templating = self.db.get(Templating, templating_id)
        if not templating:
            return None
        templating.technician_id = new_technician_id
        templating.schedule_start_date = new_start
        templating.schedule_due_date = new_due
        templating.updated_at = datetime.now()
        templating.updated_by = updated_by
        self.db.commit()
        self.db.refresh(templating)
        # Notify new technician
        try:
            send_email(
                to_email="technician@example.com",  # Replace with actual technician email
                subject="Templating Reassigned",
                body=f"You have been reassigned to template FABID {templating.fab_id} starting {new_start}."
            )
        except Exception:
            pass
        # TODO: Audit trail
        return templating
