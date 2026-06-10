"""Option C: lightweight retrieval over prior MCP Q&A history.

This is not vector RAG (no embedding service is wired). It uses recency +
keyword-overlap scoring over recent persisted questions to surface the most
relevant prior Q&A into the advisor prompt, so the assistant can build on past
analysis and stay consistent. Storage is best-effort and never blocks /ask.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import SessionLocal
from src.app.database.mcp_qa_history import MCPQAHistory


logger = logging.getLogger(__name__)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "is", "are", "was", "were", "be", "do", "does", "did", "we", "our", "us",
    "me", "my", "i", "you", "your", "what", "which", "who", "how", "many",
    "much", "show", "give", "tell", "this", "that", "these", "those", "with",
    "from", "about", "over", "under", "into", "per", "and/or", "vs",
}


def history_enabled() -> bool:
    return os.getenv("MCP_AI_ENABLE_HISTORY", "true").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", (question or "").strip().lower())


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {token for token in tokens if len(token) > 2 and token not in _STOPWORDS}


async def store_qa_history(
    *,
    user_id: int,
    question: str,
    mode: str,
    matched_tool: Optional[str],
    answer_summary: Optional[str],
    answer_json: Optional[dict[str, Any]],
    provider: Optional[str],
    model: Optional[str],
) -> None:
    """Persist a Q&A record. Best-effort: failures are logged, never raised."""
    if not history_enabled():
        return
    try:
        serialized_answer: Optional[str] = None
        if answer_json is not None:
            try:
                serialized_answer = json.dumps(answer_json, ensure_ascii=False)[:20000]
            except (TypeError, ValueError):
                serialized_answer = None

        async with SessionLocal() as session:
            record = MCPQAHistory(
                user_id=user_id,
                question=(question or "")[:8000],
                normalized_question=_normalize_question(question)[:8000],
                mode=(mode or "report")[:32],
                matched_tool=(matched_tool or None),
                answer_summary=(answer_summary or None),
                answer_json=serialized_answer,
                provider=(provider or None),
                model=(model or None),
                created_at=datetime.now(),
            )
            session.add(record)
            await session.commit()
        logger.info("mcp.history stored user_id=%s mode=%s tool=%s", user_id, mode, matched_tool)
    except Exception:
        logger.exception("mcp.history store_failed user_id=%s", user_id)


async def retrieve_related_qa(
    *,
    db: AsyncSession,
    user_id: int,
    question: str,
    limit: int = 3,
    scan_recent: int = 60,
) -> list[dict[str, Any]]:
    """Return up to `limit` prior Q&A items most relevant to `question`.

    Relevance = keyword overlap with recency tie-break. Only positive-overlap
    items are returned. Scoped to the requesting user. Read-only.
    """
    if not history_enabled():
        return []
    try:
        query_tokens = _tokenize(question)
        if not query_tokens:
            return []

        statement = (
            select(MCPQAHistory)
            .where(MCPQAHistory.user_id == user_id)
            .order_by(MCPQAHistory.created_at.desc())
            .limit(max(scan_recent, limit))
        )
        result = await db.execute(statement)
        rows = result.scalars().all()

        normalized_current = _normalize_question(question)
        scored: list[tuple[float, datetime, MCPQAHistory]] = []
        for row in rows:
            # Skip the identical question we may have just stored.
            if row.normalized_question == normalized_current:
                continue
            row_tokens = _tokenize(row.normalized_question)
            if not row_tokens:
                continue
            overlap = len(query_tokens & row_tokens)
            if overlap <= 0:
                continue
            union = len(query_tokens | row_tokens) or 1
            score = overlap / union
            # Small boost when the prior answer received positive feedback.
            if (row.feedback or 0) > 0:
                score += 0.1
            scored.append((score, row.created_at, row))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

        related: list[dict[str, Any]] = []
        for score, _created, row in scored[: max(limit, 1)]:
            related.append(
                {
                    "question": row.question,
                    "matched_tool": row.matched_tool,
                    "mode": row.mode,
                    "answer_summary": row.answer_summary,
                    "relevance": round(score, 3),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
            )
        if related:
            logger.info("mcp.history retrieved count=%s user_id=%s", len(related), user_id)
        return related
    except Exception:
        logger.exception("mcp.history retrieve_failed user_id=%s", user_id)
        # Clear any aborted transaction so the shared session stays usable.
        try:
            await db.rollback()
        except Exception:
            logger.exception("mcp.history retrieve_rollback_failed user_id=%s", user_id)
        return []


async def record_feedback(*, db: AsyncSession, history_id: int, user_id: int, feedback: int) -> bool:
    """Set thumbs up/down (1 / -1) on a prior Q&A item owned by the user."""
    try:
        statement = select(MCPQAHistory).where(
            MCPQAHistory.id == history_id,
            MCPQAHistory.user_id == user_id,
        )
        result = await db.execute(statement)
        record = result.scalar_one_or_none()
        if record is None:
            return False
        record.feedback = 1 if feedback > 0 else (-1 if feedback < 0 else 0)
        db.add(record)
        await db.commit()
        return True
    except Exception:
        logger.exception("mcp.history feedback_failed history_id=%s", history_id)
        try:
            await db.rollback()
        except Exception:
            logger.exception("mcp.history feedback_rollback_failed history_id=%s", history_id)
        return False
