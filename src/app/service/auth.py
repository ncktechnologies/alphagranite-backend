
import os
import jwt
import string
import secrets
import logging
from sqlalchemy import select
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

    # Database models are only required for methods that query the DB.
    # Wrapping these imports avoids ImportError when importing AuthService
    # in small utility scripts that don't have DB dependencies installed.
from src.app.database.user import User
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status
from typing import Optional, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.permission import Permission
from src.app.database.action_menu import ActionMenu
from src.app.database.role_permission import RolePermission


class AuthService:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    # Prefer a scheme that doesn't suffer from bcrypt's 72-byte limit.
    # pbkdf2_sha256 is a widely-supported, pure-Python scheme and will
    # avoid "password cannot be longer than 72 bytes" errors.
    # bcrypt must come before pbkdf2_sha256 so existing bcrypt hashes are tried first.
        self.pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256", "bcrypt_sha256"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        # Do not silently truncate passwords here — pass through to the password
        # context. If you rely on bcrypt, be aware bcrypt has a 72-byte limit
        # and extremely long passwords may produce an error from the backend.
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        # Try hashing with the default scheme. If the backend raises a
        # ValueError (e.g. bcrypt backend complaining about >72 bytes),
        # fall back to pbkdf2_sha256 explicitly which supports arbitrary
        # password lengths.
        try:
            return self.pwd_context.hash(password)
        except ValueError as exc:
            # This often originates from bcrypt's 72-byte limit.
            logging.warning("password hashing with default scheme failed: %s; falling back to pbkdf2_sha256", exc)
            # Force pbkdf2_sha256 for the fallback
            return self.pwd_context.hash(password, scheme="pbkdf2_sha256")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async def get_user_permissions(self, user_id: int, db_session: AsyncSession) -> List[Dict]:
        """Get all permissions for a user based on their role"""
        result = await db_session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return []

        # Super admin has all permissions for all action menus
        if user.is_super_admin:
            am_res = await db_session.execute(select(ActionMenu))
            action_menus = am_res.scalars().all()
            permissions = []
            for menu in action_menus:
                permissions.append({
                    "menu_id": menu.id,
                    "menu_name": menu.name,
                    "menu_code": menu.code,
                    "can_create": True,
                    "can_read": True,
                    "can_update": True,
                    "can_delete": True,
                })
            return permissions

        # Regular user permissions
        if not user.role_id:
            return []

        qry = (
            select(
                ActionMenu.id.label("menu_id"),
                ActionMenu.name.label("menu_name"),
                ActionMenu.code.label("menu_code"),
                Permission.can_create,
                Permission.can_read,
                Permission.can_update,
                Permission.can_delete,
            )
            .join(RolePermission, RolePermission.action_menu_id == ActionMenu.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .filter(RolePermission.role_id == user.role_id)
        )

        res = await db_session.execute(qry)
        rows = res.all()
        print(rows)
        print(res)

        return [
            {
                "menu_id": row.menu_id,
                "menu_name": row.menu_name,
                "menu_code": row.menu_code,
                "can_create": row.can_create,
                "can_read": row.can_read,
                "can_update": row.can_update,
                "can_delete": row.can_delete,
            }
            for row in rows
        ]

    async def authenticate_user(self, user_id: int, db_session: AsyncSession) -> Dict:
        """Generate tokens and user info for authenticated user"""
        res = await db_session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get user permissions for action menus
        user_permissions = await self.get_user_permissions(user.id, db_session)

        # Create tokens with claims
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role_id": user.role_id,
            "is_super_admin": user.is_super_admin,
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": user.username, "user_id": user.id})

        # Return tokens with user permissions
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role_id": user.role_id,
                "is_super_admin": user.is_super_admin,
            },
            "permissions": user_permissions,
        }

    async def create_password_reset_token(self, email: str, db_session: AsyncSession) -> Tuple[bool, Optional[str], Optional[User]]:
        """Create a password reset token for a user"""
        res = await db_session.execute(select(User).where(User.email == email))
        user = res.scalars().first()
        if not user:
            return False, "Email not found", None

        # Generate a secure random token
        reset_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))

        # Create a JWT token with the reset token
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "reset_token": reset_token,
            "exp": datetime.utcnow() + timedelta(minutes=30),  # Token expires in 30 minutes
        }

        # Note: not storing reset token in DB in this simplified implementation
        token = jwt.encode(token_data, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return True, token, user
        
    async def verify_reset_token(self, token: str, db_session: AsyncSession) -> Tuple[bool, Optional[str], Optional[int]]:
        """Verify a password reset token"""
        try:
            # Decode the JWT token
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            
            # Check if token has expired
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                return False, "Token has expired", None
                
            # Get user from database
            user_id = payload.get("user_id")
            if not user_id:
                return False, "Invalid token", None
                
            res = await db_session.execute(select(User).where(User.id == user_id))
            user = res.scalars().first()
            if not user:
                return False, "User not found", None
                
            # In a real application, you'd verify the reset_token against what's stored in the database
            # if user.reset_token != payload.get("reset_token") or user.reset_token_expires < datetime.utcnow():
            #     return False, "Invalid or expired token", None
                
            return True, None, user_id
            
        except jwt.ExpiredSignatureError:
            return False, "Token has expired", None
        except jwt.InvalidTokenError:
            return False, "Invalid token", None
            
    async def change_password(self, user_id: int, current_password: str, new_password: str, db_session: AsyncSession) -> Tuple[bool, Optional[str]]:
        """Change a user's password"""
        res = await db_session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if not user:
            return False, "User not found"

        # Verify current password
        if not self.verify_password(current_password, user.password):
            return False, "Current password is incorrect"

        # Hash the new password
        hashed_password = self.get_password_hash(new_password)

        # Update password in database
        user.password = hashed_password
        user.is_first_login = False  # User has changed password, so no longer first login
        user.updated_at = datetime.now()
        db_session.add(user)
        await db_session.commit()

        return True, None
        
    async def reset_password(self, user_id: int, new_password: str, db_session: AsyncSession) -> Tuple[bool, Optional[str]]:
        """Reset a user's password"""
        res = await db_session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if not user:
            return False, "User not found"

        # Hash the new password
        hashed_password = self.get_password_hash(new_password)

        # Update password in database
        user.password = hashed_password
        user.is_first_login = False  # Reset counts as changing password
        user.failed_login_attempts = 0  # Reset failed login attempts
        user.is_locked = False  # Unlock account if it was locked
        user.locked_at = None
        user.updated_at = datetime.now()
        db_session.add(user)
        await db_session.commit()

        return True, None
