"""Option A: multi-tool context pack.

For broad / cross-domain questions ("how is the business doing overall?"),
running a single report is too narrow. This module runs several relevant
report tools concurrently, all through the existing vetted handlers (no SQL,
no new data access), and merges their results + insights into one combined
context object for the advisor to reason across.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.mcp.report_tools import (
    enrich_params_from_question,
    get_report_tool_definition,
    invoke_report_tool,
    sanitize_params_for_tool,
    suggest_tools_for_question,
    summarize_tool_result,
)


logger = logging.getLogger(__name__)

# Sentinel "tool name" representing a multi-tool answer.
CONTEXT_PACK_TOOL = "context_pack"

# Tools that make sense to combine for a broad operational picture. We avoid
# row-dump / detail tools here and prefer summarized owner views.
_CONTEXT_PACK_PREFERRED = [
    "owner.overview",
    "owner.shop_status",
    "owner.service_level",
    "owner.turnaround_times",
    "owner.redo_analysis",
]

_BROAD_QUESTION_PATTERNS = [
    "overall", "over all", "in general", "big picture", "high level", "high-level",
    "how are we doing", "how is the business", "how's the business", "how is business",
    "state of the", "health of the", "snapshot", "summary of everything",
    "across the board", "everything", "full picture", "overall picture",
    "how are things", "how's everything", "how is everything", "general overview",
    "business health", "company health", "how is the shop doing", "how's the shop",
]


def is_broad_question(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    if any(pattern in lower for pattern in _BROAD_QUESTION_PATTERNS):
        return True
    # "how are we doing" style without an explicit single metric.
    if re.search(r"\bhow (are|is|are we|is the|are the)\b", lower) and not re.search(
        r"\b(sqft|square footage|redo|turnaround|labor cost|installer|breach|sla|stalled)\b", lower
    ):
        return True
    return False


def select_context_pack_tools(question: str, max_tools: int = 4) -> list[str]:
    """Choose a diverse set of summarized tools for a broad question."""
    chosen: list[str] = []

    # Seed with deterministic suggestions that are in our preferred set.
    for item in suggest_tools_for_question(question, limit=12):
        name = item.get("tool_name")
        if name in _CONTEXT_PACK_PREFERRED and name not in chosen:
            chosen.append(name)
        if len(chosen) >= max_tools:
            break

    # Backfill from the preferred list to guarantee a useful spread.
    for name in _CONTEXT_PACK_PREFERRED:
        if len(chosen) >= max_tools:
            break
        if name not in chosen and get_report_tool_definition(name) is not None:
            chosen.append(name)

    return chosen[:max_tools]


async def run_context_pack(
    question: str,
    *,
    db: AsyncSession,
    current_user: User,
    max_tools: int = 4,
) -> dict[str, Any]:
    """Run several report tools concurrently and merge their output.

    Returns a dict with:
      - tools_run: list of tool names that succeeded
      - sections: {tool_name: {params, insights, result}}
      - insights: flattened, labeled insight lines across all tools
      - errors: {tool_name: message} for any tool that failed
    """
    tool_names = select_context_pack_tools(question, max_tools=max_tools)
    logger.info("mcp.context_pack start tools=%s question_preview=%s", tool_names, question[:120])

    async def _run_single(tool_name: str) -> tuple[str, dict[str, Any], Any]:
        params = sanitize_params_for_tool(
            tool_name,
            enrich_params_from_question(question, tool_name),
        )
        result = await invoke_report_tool(tool_name, params, db=db, current_user=current_user)
        return tool_name, params, result

    outcomes = await asyncio.gather(
        *[_run_single(name) for name in tool_names],
        return_exceptions=True,
    )

    sections: dict[str, Any] = {}
    combined_insights: list[str] = []
    errors: dict[str, str] = {}
    tools_run: list[str] = []

    for tool_name, outcome in zip(tool_names, outcomes):
        if isinstance(outcome, Exception):
            errors[tool_name] = str(outcome)
            logger.warning("mcp.context_pack tool_failed tool=%s error=%s", tool_name, outcome)
            continue
        _name, params, result = outcome
        try:
            insights = summarize_tool_result(tool_name, result)
        except Exception:
            logger.exception("mcp.context_pack summarize_failed tool=%s", tool_name)
            insights = []
        sections[tool_name] = {"params": params, "insights": insights, "result": result}
        tools_run.append(tool_name)
        for line in insights:
            combined_insights.append(f"[{tool_name}] {line}")

    logger.info("mcp.context_pack done tools_run=%s errors=%s", tools_run, list(errors.keys()))

    return {
        "tools_run": tools_run,
        "sections": sections,
        "insights": combined_insights,
        "errors": errors,
    }
