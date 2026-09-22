import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.service.hcp_payroll_ingestion import (
    get_active_configs,
    ingest_hcp_payroll_report,
    is_config_due,
)
from src.app.tasks.celery_app import celery_app
from src.app.utils.config import DATABASE_URL
from src.app.utils.helpers import utc_now

logger = logging.getLogger("hcp_payroll_tasks")


def _run_with_session(operation: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
    """Run a DB coroutine in a fresh event loop with its own engine.

    Celery workers are not asyncio-native, and an asyncpg engine cannot be shared
    across event loops, so each task run gets a disposable engine.
    """

    async def _runner() -> Any:
        engine = create_async_engine(
            DATABASE_URL,
            connect_args={"statement_cache_size": 0} if "postgresql" in DATABASE_URL else {},
        )
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                return await operation(session)
        finally:
            await engine.dispose()

    return asyncio.run(_runner())


@celery_app.task(name="hcp_payroll.ingest_config", bind=True, max_retries=3, default_retry_delay=300)
def ingest_config_task(self, source_config_id: int) -> dict:
    try:
        return _run_with_session(lambda session: ingest_hcp_payroll_report(session, source_config_id))
    except Exception as exc:
        logger.exception("HCP ingestion task failed for config %s", source_config_id)
        raise self.retry(exc=exc)


@celery_app.task(name="hcp_payroll.dispatch_due_ingestions")
def dispatch_due_ingestions_task() -> dict:
    now = utc_now()

    async def _collect(session: AsyncSession) -> list[int]:
        configs = await get_active_configs(session)
        return [config.id for config in configs if is_config_due(config, now)]

    due_config_ids = _run_with_session(_collect)
    for config_id in due_config_ids:
        ingest_config_task.delay(config_id)

    return {"checked_at": now.isoformat(), "dispatched": due_config_ids}
