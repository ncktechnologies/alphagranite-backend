import os
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.utils.config import SessionLocal, ADMIN_EMAIL
from src.app.database.audit_trail import AuditTrail
from src.app.utils.helpers import error_response, success_response

# Reuse the application's async SessionLocal exported from config to avoid
# hardcoded credentials and duplicate engine creation which caused
# authentication errors when the values diverged from the environment.
# `SessionLocal` is imported from `src.app.utils.config` above.


def send_email(to_email: str, subject: str, body: str):
    """Synchronous SMTP send (will be executed in threadpool to avoid blocking)."""
    smtp_host = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    smtp_user = os.getenv("EMAIL_HOST_USER")
    smtp_password = os.getenv("EMAIL_HOST_PASSWORD")
    smtp_from = os.getenv("DEFAULT_FROM_EMAIL")
    use_tls = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
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
    db: AsyncSession,
    email: str,
    title: str,
    body: str,
    user_id: int = None,
    is_html: bool = True  # Add this parameter
):
    """
    Send email notification
    - email: recipient email address
    - title: email subject
    - body: email body (can be HTML or plain text)
    - user_id: optional user_id for logging
    - is_html: True to send as HTML, False for plain text
    """
    # Parse admin emails (could be comma-separated)
    admin_emails = [e.strip().lower() for e in ADMIN_EMAIL.split(',') if e.strip()]
    
    # Handle different email input formats
    email_list = []
    if isinstance(email, list):
        email_list = [e.strip() for e in email if e.strip()]
    elif isinstance(email, str):
        # Check if comma-separated
        if ',' in email:
            email_list = [e.strip() for e in email.split(',') if e.strip()]
        else:
            email_list = [email.strip()]
    
    if not email_list:
        return error_response("No valid email addresses provided", 400)
    
    # Process each email
    sent_emails = []
    failed_emails = []
    
    for recipient_email in email_list:
        # Check if email is an admin email
        is_admin_email = recipient_email.lower() in admin_emails
        
        # For non-admin emails, verify user exists and has notifications enabled
        if not is_admin_email:
            try:
                async with SessionLocal() as session:
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalars().first()
                    if not user or getattr(user, "status", None) == "deleted":
                        await save_audit_trail(session, "notification_failed", user_id, f"Notification failed for {recipient_email}", 0)
                        failed_emails.append(recipient_email)
                        continue
                    if not getattr(user, "email_notifications_enabled", True):
                        await save_audit_trail(session, "notification_off", user_id, f"Notification off for {recipient_email}", 0)
                        failed_emails.append(recipient_email)
                        continue
            except Exception as e:
                logging.error(f"Error verifying user for notification: {e}")
                failed_emails.append(recipient_email)
                continue
        
        # Send the email in a thread so we don't block the event loop
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, send_email, recipient_email, title, body)
            sent_emails.append(recipient_email)
            
            # Record audit trail that notification was sent
            async with SessionLocal() as session:
                await save_audit_trail(session, "notification_sent", user_id, f"Notification sent to {recipient_email}", 0)
        except Exception as e:
            logging.error(f"Error sending email to {recipient_email}: {e}")
            failed_emails.append(recipient_email)
    
    # Return response based on results
    if sent_emails and not failed_emails:
        return success_response(
            {"sent": sent_emails}, 
            f"Notification sent to {len(sent_emails)} recipient(s)."
        )
    elif sent_emails and failed_emails:
        return success_response(
            {"sent": sent_emails, "failed": failed_emails},
            f"Notification sent to {len(sent_emails)} recipient(s), failed for {len(failed_emails)}."
        )
    else:
        return error_response(
            f"Failed to send notification to all recipients: {', '.join(failed_emails)}", 
            500
        )
