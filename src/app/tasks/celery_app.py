import os

from celery import Celery
from celery.schedules import crontab

BROKER_URL = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL") or "redis://redis:6379/0"
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND") or BROKER_URL

celery_app = Celery(
    "alphagranite",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["src.app.tasks.hcp_payroll_tasks"],
)

celery_app.conf.update(
    timezone=os.getenv("CELERY_TIMEZONE", "America/Chicago"),
    enable_utc=False,
    task_acks_late=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "hcp-dispatch-due-ingestions": {
            "task": "hcp_payroll.dispatch_due_ingestions",
            "schedule": crontab(minute="*"),
        },
    },
)
