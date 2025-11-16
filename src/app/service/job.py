from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from datetime import datetime
from sqlmodel import Session, select, func, and_, or_
from fastapi import HTTPException, status

from src.app.database.job import (
    Job, JobCreate, JobUpdate, JobRead, 
    JobApplication, JobApplicationCreate, JobApplicationUpdate,
    JobStatus, ApplicationStatus, JobType, ExperienceLevel
)
from src.app.database import fab as fab_models
from src.app.database.user import User

T = TypeVar('T')

class PropertyService(Generic[T]):
    """
    Generic service for managing properties with ordering and audit trail support.
    """
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def is_name_unique(self, name: str, exclude_id: int = None) -> bool:
        query = self.db.query(self.model).filter(self.model.name == name)
        if exclude_id is not None:
            query = query.filter(self.model.id != exclude_id)
        return not self.db.query(query.exists()).scalar()

    def create_item(self, name: str, order: int = None, **kwargs) -> Optional[T]:
        """Create a new property item with ordering support."""
        if not self.is_name_unique(name):
            return None
            
        # Get max order if not provided
        max_order = self.db.query(self.model).order_by(self.model.order.desc()).first()
        if order is None:
            order = (max_order.order + 1) if max_order else 1
        else:
            # Shift other items
            self.db.query(self.model).filter(self.model.order >= order).update(
                {self.model.order: self.model.order + 1}
            )
            
        item = self.model(name=name, order=order, **kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        self._notify_and_audit("create", item, name, **kwargs)
        return item

    def update_item(self, item_id: int, new_name: str = None, new_order: int = None, **kwargs) -> Optional[T]:
        """Update an existing property item."""
        item = self.db.get(self.model, item_id)
        if not item:
            return None
            
        if new_name and not self.is_name_unique(new_name, exclude_id=item_id):
            return None
            
        if new_order is not None and new_order != item.order:
            self._reorder_items(item, new_order)
            item.order = new_order
            
        if new_name:
            item.name = new_name
            
        for k, v in kwargs.items():
            setattr(item, k, v)
            
        self.db.commit()
        self.db.refresh(item)
        self._notify_and_audit("update", item, item.name, **kwargs)
        return item

    def delete_item(self, item_id: int) -> bool:
        """Delete a property item and reorder remaining items."""
        item = self.db.get(self.model, item_id)
        if not item:
            return False
            
        order = item.order
        self.db.delete(item)
        self.db.commit()
        
        # Reorder remaining items
        self.db.query(self.model).filter(self.model.order > order).update(
            {self.model.order: self.model.order - 1}
        )
        self.db.commit()
        
        self._notify_and_audit("delete", item, item.name)
        return True

    def _reorder_items(self, item: T, new_order: int) -> None:
        """Internal method to handle item reordering."""
        if new_order > item.order:
            self.db.query(self.model).filter(
                self.model.order > item.order, 
                self.model.order <= new_order
            ).update({self.model.order: self.model.order - 1})
        else:
            self.db.query(self.model).filter(
                self.model.order < item.order, 
                self.model.order >= new_order
            ).update({self.model.order: self.model.order + 1})

    def _notify_and_audit(self, action: str, item: T, name: str, **kwargs) -> None:
        """Handle notifications and audit trail for item changes."""
        try:
            from src.app.service.background import send_email, save_audit_trail
            
            # Send email notification
            send_email(
                to_email="admin@example.com",
                subject=f"{action.capitalize()} {self.model.__tablename__} item",
                body=f"Item '{name}' was {action}d in {self.model.__tablename__} by user {kwargs.get('created_by', 'system')}."
            )
            
            # Save audit trail
            self.db.execute(
                """
                INSERT INTO audit_trails 
                (activity_message, user_id, activity_table_name, record_id, created_at) 
                VALUES (:msg, :uid, :tbl, :rid, CURRENT_TIMESTAMP)
                """,
                {
                    "msg": f"{action.capitalize()}d {self.model.__tablename__} item '{name}'",
                    "uid": kwargs.get('created_by', 0),
                    "tbl": self.model.__tablename__,
                    "rid": item.id
                }
            )
            self.db.commit()
        except Exception:
            # Fail silently for notifications and audit
            pass


class JobService:
    """
    Service for managing jobs, FABs, and related operations.
    Combines functionality from the original job.py and job_service.py files.
    """
    
    def __init__(self, db: Session):
        self.db = db

    # --- Core Job Methods ---
    def create_job(self, job_data: dict, user: User) -> Job:
        """
        Create a new job posting with validation and default values.
        """
        # Validate salary range if provided
        if job_data.get('salary_min') and job_data.get('salary_max'):
            if job_data['salary_min'] > job_data['salary_max']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Minimum salary cannot be greater than maximum salary"
                )
        
        # Create job with default values if not provided
        job = Job(
            **job_data,
            company_id=user.company_id,
            created_by=user.id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        return job

    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a job by ID"""
        return self.db.get(Job, job_id)
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        experience_level: Optional[ExperienceLevel] = None,
        is_remote: Optional[bool] = None,
        company_id: Optional[int] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """
        List jobs with advanced filtering and search capabilities.
        """
        query = select(Job)
        
        # Apply filters
        if status:
            query = query.where(Job.status == status)
        if job_type:
            query = query.where(Job.job_type == job_type)
        if experience_level:
            query = query.where(Job.experience_level == experience_level)
        if is_remote is not None:
            query = query.where(Job.is_remote == is_remote)
        if company_id:
            query = query.where(Job.company_id == company_id)
        if created_by:
            query = query.where(Job.created_by == created_by)
        if search:
            search = f"%{search}%"
            query = query.where(
                or_(
                    Job.title.ilike(search),
                    Job.description.ilike(search),
                    Job.requirements.ilike(search),
                    Job.responsibilities.ilike(search)
                )
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def update_job(self, job_id: int, job_update: JobUpdate, user: User) -> Optional[Job]:
        """
        Update an existing job posting with permission checks.
        """
        job = self.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        # Check permissions
        if job.created_by != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this job"
            )
        
        # Update job fields
        update_data = job_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
            
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def delete_job(self, job_id: int, user: User) -> bool:
        """
        Delete a job posting with permission checks.
        """
        job = self.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        # Check permissions
        if job.created_by != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this job"
            )
            
        self.db.delete(job)
        self.db.commit()
        return True

    # --- FAB (Fabrication) Methods ---
    def create_fabid(self, job_id: int, fab_data: dict, created_by: int) -> fab_models.Fab:
        """
        Create a FABID for a job.
        Only the project coordinator can create.
        """
        # Verify job exists
        job = self.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
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
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(fab)
        self.db.commit()
        self.db.refresh(fab)
        return fab

    def update_fabid_before_templating(self, fab_id: int, update_data: dict, user_id: int) -> Optional[fab_models.Fab]:
        """
        Update FABID details before templating.
        Can be done by project coordinator or assigned sales person.
        Only allowed if status is 'Draft'.
        """
        fab = self.db.get(fab_models.Fab, fab_id)
        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAB not found"
            )
            
        if fab.status != "Draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update FABs in Draft status"
            )
            
        # Only allow update if user is project coordinator or assigned sales person
        if user_id not in [fab.created_by, fab.sales_person_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this FAB"
            )
            
        for key, value in update_data.items():
            setattr(fab, key, value)
            
        fab.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(fab)
        return fab

    def set_fabid_status(self, fab_id: int, status: str, user_id: int) -> Optional[fab_models.Fab]:
        """
        Update FABID status (e.g., to 'Templating').
        Includes permission checks.
        """
        fab = self.db.get(fab_models.Fab, fab_id)
        if not fab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAB not found"
            )
            
        # Check if user has permission to update status
        if user_id not in [fab.created_by, fab.sales_person_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this FAB's status"
            )
            
        fab.status = status
        fab.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(fab)
        return fab

    # --- Job Application Methods ---
    def apply_for_job(self, job_id: int, application_data: dict, user: User) -> JobApplication:
        """
        Apply for a job with validation and status tracking.
        """
        # Check if job exists and is open for applications
        job = self.db.exec(
            select(Job).where(
                Job.id == job_id,
                Job.status == JobStatus.PUBLISHED,
                or_(
                    Job.application_deadline.is_(None),
                    Job.application_deadline >= datetime.utcnow()
                )
            )
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is not available for applications"
            )
            
        # Check for existing application
        existing_application = self.db.exec(
            select(JobApplication).where(
                (JobApplication.job_id == job_id) & 
                (JobApplication.applicant_id == user.id)
            )
        ).first()
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied to this job"
            )
        
        # Create application
        application = JobApplication(
            **application_data,
            job_id=job_id,
            applicant_id=user.id,
            status=ApplicationStatus.APPLIED,
            applied_at=datetime.utcnow()
        )
        
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        
        return application

    def get_application(self, application_id: int) -> Optional[JobApplication]:
        """Get a job application by ID"""
        return self.db.get(JobApplication, application_id)
    
    def list_applications(
        self,
        job_id: Optional[int] = None,
        applicant_id: Optional[int] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobApplication]:
        """List job applications with filtering options"""
        query = select(JobApplication)
        
        # Apply filters
        if job_id is not None:
            query = query.where(JobApplication.job_id == job_id)
        if applicant_id is not None:
            query = query.where(JobApplication.applicant_id == applicant_id)
        if status:
            query = query.where(JobApplication.status == status)
            
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def update_application_status(
        self, 
        application_id: int, 
        status: ApplicationStatus,
        notes: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[JobApplication]:
        """
        Update application status with permission checks.
        """
        application = self.get_application(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
            
        # If user is provided, verify they have permission to update this application
        if user:
            job = self.get_job(application.job_id)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated job not found"
                )
                
            if job.created_by != user.id and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this application"
                )
        
        # Update application
        application.status = status
        if notes is not None:
            application.notes = notes
            
        application.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(application)
        
        return application

    # --- Utility Methods ---
    def get_applications_stats(self, job_id: int) -> Dict[str, int]:
        """Get statistics for job applications"""
        query = self.db.query(
            JobApplication.status,
            func.count(JobApplication.id).label('count')
        ).filter(JobApplication.job_id == job_id)
        
        query = query.group_by(JobApplication.status)
        result = query.all()
        
        # Initialize stats with all possible statuses set to 0
        stats = {status.value: 0 for status in ApplicationStatus}
        
        # Update with actual counts
        for status, count in result:
            stats[status.value] = count
            
        return stats
    
    def get_user_applications(
        self, 
        user_id: int,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobApplication]:
        """Get all job applications for a user"""
        query = select(JobApplication).where(JobApplication.applicant_id == user_id)
        
        if status:
            query = query.where(JobApplication.status == status)
            
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def get_company_jobs(
        self,
        company_id: int,
        status: Optional[JobStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """Get all jobs for a company"""
        query = select(Job).where(Job.company_id == company_id)
        
        if status:
            query = query.where(Job.status == status)
            
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def get_job_with_applications(self, job_id: int, user: User) -> Optional[Job]:
        """Get a job with its applications (for job poster)"""
        job = self.get_job(job_id)
        if not job:
            return None
            
        # Verify user has permission to view applications
        if job.created_by != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these applications"
            )
            
        return job
