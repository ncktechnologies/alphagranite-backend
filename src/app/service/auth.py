import os
import jwt
import string
import secrets
import logging
import random
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

    # Database models are only required for methods that query the DB.
    # Wrapping these imports avoids ImportError when importing AuthService
    # in small utility scripts that don't have DB dependencies installed.
from src.app.database.user import User
from src.app.database.password_reset_otp import PasswordResetOTP
from typing import Optional, Dict, List, Tuple
from src.app.database.permission import Permission
from src.app.database.action_menu import ActionMenu
from src.app.database.role_permission import RolePermission
from src.app.database.role import Role
from src.app.database.user_role import UserRole
from passlib.context import CryptContext
from fastapi import HTTPException, status


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
        """Get all permissions for a user based on their roles (from user_roles table)"""
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

        # Get all role IDs for the user from user_roles table
        ur_result = await db_session.execute(
            select(UserRole.role_id).filter(UserRole.user_id == user_id)
        )
        role_ids = [row[0] for row in ur_result.all()]
        
        if not role_ids:
            return []

        # Get permissions from all roles
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
            .filter(RolePermission.role_id.in_(role_ids))
            .distinct()
        )

        res = await db_session.execute(qry)
        rows = res.all()

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

    async def get_user_roles(self, user_id: int, db_session: AsyncSession) -> List[Dict]:
        """Get all roles assigned to a user"""
        # Query user roles with role details
        qry = (
            select(
                Role.id,
                Role.name,
                Role.description,
            )
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
        )
        
        res = await db_session.execute(qry)
        rows = res.all()
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
            }
            for row in rows
        ]

    async def get_user_role_permissions(self, user_id: int, db_session: AsyncSession) -> List[Dict]:
        """Get all permissions from all roles assigned to a user"""
        # First get all role IDs for this user
        role_qry = select(UserRole.role_id).filter(UserRole.user_id == user_id)
        role_res = await db_session.execute(role_qry)
        role_ids = [row[0] for row in role_res.all()]
        
        if not role_ids:
            return []
        
        # Get all permissions for these roles
        perm_qry = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id.in_(role_ids))
            .distinct()
        )
        
        perm_res = await db_session.execute(perm_qry)
        permissions = perm_res.scalars().all()
        
        return [
            {
                "id": perm.id,
                "name": perm.name,
                "description": perm.description,
                "can_create": perm.can_create,
                "can_read": perm.can_read,
                "can_update": perm.can_update,
                "can_delete": perm.can_delete,
            }
            for perm in permissions
        ]

    async def authenticate_user(self, user_id: int, db_session: AsyncSession) -> Dict:
        """Generate tokens and user info for authenticated user"""
        res = await db_session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get user roles and permissions
        user_roles = await self.get_user_roles(user.id, db_session)
        user_role_permissions = await self.get_user_role_permissions(user.id, db_session)
        
        # Get user permissions for action menus (existing functionality)
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

        # Return tokens with user info, roles, and permissions
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
            "roles": user_roles,  # New: List of roles the user has
            "permissions": user_role_permissions,  # New: Permissions from all roles
            "action_permissions": user_permissions,  # Existing: Action menu permissions
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
        
    async def create_password_reset_otp(self, username_or_email: str, db: AsyncSession):
        """
        Create a 6-digit OTP for password reset
        Accepts both username and email
        Returns: (success, otp, user)
        """
        from src.app.database.user import User
        from src.app.database.password_reset_otp import PasswordResetOTP

        try:
            # Find user by username OR email
            res = await db.execute(
                select(User).where(
                    or_(
                        User.username == username_or_email,
                        User.email == username_or_email
                    )
                )
            )
            user = res.scalars().first()

            if not user:
                return False, None, None

            # Generate 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))

            # Delete any existing OTP for this user
            await db.execute(
                delete(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id)
            )
            await db.commit()

            # Create new OTP record (expires in 10 minutes)
            password_reset_otp = PasswordResetOTP(
                user_id=user.id,
                otp=otp,
                expires_at=datetime.now() + timedelta(minutes=10),
                attempts=0
            )
            db.add(password_reset_otp)
            await db.commit()
            await db.refresh(password_reset_otp)

            return True, otp, user

        except Exception as e:
            await db.rollback()
            print(f"Error creating password reset OTP: {str(e)}")
            return False, None, None

    async def verify_reset_otp(self, username_or_email: str, otp: str, db: AsyncSession):
        """
        Verify OTP for password reset
        Accepts both username and email
        Returns: (success, error_msg, user_id)
        """
        from src.app.database.user import User
        from src.app.database.password_reset_otp import PasswordResetOTP

        try:
            # Find user by username OR email
            res = await db.execute(
                select(User).where(
                    or_(
                        User.username == username_or_email,
                        User.email == username_or_email
                    )
                )
            )
            user = res.scalars().first()

            if not user:
                return False, "User not found", None

            # Find OTP record
            otp_res = await db.execute(
                select(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id)
            )
            otp_record = otp_res.scalars().first()

            if not otp_record:
                return False, "No OTP request found. Please request a new OTP.", user.id

            # Check if OTP is expired
            if datetime.now() > otp_record.expires_at:
                await db.delete(otp_record)
                await db.commit()
                return False, "OTP has expired. Please request a new one.", user.id

            # Check if too many attempts
            if otp_record.attempts >= 3:
                await db.delete(otp_record)
                await db.commit()
                return False, "Too many failed attempts. Please request a new OTP.", user.id

            # Verify OTP
            if otp_record.otp != otp:
                otp_record.attempts += 1
                db.add(otp_record)
                await db.commit()
                remaining_attempts = 3 - otp_record.attempts
                return False, f"Invalid OTP. {remaining_attempts} attempts remaining.", user.id

            # OTP is valid - delete it
            await db.delete(otp_record)
            await db.commit()

            return True, None, user.id

        except Exception as e:
            await db.rollback()
            print(f"Error verifying reset OTP: {str(e)}")
            return False, f"Error verifying OTP: {str(e)}", None

    async def reset_password(self, user_id: int, new_password: str, db: AsyncSession):
        """
        Reset user password
        Returns: (success, error_msg)
        """
        from src.app.database.user import User

        try:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalars().first()

            if not user:
                return False, "User not found"

            # Hash and update password
            user.password = self.hash_password(new_password)
            user.is_first_login = False
            user.updated_at = datetime.now()
            db.add(user)
            await db.commit()
            await db.refresh(user)

            return True, None

        except Exception as e:
            await db.rollback()
            print(f"Error resetting password: {str(e)}")
            return False, str(e)
