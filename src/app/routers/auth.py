
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.orm import Session
from src.app.database.user import User
from src.app.service.auth import AuthService
from src.app.service.account import AccountService
from src.app.interface.schemas import (
    PasswordResetConfirm, UserProfileUpdate, UserResponse,
    LoginRequest, PasswordChangeRequest, PasswordResetRequest, 
)
from src.app.utils.constants import *
from src.app.utils.config import ADMIN_EMAIL
from fastapi.security import OAuth2PasswordBearer
from src.app.service.background import send_notification, save_audit_trail
from src.app.utils.helpers import call_service, success_response, error_response
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status

# Import database session dependency
from src.app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()

# Dependency to get the current user from a token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = auth_service.decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

@auth_router.post("/login")
async def login(
    login_data: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    async def login_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        user = db.query(User).filter((User.username == login_data.username) | (User.email == login_data.username)).first()
        
        # User not found
        if not user:
            background_tasks.add_task(
                save_audit_trail, db, AUDIT_LOGIN_FAILED, None, MSG_INCORRECT_CREDENTIALS, 0, device_id, ip_address, browser
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, NOTIF_LOGIN_FAILED, f"Login failed for {login_data.username}", None
            )
            # Don't reveal that the user doesn't exist
            raise error_response(MSG_INCORRECT_CREDENTIALS, 401)
            
        # Account is locked
        if user.is_locked:
            background_tasks.add_task(
                save_audit_trail, db, AUDIT_ACCOUNT_LOCKED, user.id, MSG_ACCOUNT_LOCKED, 0, device_id, ip_address, browser
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, NOTIF_ACCOUNT_LOCKED, f"Account locked for {login_data.username}", user.id
            )
            raise error_response(MSG_ACCOUNT_LOCKED, 403)
            
        # Password verification
        if not auth_service.verify_password(login_data.password, user.password):
            # Increment failed login attempts and potentially lock account
            AccountService.increment_failed_login(db, user)
            
            background_tasks.add_task(
                save_audit_trail, db, AUDIT_LOGIN_FAILED, user.id, MSG_INCORRECT_CREDENTIALS, 0, device_id, ip_address, browser
            )
            
            # If this attempt caused the account to be locked
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                background_tasks.add_task(
                    save_audit_trail, db, AUDIT_ACCOUNT_LOCKED, user.id, MSG_MAX_ATTEMPTS_REACHED, 0, device_id, ip_address, browser
                )
                background_tasks.add_task(
                    send_notification, db, ADMIN_EMAIL, NOTIF_ACCOUNT_LOCKED, 
                    f"Account locked for {login_data.username} due to too many failed attempts", user.id
                )
                raise error_response(MSG_MAX_ATTEMPTS_REACHED, 403)
                
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, NOTIF_LOGIN_FAILED, 
                f"Login failed for {login_data.username} (Attempt {user.failed_login_attempts}/{MAX_LOGIN_ATTEMPTS})", user.id
            )
            raise error_response(MSG_INCORRECT_CREDENTIALS, 401)
            
        # Password correct, reset failed login counter
        AccountService.reset_failed_login(db, user)
        
        # First-time login check
        if user.is_first_login:
            background_tasks.add_task(
                save_audit_trail, db, AUDIT_FIRST_LOGIN, user.id, MSG_FIRST_LOGIN, 0, device_id, ip_address, browser
            )
            return success_response({"first_time": True}, MSG_FIRST_LOGIN_RESPONSE)
            
        # Role check
        if not user.role_id:
            background_tasks.add_task(
                save_audit_trail, db, AUDIT_NO_ROLE, user.id, MSG_USER_NO_ROLE, 0, device_id, ip_address, browser
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, NOTIF_NO_ROLE_ASSIGNED, f"No role for {login_data.username}", user.id
            )
            return success_response({"no_role": True, "admin_email": ADMIN_EMAIL}, MSG_NO_ROLE_RESPONSE)
            
        # Login successful, generate tokens and include permissions
        tokens_and_permissions = auth_service.authenticate_user(user.id, db)
        
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_LOGIN_SUCCESS, user.id, MSG_LOGIN_SUCCESSFUL, 0, device_id, ip_address, browser
        )
        background_tasks.add_task(
            send_notification, db, user.email, NOTIF_LOGIN_SUCCESSFUL, f"Welcome {login_data.username}", user.id
        )
        return success_response(tokens_and_permissions, MSG_LOGIN_SUCCESSFUL)
        
    return await call_service(login_flow)

@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    async def change_password_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        # Change password
        success, error_msg = auth_service.change_password(
            current_user.id, password_data.current_password, password_data.new_password, db
        )
        
        if not success:
            background_tasks.add_task(
                save_audit_trail, db, "password_change_failed", current_user.id, error_msg, 0, 
                device_id, ip_address, browser
            )
            raise error_response(error_msg, 400)
            
        # Log audit trail
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_PASSWORD_CHANGED, current_user.id, MSG_PASSWORD_CHANGED, 0, 
            device_id, ip_address, browser
        )
        
        # Send notification
        background_tasks.add_task(
            send_notification, db, current_user.email, NOTIF_PASSWORD_CHANGED, 
            "Your password has been changed successfully.", current_user.id
        )
        
        return success_response(None, MSG_PASSWORD_CHANGED)
        
    return await call_service(change_password_flow)
    
@auth_router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    async def request_reset_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        # Request password reset
        success, token, user = auth_service.create_password_reset_token(reset_data.email, db)
        
        # Always return success to prevent email enumeration attacks
        if not success:
            # Don't reveal that the email doesn't exist
            return success_response(None, MSG_PASSWORD_RESET_REQUESTED)
            
        # Build reset URL (frontend URL should be configurable)
        reset_url = f"https://yourdomain.com/reset-password?token={token}"
        
        # Log audit trail
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_PASSWORD_RESET_REQUESTED, user.id, MSG_PASSWORD_RESET_REQUESTED, 0, 
            device_id, ip_address, browser
        )
        
        # Send password reset email
        reset_email_body = f"""
        <html>
            <body>
                <p>Hello {user.first_name},</p>
                <p>We received a request to reset your password.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 30 minutes.</p>
                <p>If you did not request a password reset, please ignore this email.</p>
            </body>
        </html>
        """
        
        background_tasks.add_task(
            send_notification, db, user.email, NOTIF_PASSWORD_RESET_REQUESTED, reset_email_body, user.id
        )
        
        return success_response(None, MSG_PASSWORD_RESET_REQUESTED)
        
    return await call_service(request_reset_flow)
    
@auth_router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    async def reset_password_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        # Verify reset token
        success, error_msg, user_id = auth_service.verify_reset_token(reset_data.token, db)
        
        if not success:
            return error_response(error_msg or MSG_PASSWORD_RESET_INVALID, 400)
            
        # Reset password
        success, error_msg = auth_service.reset_password(user_id, reset_data.new_password, db)
        
        if not success:
            return error_response(error_msg, 400)
            
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        
        # Log audit trail
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_PASSWORD_RESET_COMPLETED, user_id, MSG_PASSWORD_RESET_COMPLETED, 0, 
            device_id, ip_address, browser
        )
        
        # Send notification
        background_tasks.add_task(
            send_notification, db, user.email, NOTIF_PASSWORD_RESET_COMPLETED, 
            "Your password has been reset successfully.", user_id
        )
        
        return success_response(None, MSG_PASSWORD_RESET_COMPLETED)
        
    return await call_service(reset_password_flow)


@auth_router.post("/unlock-account/{user_id}")
async def unlock_account(
    user_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    """
    Unlock a locked account (admin only endpoint)
    """
    async def unlock_flow():
        # Get user details
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise error_response("User not found", 404)
            
        # Check if account is locked
        if not user.is_locked:
            return success_response({"user_id": user_id}, "Account is not locked")
            
        # Unlock the account
        AccountService.unlock_account(db, user)
        
        # Audit trail and notification
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_ACCOUNT_UNLOCKED, user.id, MSG_ACCOUNT_UNLOCKED, 0, device_id, ip_address, browser
        )
        
        background_tasks.add_task(
            send_notification, db, user.email, NOTIF_ACCOUNT_UNLOCKED, 
            "Your account has been unlocked. You can now log in.", user.id
        )
        
        return success_response({"user_id": user_id}, MSG_ACCOUNT_UNLOCKED)
        
    return await call_service(unlock_flow)

@auth_router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user profile"""
    return UserResponse.from_orm(current_user)

@auth_router.put("/me")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update user profile"""
    async def update_profile_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)
        
        # Update user profile
        for field, value in profile_data.dict(exclude_unset=True).items():
            if value is not None:  # Only update fields that were included in the request
                setattr(current_user, field, value)
                
        current_user.updated_at = datetime.now()
        db.commit()
        db.refresh(current_user)
        
        # Log audit trail
        background_tasks.add_task(
            save_audit_trail, db, AUDIT_PROFILE_UPDATED, current_user.id, MSG_PROFILE_UPDATED, 0, 
            device_id, ip_address, browser
        )
        
        return success_response(UserResponse.from_orm(current_user), MSG_PROFILE_UPDATED)
        
    return await call_service(update_profile_flow)
