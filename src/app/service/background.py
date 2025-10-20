
import os
import smtplib
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from email.mime.text import MIMEText
from src.app.database.user import User
from email.mime.multipart import MIMEMultipart
from src.app.database.audit_trail import AuditTrail
from src.app.utils.helpers import error_response, success_response

# Audit trail background task
async def save_audit_trail(
    db: Session,
    activity: str,
    user_id: int,
    message: str,
    activity_trace_id: int
):
    audit = AuditTrail(
        activity=activity,
        user_id=user_id,
        message=message,
        activity_trace_id=activity_trace_id
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return success_response({"audit_id": audit.id}, "Audit trail saved.")

# Notification background task
# Notification background task

def send_email(to_email: str, subject: str, body: str):
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
    except Exception as e:
        # Log error or handle as needed
        pass

async def send_notification(
    db: Session,
    email: str,
    title: str,
    body: str,
    user_id: int
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status == "deleted":
        await save_audit_trail(db, "notification_failed", user_id, f"Notification failed for {email}", activity_trace_id=0)
        return error_response("User not found or deleted", 404)
    if not user.email_notifications_enabled:
        await save_audit_trail(db, "notification_off", user_id, f"Notification off for {email}", activity_trace_id=0)
        return error_response("Email notifications are off", 400)
    # Send the email using SMTP
    send_email(email, title, body)
    await save_audit_trail(db, "notification_sent", user_id, f"Notification sent to {email}", activity_trace_id=0)
    return success_response({"email": email}, "Notification sent.")
