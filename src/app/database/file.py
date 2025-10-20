from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class File(SQLModel, table=True):
    __tablename__ = "files"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    file_path: str = Field(max_length=255)
    file_type: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    file_size: str = Field(max_length=255)
