from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from src.app.utils.helpers import utc_now

if TYPE_CHECKING:
    from .user import User


class PasswordResetOTP(SQLModel, table=True):
    __tablename__ = "password_reset_otps"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    otp: str = Field(max_length=6)
    expires_at: datetime
    attempts: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)

    # Relationship back to User
    user: Optional["User"] = Relationship(back_populates="password_reset_otps")