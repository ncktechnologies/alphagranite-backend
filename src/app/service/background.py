import os
import logging
import smtplib
import asyncio
from typing import Optional, Any
from typing import Sequence
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.utils.config import SessionLocal, ADMIN_EMAIL
from src.app.database.audit_trail import AuditTrail
from src.app.utils.helpers import success_response

logger = logging.getLogger("notification_service")

# Reuse the application's async SessionLocal exported from config to avoid
# hardcoded credentials and duplicate engine creation which caused
# authentication errors when the values diverged from the environment.
# `SessionLocal` is imported from `src.app.utils.config` above.


def _smtp_config() -> tuple[str, int, str, str, str, bool]:
    smtp_host = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    smtp_user = os.getenv("EMAIL_HOST_USER")
    smtp_password = os.getenv("EMAIL_HOST_PASSWORD")
    smtp_from = os.getenv("DEFAULT_FROM_EMAIL")
    use_tls = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

    missing = []
    if not smtp_host:
        missing.append("EMAIL_HOST")
    if not smtp_user:
        missing.append("EMAIL_HOST_USER")
    if not smtp_password:
        missing.append("EMAIL_HOST_PASSWORD")
    if not smtp_from:
        missing.append("DEFAULT_FROM_EMAIL")
    if missing:
        raise ValueError(f"Missing required email environment variables: {', '.join(missing)}")

    return (
        str(smtp_host),
        smtp_port,
        str(smtp_user),
        str(smtp_password),
        str(smtp_from),
        use_tls,
    )


def send_email_with_attachments(
    to_email: str,
    subject: str,
    body: str,
    attachments: Optional[Sequence[tuple[str, bytes, str]]] = None,
    is_html: bool = True,
):
    """Synchronous SMTP send with optional attachments.

    attachments: sequence of (filename, content_bytes, mime_type)
    """
    smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, use_tls = _smtp_config()

    recipients = [item.strip() for item in to_email.split(",") if item.strip()]
    if not recipients:
        raise ValueError("No recipient email addresses provided")

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html" if is_html else "plain"))

    for filename, content, mime_type in (attachments or []):
        part = MIMEApplication(content, _subtype=mime_type.split("/")[-1])
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, recipients, msg.as_string())
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, str(e))
        raise


def send_email(to_email: str, subject: str, body: str, is_html: bool = True):
    """Synchronous SMTP send (will be executed in threadpool to avoid blocking)."""
    send_email_with_attachments(
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=None,
        is_html=is_html,
    )

async def save_audit_trail(
    db: AsyncSession,
    activity: str,
    user_id: int,
    message: str,
    activity_trace_id: int,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    browser: Optional[str] = None,
):
    return await save_audit_event(
        db=db,
        operation=activity,
        resource_type=None,
        user_id=user_id,
        message=message,
        record_id=activity_trace_id,
        device_id=device_id,
        ip_address=ip_address,
        browser=browser,
    )


async def save_audit_event(
    db: Optional[AsyncSession],
    operation: str,
    resource_type: Optional[str],
    user_id: int,
    message: str,
    record_id: Optional[int] = None,
    changed_fields: Optional[list[str]] = None,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    response_status_code: Optional[int] = None,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    browser: Optional[str] = None,
    activity_table_name: Optional[str] = None,
    auto_commit: bool = True,
):
    """Write a standardized audit event.

    If db is provided, writes and commits using that session for compatibility
    with existing call sites. If db is None, creates an internal session.
    """

    async def _write(session: AsyncSession) -> dict[str, Any]:
        audit = AuditTrail(
            activity_message=message,
            operation=(operation or "unknown")[:50],
            user_id=user_id,
            resource_type=(resource_type[:100] if resource_type else None),
            activity_table_name=(activity_table_name[:255] if activity_table_name else None),
            record_id=record_id,
            changed_fields=changed_fields,
            old_values=old_values,
            new_values=new_values,
            request_path=(request_path[:500] if request_path else None),
            request_method=(request_method[:10] if request_method else None),
            response_status_code=response_status_code,
            device_id=device_id,
            ip_address=ip_address,
            browser=browser,
        )
        session.add(audit)
        if auto_commit:
            await session.commit()
            await session.refresh(audit)
        else:
            await session.flush()
        return {"audit_id": audit.id, "message": "Audit trail saved."}

    if db is not None:
        return await _write(db)

    async with SessionLocal() as session:
        return await _write(session)


async def send_notification(
    db: AsyncSession,
    email: str,
    title: str,
    body: str,
    user_id: Optional[int] = None,
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
        return {
            "success": False,
            "message": "No valid email addresses provided",
            "data": {"sent": [], "failed": []},
        }
    
    # Process each email
    sent_emails = []
    failed_emails = []
    
    for recipient_email in email_list:
        # Check if email is an admin email
        is_admin_email = recipient_email.lower() in admin_emails
        
        # For non-admin emails, honor recipient-level notification settings when a user exists.
        if not is_admin_email:
            try:
                async with SessionLocal() as session:
                    result = await session.execute(
                        select(User).where(func.lower(User.email) == recipient_email.lower())
                    )
                    recipient_user = result.scalars().first()

                    # If recipient maps to a deleted user, skip sending.
                    if recipient_user and getattr(recipient_user, "status", None) == 3:
                        await save_audit_trail(
                            session,
                            "notification_failed",
                            user_id or 0,
                            f"Notification skipped for deleted user {recipient_email}",
                            0,
                        )
                        failed_emails.append(recipient_email)
                        continue

                    if recipient_user and not getattr(recipient_user, "email_notifications_enabled", True):
                        await save_audit_trail(
                            session,
                            "notification_off",
                            user_id or 0,
                            f"Notification disabled for {recipient_email}",
                            0,
                        )
                        failed_emails.append(recipient_email)
                        continue
            except Exception as e:
                logger.exception("Error verifying user for notification to %s: %s", recipient_email, str(e))
                failed_emails.append(recipient_email)
                continue
        
        # Send the email in a thread so we don't block the event loop
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, send_email, recipient_email, title, body, is_html)
            sent_emails.append(recipient_email)
            
            # Record audit trail that notification was sent
            async with SessionLocal() as session:
                await save_audit_trail(session, "notification_sent", user_id or 0, f"Notification sent to {recipient_email}", 0)
        except Exception as e:
            logger.exception("Error sending email to %s: %s", recipient_email, str(e))
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
        return {
            "success": False,
            "message": f"Failed to send notification to all recipients: {', '.join(failed_emails)}",
            "data": {"sent": [], "failed": failed_emails},
        }
