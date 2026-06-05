from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.routers import reports


ToolHandler = Callable[[dict[str, Any], AsyncSession, User], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class MCPToolDefinition:
    name: str
    description: str
    resource: str
    action: str
    input_schema: dict[str, Any]
    sample_params: dict[str, Any]
    result_summary: str


@dataclass(frozen=True)
class NLToolSelection:
    tool_name: str
    confidence: str
    rationale: str
    params: dict[str, Any]


def _decode_success_response(response: JSONResponse) -> dict[str, Any]:
    payload = json.loads(response.body.decode("utf-8"))
    return payload.get("data") or {}


def _parse_optional_date(value: Any, field_name: str) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO date string (YYYY-MM-DD)") from exc
    raise ValueError(f"{field_name} must be an ISO date string (YYYY-MM-DD)")


def _parse_bounded_int(
    value: Any,
    *,
    field_name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return parsed


def _default_params_for_tool(tool_name: str) -> dict[str, Any]:
    definition = get_report_tool_definition(tool_name)
    if definition is None:
        return {}
    return dict(definition.sample_params)


def _merge_date_range_params(question: str, params: dict[str, Any]) -> dict[str, Any]:
    merged = dict(params)
    lower = question.lower()
    today = date.today()

    explicit_dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", question)
    if len(explicit_dates) >= 2:
        merged["start_date"] = explicit_dates[0]
        merged["end_date"] = explicit_dates[1]
        return merged

    if "this month" in lower:
        start = today.replace(day=1)
        merged["start_date"] = start.isoformat()
        merged["end_date"] = today.isoformat()
    elif "last month" in lower:
        first_of_this_month = today.replace(day=1)
        end = first_of_this_month - timedelta(days=1)
        start = end.replace(day=1)
        merged["start_date"] = start.isoformat()
        merged["end_date"] = end.isoformat()
    elif "this week" in lower:
        start = today - timedelta(days=today.weekday())
        merged["start_date"] = start.isoformat()
        merged["end_date"] = today.isoformat()
    elif "last week" in lower:
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        merged["start_date"] = start.isoformat()
        merged["end_date"] = end.isoformat()

    day_match = re.search(r"last\s+(\d+)\s+days", lower)
    if day_match:
        days = int(day_match.group(1))
        merged["start_date"] = (today - timedelta(days=days)).isoformat()
        merged["end_date"] = today.isoformat()

    week_match = re.search(r"last\s+(\d+)\s+weeks", lower)
    if week_match:
        merged["weeks"] = int(week_match.group(1))

    top_match = re.search(r"top\s+(\d+)", lower)
    if top_match:
        merged["top_n"] = int(top_match.group(1))

    return merged


def select_tool_for_question(question: str) -> NLToolSelection:
    normalized = (question or "").strip()
    if not normalized:
        raise ValueError("question is required")

    lower = normalized.lower()
    scored_tools: list[tuple[int, str, str]] = []

    def score(tool_name: str, points: int, rationale: str) -> None:
        scored_tools.append((points, tool_name, rationale))

    if any(term in lower for term in ["management packet", "full report", "full summary", "executive packet"]):
        score("owner.management_packet", 10, "Matched full-packet language in the question.")
    if any(term in lower for term in ["specific job", "job names", "job details", "assign them", "team members", "resolve today", "who should", "stalled installation", "stalled installations", "stalled installs", "pending installations", "assign to", "assignment"]):
        score("owner.stalled_install_jobs", 10, "Matched assignment-oriented stalled install language.")
    elif "stalled" in lower and any(term in lower for term in ["job", "jobs", "details", "assign", "assignment"]):
        score("owner.stalled_install_jobs", 10, "Matched stalled install job detail language.")
    if any(term in lower for term in ["redo", "rework", "revision", "revised"]):
        score("owner.redo_analysis", 9, "Matched redo and revision terms.")
    if any(term in lower for term in ["install", "installer", "labor", "sqft per hour", "productivity"]):
        score("owner.install_performance", 8, "Matched installer productivity terms.")
    if any(term in lower for term in ["shop", "stalled", "backlog", "bottleneck", "aging", "stage load"]):
        score("owner.shop_status", 8, "Matched shop load and aging terms.")
    if any(term in lower for term in ["trend", "weekly", "over time", "trajectory"]):
        score("owner.weekly_trends", 7, "Matched weekly trend language.")
    if any(term in lower for term in ["overview", "kpi", "summary", "revenue", "gross profit", "pipeline"]):
        score("owner.overview", 6, "Matched overview and KPI terms.")

    if not scored_tools:
        tool_name = "owner.overview"
        rationale = "Defaulted to owner overview because the question was broad."
        params = _merge_date_range_params(lower, _default_params_for_tool(tool_name))
        return NLToolSelection(tool_name=tool_name, confidence="low", rationale=rationale, params=params)

    scored_tools.sort(key=lambda item: item[0], reverse=True)
    points, tool_name, rationale = scored_tools[0]
    confidence = "high" if points >= 9 else "medium"
    params = _merge_date_range_params(lower, _default_params_for_tool(tool_name))
    return NLToolSelection(tool_name=tool_name, confidence=confidence, rationale=rationale, params=params)


def summarize_tool_result(tool_name: str, result: dict[str, Any]) -> list[str]:
    if tool_name == "owner.overview":
        kpis = result.get("kpis") or {}
        stage_breakdown = result.get("stage_breakdown") or []
        top_stage = stage_breakdown[0] if stage_breakdown else None
        insights = [
            f"Total jobs: {kpis.get('total_jobs', 0)}, total fabs: {kpis.get('total_fabs', 0)}, active fabs: {kpis.get('active_fabs', 0)}.",
            f"Revenue: {kpis.get('total_revenue', 0)}, gross profit: {kpis.get('gross_profit', 0)}, gross margin: {kpis.get('gross_margin_percent', 0)}%.",
        ]
        if top_stage:
            insights.append(f"Largest stage by count is {top_stage.get('stage')} with {top_stage.get('count', 0)} fabs.")
        return insights

    if tool_name == "owner.shop_status":
        stage_status = result.get("stage_status") or []
        if not stage_status:
            return ["No shop status rows were returned for the selected period."]
        most_loaded = max(stage_status, key=lambda row: row.get("fab_count", 0))
        most_stalled = max(stage_status, key=lambda row: row.get("stalled_over_14_days", 0))
        return [
            f"Most loaded stage is {most_loaded.get('stage')} with {most_loaded.get('fab_count', 0)} fabs.",
            f"Highest stalled count is {most_stalled.get('stage')} with {most_stalled.get('stalled_over_14_days', 0)} fabs over 14 days.",
        ]

    if tool_name == "owner.stalled_install_jobs":
        summary = result.get("summary") or {}
        stalled_jobs = result.get("stalled_install_jobs") or []
        if not stalled_jobs:
            return ["No stalled install jobs were returned for the selected filters."]
        top_job = stalled_jobs[0]
        insights = [
            f"Found {summary.get('stalled_job_count', len(stalled_jobs))} stalled install jobs, including {summary.get('unassigned_count', 0)} unassigned and {summary.get('overdue_count', 0)} overdue.",
            f"Top stalled job is {top_job.get('job_number')} - {top_job.get('job_name')} at {top_job.get('age_days', 0)} days old, assigned to {top_job.get('installer_name')}.",
        ]
        if summary.get("due_today_count"):
            insights.append(f"{summary.get('due_today_count')} stalled install jobs are due today.")
        return insights

    if tool_name == "owner.redo_analysis":
        summary = result.get("summary") or {}
        top_accounts = result.get("top_accounts_with_redo") or []
        top_jobs = result.get("top_jobs_with_redo") or []
        insights = [
            f"Redo rate is {summary.get('redo_rate_percent', 0)}% across {summary.get('total_fabs', 0)} fabs, with {summary.get('revision_events', 0)} revision events.",
        ]
        if top_accounts:
            insights.append(
                f"Top redo account is {top_accounts[0].get('account_name')} with {top_accounts[0].get('redo_count', 0)} redo fabs."
            )
        if top_jobs:
            insights.append(
                f"Top redo job is {top_jobs[0].get('job_number')} - {top_jobs[0].get('job_name')} with {top_jobs[0].get('redo_count', 0)} redo fabs."
            )
        return insights

    if tool_name == "owner.install_performance":
        summary = result.get("summary") or {}
        breakdown = result.get("installer_breakdown") or []
        insights = [
            f"Portfolio installed {summary.get('total_sqft_installed', 0)} sqft in {summary.get('total_work_hours', 0)} work hours at {summary.get('portfolio_sqft_per_hour', 0)} sqft/hour.",
            f"Portfolio labor cost per sqft is {summary.get('portfolio_labor_cost_per_sqft', 0)} across {summary.get('installer_count', 0)} installers.",
        ]
        if breakdown:
            leader = breakdown[0]
            insights.append(
                f"Top installer by output is {leader.get('installer_name')} with {leader.get('sqft_installed', 0)} sqft and {leader.get('sqft_per_hour', 0)} sqft/hour."
            )
        return insights

    if tool_name == "owner.weekly_trends":
        weekly_rows = result.get("weekly_trends") or []
        if not weekly_rows:
            return ["No weekly trend rows were returned for the selected period."]
        latest = weekly_rows[-1]
        previous = weekly_rows[-2] if len(weekly_rows) > 1 else None
        insights = [
            f"Latest week starting {latest.get('week_start')} shows {latest.get('fabs_created', 0)} fabs created, {latest.get('installs_completed', 0)} installs completed, and revenue of {latest.get('revenue', 0)}.",
        ]
        if previous:
            revenue_delta = round(float(latest.get('revenue', 0) or 0) - float(previous.get('revenue', 0) or 0), 2)
            insights.append(f"Week-over-week revenue delta is {revenue_delta} compared with the previous week.")
        return insights

    if tool_name == "owner.management_packet":
        overview = result.get("overview") or {}
        redo = result.get("redo_analysis") or {}
        shop_status = result.get("shop_status") or {}
        install_perf = result.get("install_performance") or {}
        insights = []
        insights.extend(summarize_tool_result("owner.overview", overview)[:2])
        insights.extend(summarize_tool_result("owner.redo_analysis", redo)[:1])
        shop_insights = summarize_tool_result("owner.shop_status", shop_status)
        if shop_insights:
            insights.append(shop_insights[0])
        perf_insights = summarize_tool_result("owner.install_performance", install_perf)
        if perf_insights:
            insights.append(perf_insights[0])
        return insights

    return ["The tool executed successfully and returned structured BI data."]


async def _run_owner_overview(params: dict[str, Any], db: AsyncSession, current_user: User) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    response = await reports.get_owner_overview_report(
        start_date=start_date,
        end_date=end_date,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_shop_status(params: dict[str, Any], db: AsyncSession, current_user: User) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    response = await reports.get_owner_shop_status_report(
        start_date=start_date,
        end_date=end_date,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_stalled_install_jobs(params: dict[str, Any], db: AsyncSession, current_user: User) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    min_age_days = _parse_bounded_int(
        params.get("min_age_days"),
        field_name="min_age_days",
        default=0,
        minimum=0,
        maximum=3650,
    )
    top_n = _parse_bounded_int(
        params.get("top_n"),
        field_name="top_n",
        default=50,
        minimum=1,
        maximum=200,
    )
    include_assigned_raw = params.get("include_assigned", True)
    if isinstance(include_assigned_raw, bool):
        include_assigned = include_assigned_raw
    elif isinstance(include_assigned_raw, str):
        include_assigned = include_assigned_raw.strip().lower() not in {"false", "0", "no", "off"}
    else:
        include_assigned = bool(include_assigned_raw)
    response = await reports.get_owner_stalled_install_jobs_report(
        start_date=start_date,
        end_date=end_date,
        min_age_days=min_age_days,
        top_n=top_n,
        include_assigned=include_assigned,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_redo_analysis(params: dict[str, Any], db: AsyncSession, current_user: User) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    top_n = _parse_bounded_int(
        params.get("top_n"),
        field_name="top_n",
        default=10,
        minimum=1,
        maximum=50,
    )
    response = await reports.get_owner_redo_analysis_report(
        start_date=start_date,
        end_date=end_date,
        top_n=top_n,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_install_performance(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    top_n = _parse_bounded_int(
        params.get("top_n"),
        field_name="top_n",
        default=25,
        minimum=1,
        maximum=100,
    )
    response = await reports.get_owner_install_performance_report(
        start_date=start_date,
        end_date=end_date,
        top_n=top_n,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_weekly_trends(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    weeks = _parse_bounded_int(
        params.get("weeks"),
        field_name="weeks",
        default=12,
        minimum=4,
        maximum=52,
    )
    response = await reports.get_owner_weekly_trends_report(
        weeks=weeks,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_management_packet(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    weeks = _parse_bounded_int(
        params.get("weeks"),
        field_name="weeks",
        default=12,
        minimum=4,
        maximum=52,
    )
    top_n = _parse_bounded_int(
        params.get("top_n"),
        field_name="top_n",
        default=10,
        minimum=1,
        maximum=50,
    )
    response = await reports.get_owner_management_packet(
        start_date=start_date,
        end_date=end_date,
        weeks=weeks,
        top_n=top_n,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


_TOOL_DEFINITIONS: dict[str, MCPToolDefinition] = {
    "owner.overview": MCPToolDefinition(
        name="owner.overview",
        description="Return owner KPI overview across jobs, fabs, revenue, and installation pipeline.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        result_summary="KPI totals plus stage breakdown for owner review.",
    ),
    "owner.shop_status": MCPToolDefinition(
        name="owner.shop_status",
        description="Return current shop load by stage with aging and stalled-work indicators.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        result_summary="Stage counts with average age, max age, and stalled counts.",
    ),
    "owner.stalled_install_jobs": MCPToolDefinition(
        name="owner.stalled_install_jobs",
        description="Return stalled install jobs with job numbers, job names, assignment details, and due dates for dispatch.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "min_age_days": {"type": "integer", "minimum": 0, "maximum": 3650, "default": 0},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                "include_assigned": {"type": "boolean", "default": True},
            },
        },
        sample_params={"min_age_days": 0, "top_n": 26, "include_assigned": True},
        result_summary="Job-level stalled install list with assignment context and overdue signals.",
    ),
    "owner.redo_analysis": MCPToolDefinition(
        name="owner.redo_analysis",
        description="Return redo hotspots by stage, account, and job for owner analysis.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30", "top_n": 10},
        result_summary="Redo rate summary plus hotspot rankings by stage, account, and job.",
    ),
    "owner.install_performance": MCPToolDefinition(
        name="owner.install_performance",
        description="Return installer productivity and labor efficiency metrics.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30", "top_n": 15},
        result_summary="Installer productivity breakdown with sqft, labor cost, and efficiency metrics.",
    ),
    "owner.weekly_trends": MCPToolDefinition(
        name="owner.weekly_trends",
        description="Return trailing weekly revenue, gross profit, fab creation, and install completion trends.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "weeks": {"type": "integer", "minimum": 4, "maximum": 52, "default": 12},
            },
        },
        sample_params={"weeks": 12},
        result_summary="Weekly trend series for fabs created, installs completed, revenue, GP, and sqft installed.",
    ),
    "owner.management_packet": MCPToolDefinition(
        name="owner.management_packet",
        description="Return the combined owner management packet across the main BI report blocks.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "weeks": {"type": "integer", "minimum": 4, "maximum": 52, "default": 12},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30", "weeks": 12, "top_n": 10},
        result_summary="Composite BI packet with overview, redo, shop status, install performance, and weekly trends.",
    ),
}


_TOOL_HANDLERS: dict[str, ToolHandler] = {
    "owner.overview": _run_owner_overview,
    "owner.shop_status": _run_owner_shop_status,
    "owner.stalled_install_jobs": _run_owner_stalled_install_jobs,
    "owner.redo_analysis": _run_owner_redo_analysis,
    "owner.install_performance": _run_owner_install_performance,
    "owner.weekly_trends": _run_owner_weekly_trends,
    "owner.management_packet": _run_owner_management_packet,
}


def list_report_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": definition.name,
            "description": definition.description,
            "resource": definition.resource,
            "action": definition.action,
            "input_schema": definition.input_schema,
            "sample_params": definition.sample_params,
            "result_summary": definition.result_summary,
        }
        for definition in _TOOL_DEFINITIONS.values()
    ]


def get_report_tool_definition(name: str) -> MCPToolDefinition | None:
    return _TOOL_DEFINITIONS.get((name or "").strip().lower())


def sanitize_params_for_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Keep only schema-allowed params and coerce simple scalar types."""
    definition = get_report_tool_definition(tool_name)
    if definition is None:
        return {}

    properties = (definition.input_schema or {}).get("properties") or {}
    cleaned: dict[str, Any] = {}

    for key, schema in properties.items():
        if key not in params:
            continue

        value = params.get(key)
        expected_type = (schema or {}).get("type")

        if expected_type == "integer":
            try:
                cleaned[key] = int(value)
            except (TypeError, ValueError):
                continue
            continue

        if expected_type == "number":
            try:
                cleaned[key] = float(value)
            except (TypeError, ValueError):
                continue
            continue

        if expected_type == "boolean":
            if isinstance(value, bool):
                cleaned[key] = value
            elif isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "y"}:
                    cleaned[key] = True
                elif normalized in {"false", "0", "no", "n"}:
                    cleaned[key] = False
            elif isinstance(value, (int, float)):
                cleaned[key] = bool(value)
            continue

        # Default to string for any text/date field.
        if value is not None:
            cleaned[key] = str(value)

    return cleaned


async def invoke_report_tool(
    name: str,
    params: dict[str, Any],
    *,
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    normalized_name = (name or "").strip().lower()
    handler = _TOOL_HANDLERS.get(normalized_name)
    if handler is None:
        raise KeyError(normalized_name)
    return await handler(params or {}, db, current_user)
