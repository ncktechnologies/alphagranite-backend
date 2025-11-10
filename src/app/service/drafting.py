from sqlmodel import Session
from typing import Optional, List
from datetime import datetime, timedelta
from src.app.service.background import send_email, save_audit_trail, send_notification
from src.app.interface.generated_schemas import Drafting

class DraftingService:
    def __init__(self, db: Session):
        self.db = db

    def auto_assign_drafter(self, fab_id: int, drafter_id: int, created_by: int) -> Drafting:
        due_date = datetime.now() + timedelta(days=2)
        drafting = Drafting(
            fab_id=fab_id,
            drafter_id=drafter_id,
            scheduled_start_date=datetime.now(),
            scheduled_end_date=due_date,
            status_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_by=created_by
        )
        self.db.add(drafting)
        self.db.commit()
        self.db.refresh(drafting)
        
        try:
            send_email(
                to_email="drafter@example.com",
                subject="New Drafting Assignment",
                body=f"You have been assigned to draft FABID {fab_id}. Due: {due_date}."
            )
        except Exception:
            pass
        
        try:
            save_audit_trail(
                db=self.db,
                activity="drafting_assigned",
                user_id=created_by,
                message=f"Assigned drafter {drafter_id} to FAB {fab_id}",
                activity_trace_id=drafting.id
            )
        except Exception:
            pass
        
        return drafting

    def submit_draft(self, drafting_id: int, file_ids: List[int], no_of_piece_drafted: int, total_sqft_drafted: str, draft_note: str, mentions: List[int], is_completed: bool, updated_by: int):
        drafting = self.db.get(Drafting, drafting_id)
        if not drafting:
            return None
        drafting.file_ids = ','.join(map(str, file_ids))
        drafting.no_of_piece_drafted = str(no_of_piece_drafted)
        drafting.total_sqft_drafted = total_sqft_drafted
        drafting.draft_note = draft_note
        drafting.mentions = ','.join(map(str, mentions))
        drafting.is_redrafting = False
        drafting.updated_at = datetime.now()
        drafting.updated_by = updated_by
        if is_completed:
            drafting.status_id = 2
        self.db.commit()
        self.db.refresh(drafting)
        
        try:
            send_email(
                to_email="coordinator@example.com",
                subject="Draft Submitted",
                body=f"Draft for FABID {drafting.fab_id} has been submitted."
            )
        except Exception:
            pass
        
        try:
            save_audit_trail(
                db=self.db,
                activity="draft_submitted",
                user_id=updated_by,
                message=f"Draft submitted for FAB {drafting.fab_id}",
                activity_trace_id=drafting.id
            )
        except Exception:
            pass
        
        return drafting

    def mark_redrafting_needed(self, drafting_id: int, note: str, updated_by: int):
        drafting = self.db.get(Drafting, drafting_id)
        if not drafting:
            return None
        drafting.is_redrafting = True
        drafting.draft_note = note
        drafting.updated_at = datetime.now()
        drafting.updated_by = updated_by
        self.db.commit()
        self.db.refresh(drafting)
        
        try:
            send_email(
                to_email="drafter@example.com",
                subject="Redrafting Needed",
                body=f"Redrafting is required for FABID {drafting.fab_id}. Note: {note}"
            )
        except Exception:
            pass
        
        try:
            save_audit_trail(
                db=self.db,
                activity="redrafting_needed",
                user_id=updated_by,
                message=f"Redrafting needed for FAB {drafting.fab_id}",
                activity_trace_id=drafting.id
            )
        except Exception:
            pass
        
        return drafting
