from datetime import datetime
from sqlalchemy import select
from typing import Any, Optional
from src.app.database.user import User
from src.app.service.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.service.account import AccountService
from src.app.interface.schemas import (
    TokenSchema, RefreshTokenRequest,
    PasswordResetConfirm, UserProfileUpdate, UserResponse,
    LoginRequest, PasswordChangeRequest, PasswordResetRequest,
)

# ...existing code...

# Place the refresh token endpoint after auth_router is defined

from src.app.utils.constants import *
from src.app.utils.config import ADMIN_EMAIL
from src.app.interface.response_wrappers import SuccessResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.app.service.background import send_notification, save_audit_trail
from src.app.utils.helpers import call_service, success_response, error_response
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status

# Import database session dependency
from src.app.database import get_db
from src.app.database.user_role import UserRole

bearer_scheme = HTTPBearer()

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


# Dependency to get the current user from a token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# Add refresh token endpoint for Swagger/OpenAPI
@auth_router.post(
    "/refresh-token",
    response_model=SuccessResponse[TokenSchema],
    summary="Refresh JWT tokens",
    response_description="Returns a new access and refresh token.",
    tags=["auth"],
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token and refresh token.

    - **refresh_token**: The refresh token issued during login or previous refresh.

    Returns a new access token and refresh token if the provided refresh token is valid and not expired.
    """
    try:
        payload = auth_service.decode_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise error_response("Invalid refresh token type", status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("user_id")
        if not user_id:
            raise error_response("Invalid refresh token payload", status.HTTP_401_UNAUTHORIZED)
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(f"Invalid refresh token: {str(e)}", status.HTTP_401_UNAUTHORIZED)

    # Check user still exists and is active
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user or getattr(user, "status", None) != 1:
        raise error_response("User not found or inactive", status.HTTP_401_UNAUTHORIZED)

    # Generate new tokens
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role_id": user.role_id,
        "is_super_admin": user.is_super_admin,
    }
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token({"sub": user.username, "user_id": user.id})
    token_obj = TokenSchema(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
    return success_response(token_obj, "Tokens refreshed successfully")

@auth_router.post("/login")
async def login(
    login_data: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    async def login_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        res = await db.execute(
            select(User).where((User.username == login_data.username) | (User.email == login_data.username))
        )
        user = res.scalars().first()

        # User not found
        if not user:
            background_tasks.add_task(
                save_audit_trail,
                db,
                AUDIT_LOGIN_FAILED,
                None,
                MSG_INCORRECT_CREDENTIALS,
                0,
                device_id,
                ip_address,
                browser,
            )
            background_tasks.add_task(
                send_notification,
                db,
                ADMIN_EMAIL,
                NOTIF_LOGIN_FAILED,
                f"Login failed for {login_data.username}",
                None,
            )
            # Don't reveal that the user doesn't exist
            raise error_response(MSG_INCORRECT_CREDENTIALS, 401)

        # TEMPORARILY DISABLED: Account locking check (for debugging/testing)
        # if user.is_locked:
        #     background_tasks.add_task(
        #         save_audit_trail,
        #         db,
        #         AUDIT_ACCOUNT_LOCKED,
        #         user.id,
        #         MSG_ACCOUNT_LOCKED,
        #         0,
        #         device_id,
        #         ip_address,
        #         browser,
        #     )
        #     background_tasks.add_task(
        #         send_notification,
        #         db,
        #         ADMIN_EMAIL,
        #         NOTIF_ACCOUNT_LOCKED,
        #         f"Account locked for {login_data.username}",
        #         user.id,
        #     )
        #     raise error_response(MSG_ACCOUNT_LOCKED, 403)

        # Account must be active (status == 1)
        # If not active, deny login
        if getattr(user, "status", None) != 1:
            background_tasks.add_task(
                save_audit_trail,
                db,
                AUDIT_ACCOUNT_LOCKED,
                user.id,
                MSG_ACCOUNT_INACTIVE,
                0,
                device_id,
                ip_address,
                browser,
            )
            background_tasks.add_task(
                send_notification,
                db,
                ADMIN_EMAIL,
                NOTIF_ACCOUNT_INACTIVE,
                f"Attempted login to inactive account {login_data.username}",
                user.id,
            )
            raise error_response(MSG_ACCOUNT_INACTIVE, 403)

        # Password verification
        if not auth_service.verify_password(login_data.password, user.password):
            # TEMPORARILY DISABLED: Failed login attempts tracking (for debugging/testing)
            # await AccountService.increment_failed_login(db, user)

            background_tasks.add_task(
                save_audit_trail,
                db,
                AUDIT_LOGIN_FAILED,
                user.id,
                MSG_INCORRECT_CREDENTIALS,
                0,
                device_id,
                ip_address,
                browser,
            )

            # TEMPORARILY DISABLED: Account locking on max attempts (for debugging/testing)
            # if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            #     background_tasks.add_task(
            #         save_audit_trail,
            #         db,
            #         AUDIT_ACCOUNT_LOCKED,
            #         user.id,
            #         MSG_MAX_ATTEMPTS_REACHED,
            #         0,
            #         device_id,
            #         ip_address,
            #         browser,
            #     )
            #     background_tasks.add_task(
            #         send_notification,
            #         db,
            #         ADMIN_EMAIL,
            #         NOTIF_ACCOUNT_LOCKED,
            #         f"Account locked for {login_data.username} due to too many failed attempts",
            #         user.id,
            #     )
            #     raise error_response(MSG_MAX_ATTEMPTS_REACHED, 403)

            # background_tasks.add_task(
            #     send_notification,
            #     db,
            #     ADMIN_EMAIL,
            #     NOTIF_LOGIN_FAILED,
            #     f"Login failed for {login_data.username} (Attempt {user.failed_login_attempts}/{MAX_LOGIN_ATTEMPTS})",
            #     user.id,
            # )
            raise error_response(MSG_INCORRECT_CREDENTIALS, 401)

        # TEMPORARILY DISABLED: Reset failed login counter (for debugging/testing)
        # await AccountService.reset_failed_login(db, user)

        # First-time login check
        if user.is_first_login:
            background_tasks.add_task(
                save_audit_trail,
                db,
                AUDIT_FIRST_LOGIN,
                user.id,
                MSG_FIRST_LOGIN,
                0,
                device_id,
                ip_address,
                browser,
            )
            # Generate tokens and include a minimal token response with the
            # first_time flag so frontends can complete onboarding while
            # authenticated. Keep response minimal: access_token + token_type.
            tokens_and_permissions = await auth_service.authenticate_user(user.id, db)
            token_payload = {
                "first_time": True,
                "access_token": tokens_and_permissions.get("access_token"),
                "token_type": tokens_and_permissions.get("token_type", "bearer"),
            }
            return success_response(token_payload, MSG_FIRST_LOGIN_RESPONSE)

        # Role check
        if not user.role_id and not user.is_super_admin:
            background_tasks.add_task(
                save_audit_trail,
                db,
                AUDIT_NO_ROLE,
                user.id,
                MSG_USER_NO_ROLE,
                0,
                device_id,
                ip_address,
                browser,
            )
            background_tasks.add_task(
                send_notification,
                db,
                ADMIN_EMAIL,
                NOTIF_NO_ROLE_ASSIGNED,
                f"No role for {login_data.username}",
                user.id,
            )
            return success_response({"no_role": True, "admin_email": ADMIN_EMAIL}, MSG_NO_ROLE_RESPONSE)

        # Login successful, generate tokens and include permissions
        tokens_and_permissions = await auth_service.authenticate_user(user.id, db)

        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_LOGIN_SUCCESS,
            user.id,
            MSG_LOGIN_SUCCESSFUL,
            0,
            device_id,
            ip_address,
            browser,
        )
        background_tasks.add_task(
            send_notification,
            db,
            user.email,
            NOTIF_LOGIN_SUCCESSFUL,
            f"Welcome {login_data.username}",
            user.id,
        )
        
        return success_response(tokens_and_permissions, MSG_LOGIN_SUCCESSFUL)

    return await call_service(login_flow)


@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    async def change_password_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        # Change password
        success, error_msg = await auth_service.change_password(
            current_user.id, password_data.current_password, password_data.new_password, db
        )

        if not success:
            background_tasks.add_task(
                save_audit_trail,
                db,
                "password_change_failed",
                current_user.id,
                error_msg,
                0,
                device_id,
                ip_address,
                browser,
            )
            raise error_response(error_msg, 400)

        # Log audit trail
        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_PASSWORD_CHANGED,
            current_user.id,
            MSG_PASSWORD_CHANGED,
            0,
            device_id,
            ip_address,
            browser,
        )

        # Send notification
        background_tasks.add_task(
            send_notification,
            db,
            current_user.email,
            NOTIF_PASSWORD_CHANGED,
            "Your password has been changed successfully.",
            current_user.id,
        )

        return success_response(None, MSG_PASSWORD_CHANGED)

    return await call_service(change_password_flow)


@auth_router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    async def request_reset_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        # Request password reset
        success, otp, user = await auth_service.create_password_reset_otp(reset_data.email, db)

        # Always return success to prevent email enumeration attacks
        if not success:
            # Don't reveal that the email doesn't exist
            return success_response(None, MSG_PASSWORD_RESET_REQUESTED)

        # Log audit trail
        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_PASSWORD_RESET_REQUESTED,
            user.id,
            MSG_PASSWORD_RESET_REQUESTED,
            0,
            device_id,
            ip_address,
            browser,
        )

        # Send OTP to central support email
        support_email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Password Reset Request - OTP Code</h2>
                <p>A password reset request has been submitted.</p>
                
                <p><strong>User Details:</strong></p>
                <ul>
                    <li><strong>Name:</strong> {user.first_name} {user.last_name}</li>
                    <li><strong>Email:</strong> {user.email}</li>
                    <li><strong>Username:</strong> {user.username}</li>
                    <li><strong>Request Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>IP Address:</strong> {ip_address or 'N/A'}</li>
                </ul>
                
                <p><strong>OTP Code (6 digits):</strong></p>
                <p style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; font-size: 24px; font-weight: bold; letter-spacing: 2px;">{otp}</p>
                
                <p><strong>OTP Expiration:</strong> 10 minutes from request time</p>
                
                <p>Please provide this OTP to the user or instruct them to use it to reset their password.</p>
                
                <hr style="margin: 20px 0;">
                
                <p style="color: #666; font-size: 12px;">
                    This is an automated message from AlphaGranite. Please do not reply to this email.
                </p>
            </body>
        </html>
        """

        # Send to central support email
        background_tasks.add_task(
            send_notification,
            db,
            SUPPORT_EMAIL,
            NOTIF_PASSWORD_RESET_REQUESTED,
            support_email_body,
            user.id,
        )

        # Also send confirmation email to user (without OTP)
        user_confirmation_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Hello {user.first_name},</p>
                <p>We received your password reset request.</p>
                <p>Our support team will contact you shortly with an OTP code to complete your password reset.</p>
                <p>If you did not request a password reset, please contact our support team at {SUPPORT_EMAIL}</p>
                <p style="color: #666;">The OTP will expire in 10 minutes.</p>
                <br>
                <p>Best regards,<br><strong>AlphaGranite Support Team</strong></p>
            </body>
        </html>
        """

        background_tasks.add_task(
            send_notification,
            db,
            user.email,
            "password_reset_request_received",
            user_confirmation_body,
            user.id,
        )

        return success_response(None, MSG_PASSWORD_RESET_REQUESTED)

    return await call_service(request_reset_flow)


@auth_router.post("/verify-reset-otp")
async def verify_reset_otp(
    otp_data: dict,  # {"email": "user@example.com", "otp": "123456"}
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify OTP for password reset"""
    async def verify_otp_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        email = otp_data.get("email")
        otp = otp_data.get("otp")

        if not email or not otp:
            raise error_response("Email and OTP are required", 400)

        # Verify OTP
        success, error_msg, user_id = await auth_service.verify_reset_otp(email, otp, db)

        if not success:
            background_tasks.add_task(
                save_audit_trail,
                db,
                "password_reset_otp_failed",
                user_id,
                error_msg or "Invalid OTP",
                0,
                device_id,
                ip_address,
                browser,
            )
            raise error_response(error_msg or "Invalid or expired OTP", 400)

        # Get user
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()

        # Log audit trail
        background_tasks.add_task(
            save_audit_trail,
            db,
            "password_reset_otp_verified",
            user_id,
            "OTP verified successfully",
            0,
            device_id,
            ip_address,
            browser,
        )

        return success_response(
            {"user_id": user_id, "email": user.email},
            "OTP verified successfully. You can now reset your password."
        )

    return await call_service(verify_otp_flow)


@auth_router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,  # {"email": "user@example.com", "otp": "123456", "new_password": "..."}
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    async def reset_password_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        # Verify OTP first
        success, error_msg, user_id = await auth_service.verify_reset_otp(
            reset_data.email, reset_data.otp, db
        )

        if not success:
            background_tasks.add_task(
                save_audit_trail,
                db,
                "password_reset_failed",
                user_id,
                error_msg or "Invalid OTP",
                0,
                device_id,
                ip_address,
                browser,
            )
            raise error_response(error_msg or "Invalid or expired OTP", 400)

        # Reset password
        success, error_msg = await auth_service.reset_password(user_id, reset_data.new_password, db)

        if not success:
            raise error_response(error_msg, 400)

        # Get user
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()

        # Log audit trail
        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_PASSWORD_RESET_COMPLETED,
            user_id,
            MSG_PASSWORD_RESET_COMPLETED,
            0,
            device_id,
            ip_address,
            browser,
        )

        # Send notification to support email
        support_notification_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Password Reset Completed</h2>
                <p>Password reset has been successfully completed for:</p>
                <ul>
                    <li><strong>User:</strong> {user.first_name} {user.last_name}</li>
                    <li><strong>Email:</strong> {user.email}</li>
                    <li><strong>Completion Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </body>
        </html>
        """

        background_tasks.add_task(
            send_notification,
            db,
            SUPPORT_EMAIL,
            "password_reset_completed",
            support_notification_body,
            user_id,
        )

        # Send confirmation to user
        background_tasks.add_task(
            send_notification,
            db,
            user.email,
            NOTIF_PASSWORD_RESET_COMPLETED,
            "Your password has been reset successfully. You can now log in with your new password.",
            user_id,
        )

        return success_response(None, MSG_PASSWORD_RESET_COMPLETED)

    return await call_service(reset_password_flow)


@auth_router.post("/unlock-account/{user_id}")
async def unlock_account(
    user_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Unlock a locked account (admin only endpoint)
    """
    async def unlock_flow():
        # Get user details
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if not user:
            raise error_response("User not found", 404)

        # Check if account is locked
        if not user.is_locked:
            return success_response({"user_id": user_id}, "Account is not locked")

        # Unlock the account
        await AccountService.unlock_account(db, user)

        # Audit trail and notification
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_ACCOUNT_UNLOCKED,
            user.id,
            MSG_ACCOUNT_UNLOCKED,
            0,
            device_id,
            ip_address,
            browser,
        )

        background_tasks.add_task(
            send_notification,
            db,
            user.email,
            NOTIF_ACCOUNT_UNLOCKED,
            "Your account has been unlocked. You can now log in.",
            user.id,
        )

        return success_response({"user_id": user_id}, MSG_ACCOUNT_UNLOCKED)

    return await call_service(unlock_flow)


@auth_router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current user profile with roles and permissions"""
    # Fetch department name if user has a department
    from src.app.database.department import Department
    from src.app.service.file import FileService
    
    department_name = None
    if current_user.department:
        dept_result = await db.execute(
            select(Department).where(Department.id == current_user.department)
        )
        department = dept_result.scalars().first()
        if department:
            department_name = department.name
    
    # Fetch profile image URL if user has a profile image
    profile_image_url = None
    if current_user.profile_image_id:
        file_data = await FileService.get_file(db, current_user.profile_image_id)
        if file_data:
            profile_image_url = file_data.get("url")
    
    # Get user roles and permissions using auth service
    user_roles = await auth_service.get_user_roles(current_user.id, db)
    user_role_permissions = await auth_service.get_user_role_permissions(current_user.id, db)
    user_action_permissions = await auth_service.get_user_permissions(current_user.id, db)
    
    # Convert user to dict and add additional data
    user_dict = current_user.model_dump()
    user_dict['department_name'] = department_name
    user_dict['profile_image_url'] = profile_image_url
    user_dict['roles'] = user_roles
    user_dict['permissions'] = user_role_permissions
    user_dict['action_permissions'] = user_action_permissions
    
    return UserResponse(**user_dict)


@auth_router.put("/me")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update user profile"""
    async def update_profile_flow():
        # Extract device info from headers
        device_id = request.headers.get(HEADER_DEVICE_ID)
        ip_address = request.client.host if request.client else None
        browser = request.headers.get(HEADER_USER_AGENT)

        # Check if role_id is being updated - only admins can do this
        if profile_data.role_id is not None:
            if not current_user.is_super_admin:
                raise error_response("Only administrators can assign roles", 403)
            
            # Update role_id on user (for backward compatibility)
            current_user.role_id = profile_data.role_id
            
            # Update user_roles table - add new role if not already assigned
            try:
                # Check if user already has THIS specific role
                ur_result = await db.execute(
                    select(UserRole).where(
                        UserRole.user_id == current_user.id,
                        UserRole.role_id == profile_data.role_id
                    )
                )
                existing_user_role = ur_result.scalars().first()
                
                if not existing_user_role:
                    # Create new role assignment (don't replace existing roles)
                    new_user_role = UserRole(
                        user_id=current_user.id,
                        role_id=profile_data.role_id,
                        created_at=datetime.now()
                    )
                    db.add(new_user_role)
                    await db.flush()  # Flush to ensure UserRole is created
                # else: User already has this role, no action needed
                
            except Exception as e:
                await db.rollback()
                raise error_response(f"Failed to update role assignment: {str(e)}", 500)

        # Update other profile fields
        for field, value in profile_data.dict(exclude_unset=True, exclude={'role_id'}).items():
            if value is not None:  # Only update fields that were included in the request
                setattr(current_user, field, value)

        current_user.updated_at = datetime.now()
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)

        # Log audit trail
        background_tasks.add_task(
            save_audit_trail,
            db,
            AUDIT_PROFILE_UPDATED,
            current_user.id,
            MSG_PROFILE_UPDATED,
            0,
            device_id,
            ip_address,
            browser,
        )

        # Fetch department name if user has a department
        from src.app.database.department import Department
        department_name = None
        if current_user.department:
            dept_result = await db.execute(
                select(Department).where(Department.id == current_user.department)
            )
            department = dept_result.scalars().first()
            if department:
                department_name = department.name
        
        # Get user roles and permissions using auth service
        user_roles = await auth_service.get_user_roles(current_user.id, db)
        user_role_permissions = await auth_service.get_user_role_permissions(current_user.id, db)
        user_action_permissions = await auth_service.get_user_permissions(current_user.id, db)
        
        # Convert user to dict and add additional data
        user_dict = current_user.model_dump()
        user_dict['department_name'] = department_name
        user_dict['roles'] = user_roles
        user_dict['permissions'] = user_role_permissions
        user_dict['action_permissions'] = user_action_permissions

        return success_response(UserResponse(**user_dict), MSG_PROFILE_UPDATED)

    return await call_service(update_profile_flow)
