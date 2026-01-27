from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.app.database import Base
from src.app.utils.helpers import utc_now


class JobNote(Base):
    __tablename__ = "job_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("business_jobs.id", ondelete="CASCADE"), nullable=False)
    note = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    # Relationships - use string reference for User to avoid circular imports
    creator = relationship("User", foreign_keys=[created_by], viewonly=True)