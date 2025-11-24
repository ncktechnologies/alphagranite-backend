import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, validator

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    
class DatabaseHealthResponse(BaseModel):
    """Database health check response"""
    status: str
    database: bool
    message: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
    
    # @validator('password')
    # def truncate_password(cls, v):
    #     """Truncate password to 72 bytes for bcrypt compatibility"""
    #     if isinstance(v, str):
    #         v_bytes = v.encode('utf-8')
    #         if len(v_bytes) > 72:
    #             return v_bytes[:72].decode('utf-8', errors='ignore')
    #     return v


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class TokenPayload(BaseModel):
    sub: str
    user_id: int
    role_id: Optional[int] = None
    is_super_admin: bool = False
    exp: int

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('current_password', 'new_password', 'confirm_password')
    def truncate_password(cls, v):
        """Truncate password to 72 bytes for bcrypt compatibility"""
        if isinstance(v, str):
            v_bytes = v.encode('utf-8')
            if len(v_bytes) > 72:
                return v_bytes[:72].decode('utf-8', errors='ignore')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """
        Validate password strength requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str
    
    @validator('new_password', 'confirm_password')
    def truncate_password(cls, v):
        """Truncate password to 72 bytes for bcrypt compatibility"""
        if isinstance(v, str):
            v_bytes = v.encode('utf-8')
            if len(v_bytes) > 72:
                return v_bytes[:72].decode('utf-8', errors='ignore')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """
        Validate password strength requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    home_address: Optional[str] = None
    gender: Optional[str] = None
    role_id: Optional[int] = None  # Only admins can update this

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    home_address: Optional[str] = None
    gender: Optional[str] = None
    department: int
    department_name: Optional[str] = None
    status: int
    is_super_admin: bool
    created_at: datetime
    updated_at: datetime
    roles: Optional[List[Dict[str, Any]]] = None
    permissions: Optional[List[Dict[str, Any]]] = None
    action_permissions: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True