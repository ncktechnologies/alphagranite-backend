from sqlmodel import Session
from datetime import datetime
from typing import Optional, List
from src.app.database.slab_smith import SlabSmith
from src.app.service.background import send_email

class SlabSmithService:
    def __init__(self, db: Session):
        self.db = db

    def start_slab_smith(self, fab_id: int, drafter_id: int, slab_smith_type: str, created_by: int) -> SlabSmith:
        slab_smith = SlabSmith(
            fab_id=fab_id,
            drafter_id=drafter_id,
            slab_smith_type=slab_smith_type,
            status_id=1,  # started
            start_date=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_by=created_by
        )
        self.db.add(slab_smith)
        self.db.commit()
        self.db.refresh(slab_smith)
        # Notify drafter
        try:
            send_email(
                to_email="drafter@example.com",  # Replace with actual drafter email
                subject="SlabSmith Started",
                body=f"SlabSmith ({slab_smith_type}) started for FABID {fab_id}."
            )
        except Exception:
            pass
        # TODO: Audit trail
        return slab_smith

    def update_progress(self, slab_smith_id: int, total_sqft_completed: str, file_ids: List[int], note: Optional[str], updated_by: int):
        slab_smith = self.db.get(SlabSmith, slab_smith_id)
        if not slab_smith:
            return None
        slab_smith.total_sqft_completed = total_sqft_completed
        slab_smith.file_ids = ','.join(map(str, file_ids))
        slab_smith.updated_at = datetime.now()
        slab_smith.updated_by = updated_by
        if note:
            slab_smith.note = note
        self.db.commit()
        self.db.refresh(slab_smith)
        return slab_smith

    def complete_slab_smith(self, slab_smith_id: int, updated_by: int):
        slab_smith = self.db.get(SlabSmith, slab_smith_id)
        if not slab_smith:
            return None
        slab_smith.status_id = 2  # completed
        slab_smith.end_date = datetime.now()
        slab_smith.updated_at = datetime.now()
        slab_smith.updated_by = updated_by
        self.db.commit()
        self.db.refresh(slab_smith)
        # Notify project coordinator and sales person
        try:
            send_email(
                to_email="coordinator@example.com",  # Replace with actual emails
                subject="SlabSmith Completed",
                body=f"SlabSmith for FABID {slab_smith.fab_id} has been completed."
            )
        except Exception:
            pass
        # TODO: Audit trail
        return slab_smith
