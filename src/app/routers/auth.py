from typing import Any
from sqlalchemy.orm import Session
from src.app.database.user import User
from src.app.service.auth import AuthService
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from src.app.service.background import send_notification, save_audit_trail
from src.app.utils.helpers import call_service, success_response, error_response
from src.app.utils.config import ADMIN_EMAIL

# You should have a get_db dependency for SQLAlchemy session
# from src.app.database import get_db

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()

@auth_router.post("/login")
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str,
    password: str,
    db: Session = Depends(),  # Replace with Depends(get_db) in real code
    device_id: str = None,
    ip_address: str = None,
    browser: str = None
) -> Any:
    async def login_flow():
        user = db.query(User).filter((User.username == username) | (User.email == username)).first()
        if not user:
            background_tasks.add_task(
                save_audit_trail, db, "login_failed", None, "Incorrect credentials", 0
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, "Login failed", f"Login failed for {username}", None
            )
            raise error_response("Incorrect credentials", 401)
        if user.is_locked:
            background_tasks.add_task(
                save_audit_trail, db, "account_locked", user.id, "Account is locked", 0
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, "Account locked", f"Account locked for {username}", user.id
            )
            raise error_response("Account is locked", 403)
        if not auth_service.verify_password(password, user.password):
            background_tasks.add_task(
                save_audit_trail, db, "login_failed", user.id, "Incorrect credentials", 0
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, "Login failed", f"Login failed for {username}", user.id
            )
            raise error_response("Incorrect credentials", 401)
        if user.is_first_login:
            background_tasks.add_task(
                save_audit_trail, db, "first_login", user.id, "First time login", 0
            )
            return success_response({"first_time": True}, "First time login, please change your password.")
        if not user.role_id:
            background_tasks.add_task(
                save_audit_trail, db, "no_role", user.id, "User has no role", 0
            )
            background_tasks.add_task(
                send_notification, db, ADMIN_EMAIL, "No role assigned", f"No role for {username}", user.id
            )
            return success_response({"no_role": True, "admin_email": ADMIN_EMAIL}, "User has no role, contact admin.")
        tokens = auth_service.authenticate_user(username, password, db)
        background_tasks.add_task(
            save_audit_trail, db, "login_success", user.id, "Login successful", 0
        )
        background_tasks.add_task(
            send_notification, db, user.email, "Login successful", f"Welcome {username}", user.id
        )
        return success_response(tokens, "Login successful.")
    return await call_service(login_flow)
