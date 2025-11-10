from sqlmodel import Session
from datetime import datetime
from typing import Optional, List
from src.app.database.sales_ct import SalesCT
from src.app.service.background import send_email
from src.app.database.sct_revision_queue import SCTRevisionQueue

class SalesCTService:
    def __init__(self, db: Session):
        self.db = db

    def start_sales_ct(self, fab_id: int, created_by: int) -> SalesCT:
        sales_ct = SalesCT(
            fab_id=fab_id,
            is_revision_needed=False,
            status_id=1,  # started
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_by=created_by
        )
        self.db.add(sales_ct)
        self.db.commit()
        self.db.refresh(sales_ct)
        return sales_ct

    def mark_revision_needed(self, sales_ct_id: int, revision_reason: str, file_ids: List[int], drafter_id: int, created_by: int) -> SCTRevisionQueue:
        revision = SCTRevisionQueue(
            sales_cts_id=sales_ct_id,
            revision_type="manual",  # or other type
            status_id=1,  # started
            draftings_id=drafter_id,
            file_ids=','.join(map(str, file_ids)),
            revision_number=1,  # increment as needed
            created_at=datetime.now(),
            start_date=datetime.now(),
            revision_reason=revision_reason,
            updated_by=created_by
        )
        self.db.add(revision)
        self.db.commit()
        self.db.refresh(revision)
        # Notify project coordinator and drafter
        try:
            send_email(
                to_email="coordinator@example.com",  # Replace with actual emails
                subject="SCT Revision Needed",
                body=f"A revision is needed for SalesCT {sales_ct_id}. Reason: {revision_reason}"
            )
        except Exception:
            pass
        # Audit trail
        try:
            self.db.execute(
                """
                INSERT INTO audit_trails (activity_message, user_id, activity_table_name, record_id, created_at)
                VALUES (:msg, :uid, :tbl, :rid, CURRENT_TIMESTAMP)
                """,
                {
                    "msg": f"Created SCT revision for SalesCT {sales_ct_id} (reason: {revision_reason})",
                    "uid": created_by,
                    "tbl": "sct_revision_queue",
                    "rid": revision.id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return revision

    def complete_revision(self, revision_id: int, note: str, updated_by: int):
        revision = self.db.get(SCTRevisionQueue, revision_id)
        if not revision:
            return None
        revision.status_id = 2  # completed
        revision.end_date = datetime.now()
        revision.updated_at = datetime.now()
        revision.revision_reason = note
        revision.updated_by = updated_by
        self.db.commit()
        self.db.refresh(revision)
        # Notify project coordinator and sales person
        try:
            send_email(
                to_email="coordinator@example.com",  # Replace with actual emails
                subject="SCT Revision Completed",
                body=f"Revision {revision_id} for SalesCT {revision.sales_cts_id} has been completed."
            )
        except Exception:
            pass
        # Audit trail
        try:
            self.db.execute(
                """
                INSERT INTO audit_trails (activity_message, user_id, activity_table_name, record_id, created_at)
                VALUES (:msg, :uid, :tbl, :rid, CURRENT_TIMESTAMP)
                """,
                {
                    "msg": f"Completed SCT revision {revision_id} for SalesCT {revision.sales_cts_id}",
                    "uid": updated_by,
                    "tbl": "sct_revision_queue",
                    "rid": revision_id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return revision
