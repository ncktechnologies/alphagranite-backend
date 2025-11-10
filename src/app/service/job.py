from sqlmodel import Session
from typing import Optional, List
from src.app.database import job as job_models, fab as fab_models


class PropertyService:
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def is_name_unique(self, name: str, exclude_id: int = None) -> bool:
        query = self.db.query(self.model).filter(self.model.name == name)
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)
        return not self.db.query(query.exists()).scalar()

    def create_item(self, name: str, order: int = None, **kwargs):
        if not self.is_name_unique(name):
            return None
        # Get max order if not provided
        max_order = self.db.query(self.model).order_by(self.model.order.desc()).first()
        if order is None:
            order = (max_order.order + 1) if max_order else 1
        else:
            # Shift other items
            self.db.query(self.model).filter(self.model.order >= order).update({self.model.order: self.model.order + 1})
        item = self.model(name=name, order=order, **kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        # Notify super admin and save audit trail (sync call)
        from src.app.service.background import send_email, save_audit_trail
        # Example: send email to super admin (replace with actual admin email)
        try:
            send_email(
                to_email="admin@example.com",
                subject=f"New {self.model.__tablename__} item created",
                body=f"A new item '{name}' was created in {self.model.__tablename__} by user {kwargs.get('created_by', 'system')}."
            )
        except Exception:
            pass
        # Example: save audit trail (replace with actual user_id and details)
        try:
            # If you have an async event loop, you could run this as a background task
            # Here, just a placeholder for sync context
            self.db.execute(
                f"INSERT INTO audit_trails (activity_message, user_id, activity_table_name, record_id, created_at) VALUES (:msg, :uid, :tbl, :rid, CURRENT_TIMESTAMP)",
                {
                    "msg": f"Created {self.model.__tablename__} item '{name}'",
                    "uid": kwargs.get('created_by', 0),
                    "tbl": self.model.__tablename__,
                    "rid": item.id
                }
            )
            self.db.commit()
        except Exception:
            pass
        return item

    def update_item(self, item_id: int, new_name: str = None, new_order: int = None, **kwargs):
        item = self.db.get(self.model, item_id)
        if not item:
            return None
        if new_name and not self.is_name_unique(new_name, exclude_id=item_id):
            return None
        if new_order and new_order != item.order:
            # Shift orders
            if new_order > item.order:
                self.db.query(self.model).filter(self.model.order > item.order, self.model.order <= new_order).update({self.model.order: self.model.order - 1})
            else:
                self.db.query(self.model).filter(self.model.order < item.order, self.model.order >= new_order).update({self.model.order: self.model.order + 1})
            item.order = new_order
        if new_name:
            item.name = new_name
        for k, v in kwargs.items():
            setattr(item, k, v)
        self.db.commit()
        self.db.refresh(item)
        # TODO: Notify super admin, audit trail
        return item

    def delete_item(self, item_id: int):
        item = self.db.get(self.model, item_id)
        if not item:
            return False
        order = item.order
        self.db.delete(item)
        self.db.commit()
        # Reorder remaining
        self.db.query(self.model).filter(self.model.order > order).update({self.model.order: self.model.order - 1})
        self.db.commit()
        # TODO: Notify super admin, audit trail
        return True


class JobService:
    def create_job(self, job_data: dict, created_by: int):
        """
        Create a Job.
        Steps:
        - Input job name
        - Select account
        - Input job number
        - Save job details
        """
        job = job_models.Job(
            name=job_data["name"],
            account_id=job_data["account_id"],
            job_id=job_data["job_id"],
            created_by=created_by,
            status_id=job_data.get("status_id", 1),  # default status if not provided
            created_at=job_data.get("created_at"),
            updated_at=job_data.get("updated_at"),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    def __init__(self, db: Session):
        self.db = db

    def create_fabid(self, job_id: int, fab_data: dict, created_by: int) -> fab_models.Fab:
        """
        Create a FABID for a job. Only the project coordinator can create.
        Steps:
        - Select job (job_id)
        - Input fab details (fab type, stone type, color, thickness, area, edge, total sqft, notes)
        - Assign sales person
        - Select steps FABID will go through (template, drafting, slab smith, SCT, final programming)
        - Set status to 'Draft'
        """
        fab = fab_models.Fab(
            job_id=job_id,
            fab_type=fab_data["fab_type"],
            stone_type=fab_data["stone_type"],
            stone_color=fab_data["stone_color"],
            stone_thickness=fab_data["stone_thickness"],
            area=fab_data["area"],
            edge=fab_data["edge"],
            total_sqft=fab_data["total_sqft"],
            notes=fab_data.get("notes"),
            sales_person_id=fab_data["sales_person_id"],
            steps=fab_data["steps"],
            status="Draft",
            created_by=created_by
        )
        self.db.add(fab)
        self.db.commit()
        self.db.refresh(fab)
        return fab

    def update_fabid_before_templating(self, fab_id: int, update_data: dict, user_id: int) -> Optional[fab_models.Fab]:
        """
        Update FABID details before templating. Can be done by project coordinator or assigned sales person.
        Only allowed if status is 'Draft'.
        """
        fab = self.db.get(fab_models.Fab, fab_id)
        if not fab or fab.status != "Draft":
            return None
        # Only allow update if user is project coordinator or assigned sales person
        if user_id not in [fab.created_by, fab.sales_person_id]:
            return None
        for key, value in update_data.items():
            setattr(fab, key, value)
        self.db.commit()
        self.db.refresh(fab)
        return fab

    def set_fabid_status(self, fab_id: int, status: str) -> Optional[fab_models.Fab]:
        """
        Update FABID status (e.g., to 'Templating').
        """
        fab = self.db.get(fab_models.Fab, fab_id)
        if not fab:
            return None
        fab.status = status
        self.db.commit()
        self.db.refresh(fab)
        return fab
