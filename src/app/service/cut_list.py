from typing import Optional
from sqlmodel import Session
from datetime import datetime
from src.app.database.cut_list import CutList
from src.app.service.background import send_email

class CutListService:

    def update_cut_list_details(self, cut_list_id: int, updated_by: int, no_of_piece: Optional[str] = None, total_sqft: Optional[str] = None, installation_date: Optional[datetime] = None, ln_ft_map: Optional[str] = None):
        cut_list = self.db.get(CutList, cut_list_id)
        if not cut_list:
            return None
        if no_of_piece is not None:
            cut_list.no_of_piece = no_of_piece
        if total_sqft is not None:
            cut_list.total_sqft = total_sqft
        if installation_date is not None:
            cut_list.installation_date = installation_date
        if ln_ft_map is not None:
            cut_list.Ln_ft_map = ln_ft_map
        cut_list.updated_at = datetime.now()
        cut_list.updated_by = updated_by
        self.db.commit()
        self.db.refresh(cut_list)
        # Audit trail
        try:
            self.db.execute(
                """
                INSERT INTO audit_trails (activity_message, user_id, activity_table_name, record_id, created_at)
                VALUES (:msg, :uid, :tbl, :rid, CURRENT_TIMESTAMP)
                """,
                {
                    "msg": f"Updated CutList {cut_list_id} details (no_of_piece, total_sqft, installation_date, Ln_ft_map)",
                    "uid": updated_by,
                    "tbl": "cut_list",
                    "rid": cut_list_id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return cut_list
    def __init__(self, db: Session):
        self.db = db

    def schedule_shop(self, cut_list_id: int, shop_schedule_date: datetime, updated_by: int):
        cut_list = self.db.get(CutList, cut_list_id)
        if not cut_list:
            return None
        cut_list.shop_schedule_date = shop_schedule_date
        cut_list.updated_at = datetime.now()
        cut_list.updated_by = updated_by
        self.db.commit()
        self.db.refresh(cut_list)
        # Notify project coordinator
        try:
            send_email(
                to_email="coordinator@example.com",  # Replace with actual email
                subject="Shop Scheduled",
                body=f"Shop scheduled for CutList {cut_list_id} on {shop_schedule_date}."
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
                    "msg": f"Scheduled shop for CutList {cut_list_id} on {shop_schedule_date}",
                    "uid": updated_by,
                    "tbl": "cut_list",
                    "rid": cut_list_id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return cut_list

    def confirm_cut_list(self, cut_list_id: int, updated_by: int):
        cut_list = self.db.get(CutList, cut_list_id)
        if not cut_list:
            return None
        cut_list.status_id = 2  # confirmed
        cut_list.updated_at = datetime.now()
        cut_list.updated_by = updated_by
        self.db.commit()
        self.db.refresh(cut_list)
        # Notify sales person and project manager
        try:
            send_email(
                to_email="sales@example.com",  # Replace with actual emails
                subject="Cut List Confirmed",
                body=f"CutList {cut_list_id} has been confirmed."
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
                    "msg": f"Confirmed CutList {cut_list_id}",
                    "uid": updated_by,
                    "tbl": "cut_list",
                    "rid": cut_list_id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return cut_list
