
import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.utils.config import SessionLocal
from src.app.database.audit_trail import AuditTrail
from src.app.utils.helpers import error_response, success_response

# Reuse the application's async SessionLocal exported from config to avoid
# hardcoded credentials and duplicate engine creation which caused
# authentication errors when the values diverged from the environment.
# `SessionLocal` is imported from `src.app.utils.config` above.


def send_email(to_email: str, subject: str, body: str):
    """Synchronous SMTP send (will be executed in threadpool to avoid blocking)."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())
    except Exception:
        # Log error or handle as needed (avoid raising inside background tasks)
        pass

async def save_audit_trail(
    db: AsyncSession,
    activity: str,
    user_id: int,
    message: str,
    activity_trace_id: int,
    device_id: str = None,
    ip_address: str = None,
    browser: str = None,
):
    async with SessionLocal() as session:
        audit = AuditTrail(
            activity_message=message,
            user_id=user_id,
            record_id=activity_trace_id,
            device_id=device_id,
            ip_address=ip_address,
            browser=browser,
        )
        session.add(audit)
        await session.commit()
        await session.refresh(audit)
        return {"audit_id": audit.id, "message": "Audit trail saved."}


async def send_notification(
    db: AsyncSession | None,
    email: str,
    title: str,
    body: str,
    user_id: int,
):
    """Send an email notification and record audit events. This function
    opens its own async session so callers can pass a request session or None.
    """
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user or getattr(user, "status", None) == "deleted":
            await save_audit_trail(session, "notification_failed", user_id, f"Notification failed for {email}", 0)
            return error_response("User not found or deleted", 404)
        if not getattr(user, "email_notifications_enabled", True):
            await save_audit_trail(session, "notification_off", user_id, f"Notification off for {email}", 0)
            return error_response("Email notifications are off", 400)

    # Send the email in a thread so we don't block the event loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send_email, email, title, body)

    # Record audit trail that notification was sent
    async with SessionLocal() as session:
        await save_audit_trail(session, "notification_sent", user_id, f"Notification sent to {email}", 0)
    return success_response({"email": email}, "Notification sent.")
