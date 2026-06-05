from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.routers import dashboard, fabs, operators, reports, shop_cut_plan


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
    if isinstance(response, dict):
        return response.get("data") or {}
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


def _parse_bounded_float(
    value: Any,
    *,
    field_name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return parsed


def _default_params_for_tool(tool_name: str) -> dict[str, Any]:
    definition = get_report_tool_definition(tool_name)
    if definition is None:
        return {}
    # `sample_params` are documentation examples, not runtime defaults.
    # If copied directly, stale sample dates (e.g. 2026-06-01..2026-06-30)
    # can force old windows for "current" questions. Runtime defaults should
    # come from explicit NL date parsing or handler-level defaults.
    return {}


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

    month_aliases = {
        name.lower(): index
        for index, name in enumerate(calendar.month_name)
        if index > 0
    }
    month_aliases.update(
        {
            abbr.lower(): index
            for index, abbr in enumerate(calendar.month_abbr)
            if index > 0
        }
    )
    month_matches = list(
        re.finditer(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b",
            lower,
        )
    )
    if month_matches:
        explicit_year_match = re.search(r"\b(20\d{2})\b", lower)
        resolved_year = int(explicit_year_match.group(1)) if explicit_year_match else today.year

        month_numbers: list[int] = []
        for match in month_matches:
            token = match.group(1)
            if token == "sept":
                token = "sep"
            month_index = month_aliases.get(token)
            if month_index and month_index not in month_numbers:
                month_numbers.append(month_index)

        if month_numbers:
            earliest_month = min(month_numbers)
            latest_month = max(month_numbers)
            # Build an inclusive date range spanning the referenced month(s) so
            # date-range tools (e.g. shop_status, overview) target the right window.
            start = date(resolved_year, earliest_month, 1)
            last_day = calendar.monthrange(resolved_year, latest_month)[1]
            end = date(resolved_year, latest_month, last_day)
            merged["start_date"] = start.isoformat()
            merged["end_date"] = end.isoformat()
            # Month/year tools use the latest referenced month.
            merged["month"] = latest_month
            merged["year"] = resolved_year

    year_match = re.search(r"\b(20\d{2})\b", lower)
    if year_match:
        merged["year"] = int(year_match.group(1))

    if "this month" in lower:
        merged["month"] = today.month
        merged["year"] = today.year
    elif "last month" in lower:
        first_of_this_month = today.replace(day=1)
        previous_month_day = first_of_this_month - timedelta(days=1)
        merged["month"] = previous_month_day.month
        merged["year"] = previous_month_day.year

    if "created basis" in lower or "created date" in lower:
        merged["date_basis"] = "created"
    elif "scheduled basis" in lower or "scheduled date" in lower:
        merged["date_basis"] = "scheduled"
    elif "completed basis" in lower or "completion date" in lower:
        merged["date_basis"] = "completed"

    activity_match = re.search(r"\b(installation|template|both)\b", lower)
    if activity_match and any(term in lower for term in ["installation template", "template report", "installer hours"]):
        merged["activity"] = activity_match.group(1)

    sla_match = re.search(r"sla\s*(\d+)", lower)
    if sla_match:
        merged["sla_days"] = int(sla_match.group(1))

    threshold_match = re.search(r"threshold\s*(\d+)", lower)
    if threshold_match:
        merged["threshold_days"] = int(threshold_match.group(1))

    # Capture day-based SLA thresholds phrased naturally, e.g. "exceed 14 days",
    # "over 14 days", "more than 14 days", "older than 14 days", "14+ days".
    if "threshold_days" not in merged or not threshold_match:
        day_threshold_match = re.search(
            r"(?:exceed(?:ing|s)?|over|more than|greater than|older than|beyond|longer than|above|past)\s+(\d+)\s*(?:\+)?\s*days",
            lower,
        )
        if not day_threshold_match:
            day_threshold_match = re.search(r"(\d+)\s*\+\s*days", lower)
        if day_threshold_match:
            merged["threshold_days"] = int(day_threshold_match.group(1))

    return merged


def _score_tools_for_question(lower: str) -> list[tuple[int, str, str]]:
    scored_tools: list[tuple[int, str, str]] = []

    def score(tool_name: str, points: int, rationale: str) -> None:
        scored_tools.append((points, tool_name, rationale))

    if any(term in lower for term in ["management packet", "full report", "full summary", "executive packet"]):
        score("owner.management_packet", 10, "Matched full-packet language in the question.")
    if any(term in lower for term in ["dashboard", "platform status", "today status", "this week status", "this month status"]):
        score("platform.dashboard", 10, "Matched platform dashboard status language.")
    if any(term in lower for term in ["stage fabs", "fabs by stage", "stage queue", "workflow stage", "final programming pending", "pending final programming"]):
        score("ops.stage_fabs", 10, "Matched workflow stage queue language.")
    if (
        any(term in lower for term in ["currently sitting", "sitting in", "in sct", "in fabrication", "manual count"]) 
        and any(term in lower for term in ["job", "jobs", "fab", "fabs", "count", "how many"])
        and any(term in lower for term in ["sct", "fabrication", "stage", "stages"])
    ):
        score("ops.stage_fabs", 11, "Matched current stage queue count language (SCT/fabrication).")
        score("owner.shop_status", 10, "Matched current shop-load count by stage language.")
    if any(term in lower for term in ["all stages", "stage counts", "stage overview"]):
        score("ops.stages_overview", 9, "Matched stage-overview language.")
    if any(term in lower for term in ["shop plans", "shop schedule", "cut plans", "workstation plans", "calendar view"]):
        score("ops.shop_plans", 10, "Matched shop planning calendar language.")
    if any(term in lower for term in ["shop plan details", "plan id", "specific plan"]):
        score("ops.shop_plan_details", 9, "Matched shop-plan detail language.")
    if any(term in lower for term in ["plans for fab", "fab plans", "has shop plans"]):
        score("ops.shop_plans_by_fab", 9, "Matched FAB-specific planning language.")
    if any(term in lower for term in ["my operator tasks", "operator tasks", "active task", "assigned tasks"]):
        score("ops.operator_my_tasks", 10, "Matched operator task workload language.")
    if any(term in lower for term in ["weekly fabrication labor", "fabrication labor cost", "shop labor cost", "weekly fab labor"]):
        score("owner.weekly_fabrication_labor_cost", 10, "Matched weekly fabrication labor-cost language.")
    if any(term in lower for term in ["weekly installer labor", "installer labor cost", "sub contractor", "cost to install per sqft"]):
        score("owner.weekly_installer_labor_cost", 10, "Matched weekly installer labor-cost language.")
    if any(term in lower for term in ["installation template", "template report", "installer hours", "template completion"]):
        score("owner.installation_template", 10, "Matched installation-template reporting language.")
    if any(term in lower for term in ["monthly install completion", "install completion by month"]):
        score("owner.monthly_install_completion", 10, "Matched monthly install completion language.")
    if any(term in lower for term in ["daily install completion", "install completion by day"]):
        score("owner.daily_install_completion", 10, "Matched daily install completion language.")
    if any(term in lower for term in ["monthly cut completion", "cut completion by month"]):
        score("owner.monthly_cut_completion", 10, "Matched monthly cut completion language.")
    if any(term in lower for term in ["turnaround", "cycle time", "fab days", "predraft days", "cnc days"]):
        score("owner.turnaround_times", 10, "Matched turnaround-time analysis language.")
    if (
        any(
            term in lower
            for term in [
                "stage-by-stage",
                "stage by stage",
                "time in stage",
                "time-in-stage",
                "days in stage",
                "days in each stage",
                "stage duration",
                "stage durations",
                "how long are fabs taking",
                "how long are jobs taking",
                "how long do fabs take",
                "how long is each stage",
                "time per stage",
            ]
        )
        or (
            any(term in lower for term in ["how long", "how many days", "duration", "taking", "time"])
            and any(term in lower for term in ["stage", "stages", "fab", "fabs", "fabrication", "step", "steps"])
        )
        or (
            re.search(r"(?:exceed(?:ing|s)?|over|more than|older than|beyond|longer than)\s+\d+\s*(?:\+)?\s*days", lower) is not None
            and any(term in lower for term in ["stage", "stages", "fab", "fabs", "fabrication", "turnaround", "cycle", "taking", "how long"])
        )
    ):
        score("owner.turnaround_times", 11, "Matched stage-duration / time-in-stage / day-threshold language.")
    if any(term in lower for term in ["service level", "sla", "breach", "bottleneck heat map", "at risk"]):
        score("owner.service_level", 10, "Matched service-level and SLA language.")
    if any(term in lower for term in ["installer rate", "hourly rate", "pay rate"]):
        score("owner.installer_rates", 9, "Matched installer-rate language.")
    if any(term in lower for term in ["ag redo", "redo rows", "redo list"]):
        score("owner.ag_redos", 9, "Matched AG redo row-level language.")
    if (
        any(
            term in lower
            for term in [
                "most square footage",
                "most sqft",
                "largest jobs",
                "largest job",
                "biggest jobs",
                "biggest job",
                "largest projects",
                "largest project",
                "highest sqft",
                "top jobs by sqft",
                "jobs by square footage",
            ]
        )
        or (
            any(term in lower for term in ["square footage", "sqft", "square feet", "largest", "biggest", "most"])
            and any(term in lower for term in ["job", "jobs", "project", "projects"])
        )
    ) and not any(term in lower for term in ["cost per sqft", "sqft per hour"]):
        score("owner.largest_jobs", 10, "Matched job-size ranking language.")
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

    return scored_tools


def suggest_tools_for_question(question: str, limit: int = 8) -> list[dict[str, Any]]:
    normalized = (question or "").strip()
    if not normalized:
        return []

    lower = normalized.lower()
    scored_tools = _score_tools_for_question(lower)
    if not scored_tools:
        return [{"tool_name": "owner.overview", "points": 1, "rationale": "Default broad question fallback."}]

    scored_tools.sort(key=lambda item: item[0], reverse=True)
    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for points, tool_name, rationale in scored_tools:
        if tool_name in seen:
            continue
        seen.add(tool_name)
        ranked.append({"tool_name": tool_name, "points": points, "rationale": rationale})
        if len(ranked) >= max(limit, 1):
            break

    return ranked


def select_tool_for_question(question: str) -> NLToolSelection:
    normalized = (question or "").strip()
    if not normalized:
        raise ValueError("question is required")

    lower = normalized.lower()
    scored_tools = _score_tools_for_question(lower)

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


def enrich_params_from_question(question: str, tool_name: str) -> dict[str, Any]:
    """Deterministically derive tool params (dates, month/year, thresholds, top_n)
    from the natural-language question.

    Used as a defaults layer so LLM-planned selections still receive reliable
    date/threshold extraction even when the model omits those params. Returned
    params are already sanitized for the target tool.
    """
    normalized = (question or "").strip()
    if not normalized or get_report_tool_definition(tool_name) is None:
        return {}
    lower = normalized.lower()
    merged = _merge_date_range_params(lower, _default_params_for_tool(tool_name))
    return sanitize_params_for_tool(tool_name, merged)


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

    if tool_name == "owner.largest_jobs":
        summary = result.get("summary") or {}
        rows = result.get("rows") or []
        if not rows:
            return ["No job-level square-footage rows were returned for the selected filters."]
        leader = rows[0]
        return [
            f"Returned {summary.get('row_count', len(rows))} ranked jobs by square footage.",
            f"Largest job is {leader.get('job_number')} - {leader.get('job_name')} with {leader.get('total_sqft', 0)} sqft.",
        ]

    if tool_name == "owner.weekly_fabrication_labor_cost":
        monthly_report = result.get("monthly_report") or {}
        totals = monthly_report.get("totals") or {}
        return [
            f"Fabrication month has {totals.get('number_of_weeks', 0)} weeks, {totals.get('completed_sqft', 0)} completed sqft, and {totals.get('gross_revenue', 0)} revenue.",
            f"Total labor cost is {totals.get('total_labor_cost', 0)} with labor cost per sqft at {totals.get('labor_cost_per_sq_ft', 0)}.",
        ]

    if tool_name == "owner.weekly_installer_labor_cost":
        monthly_report = result.get("monthly_report") or {}
        totals = monthly_report.get("totals") or {}
        return [
            f"Installer month has {totals.get('number_of_weeks', 0)} weeks, {totals.get('completed_sqft', 0)} completed sqft, and {totals.get('gross_revenue', 0)} revenue.",
            f"Total installer labor cost is {totals.get('total_labor_cost', 0)} and install cost per sqft is {totals.get('cost_to_install_per_sqft', 0)}.",
        ]

    if tool_name == "owner.installation_template":
        summary = result.get("summary") or {}
        return [
            f"Returned {summary.get('row_count', 0)} rows with {summary.get('total_installer_hours', 0)} installer hours total.",
            f"Installed sqft: {summary.get('total_sq_ft_installed', 0)}; incomplete sqft: {summary.get('total_sq_ft_incomplete', 0)}.",
        ]

    if tool_name in {"owner.monthly_install_completion", "owner.daily_install_completion", "owner.monthly_cut_completion"}:
        summary = result.get("summary") or {}
        return [
            f"Rows: {summary.get('row_count', 0)}, pieces: {summary.get('pieces', 0)}, sqft: {summary.get('sq_ft', 0)}.",
            f"Revenue: {summary.get('revenue', 0)}, GP: {summary.get('gp', 0)}, revenue/sqft: {summary.get('revenue_per_sq_ft', 0)}.",
        ]

    if tool_name == "owner.turnaround_times":
        summary = result.get("summary") or {}
        stage_averages = result.get("stage_averages") or {}
        insights = [
            f"Turnaround rows: {summary.get('row_count', 0)} with total average days {stage_averages.get('total', 'n/a')}.",
            f"Draft avg: {stage_averages.get('drafting', 'n/a')} days, CNC avg: {stage_averages.get('cnc', 'n/a')} days, cut avg: {stage_averages.get('cut', 'n/a')} days.",
        ]
        threshold_analysis = result.get("threshold_analysis") or {}
        if threshold_analysis:
            threshold_days = threshold_analysis.get("threshold_days")
            counts_by_stage = threshold_analysis.get("counts_by_stage") or {}
            total_exceeding = sum(int(count or 0) for count in counts_by_stage.values())
            insights.append(
                f"{total_exceeding} fab-stage instances exceed the {threshold_days}-day threshold across {len(counts_by_stage)} stages."
            )
            worst_stages = sorted(
                counts_by_stage.items(), key=lambda item: int(item[1] or 0), reverse=True
            )
            top_offenders = [f"{stage} ({count})" for stage, count in worst_stages if int(count or 0) > 0][:3]
            if top_offenders:
                insights.append(
                    f"Stages with the most fabs over {threshold_days} days: {', '.join(top_offenders)}."
                )
            else:
                insights.append(f"No fabs exceeded the {threshold_days}-day threshold this period.")
        return insights


    if tool_name == "owner.service_level":
        summary = result.get("summary") or {}
        widgets = result.get("widgets") or {}
        return [
            f"On-time is {summary.get('on_time_percent', 0)}% with {summary.get('sla_breach_count', 0)} SLA breaches and open backlog {summary.get('open_backlog_count', 0)}.",
            f"Risk mix: green {widgets.get('on_track_green', 0)}, yellow {widgets.get('at_risk_yellow', 0)}, red {widgets.get('overdue_red', 0)}.",
        ]

    if tool_name == "owner.installer_rates":
        rates = result.get("rates") or []
        if not rates:
            return ["No installer rates were returned for the selected filters."]
        return [
            f"Returned {len(rates)} installer rate records.",
            f"Most recent rate is {rates[0].get('hourly_rate', 0)} for {rates[0].get('installer_name', 'Unknown')}.",
        ]

    if tool_name == "owner.ag_redos":
        rows = result.get("rows") or result.get("redos") or []
        return [
            f"Returned {len(rows)} AG redo rows for detailed review.",
        ]

    if tool_name == "platform.dashboard":
        kpis = result.get("kpis") or {}
        return [
            f"Dashboard totals: {kpis.get('total_fabs', 0)} fabs, {kpis.get('total_jobs', 0)} jobs, {kpis.get('pending_installations', 0)} pending installations.",
            f"Completion rate is {kpis.get('completion_rate', 0)}% with revenue installed {kpis.get('revenue_installed', 0)}.",
        ]

    if tool_name == "ops.stage_fabs":
        rows = result.get("data") or result.get("rows") or result
        count = len(rows) if isinstance(rows, list) else 0
        return [f"Stage queue returned {count} FABs for the selected filters."]

    if tool_name == "ops.stages_overview":
        rows = result.get("stages") or result.get("data") or result
        count = len(rows) if isinstance(rows, list) else 0
        return [f"Stage overview returned {count} stage buckets."]

    if tool_name == "ops.shop_plans":
        data = result.get("data") or {}
        return [
            f"Shop plans view returned {data.get('total', 0)} plans for {data.get('view', 'week')} starting {data.get('reference_date')}.",
        ]

    if tool_name == "ops.shop_plan_details":
        data = result.get("data") or {}
        return [
            f"Plan {data.get('id')} for FAB {data.get('fab_id')} is assigned to {data.get('operator_name')} at {data.get('workstation_name')}.",
        ]

    if tool_name == "ops.shop_plans_by_fab":
        data = result.get("data") or {}
        return [
            f"FAB {data.get('fab_id')} has {data.get('total', 0)} shop plans in the selected window.",
        ]

    if tool_name == "ops.operator_my_tasks":
        return [
            f"Operator task view returned {result.get('total', 0)} tasks in {result.get('view', 'week')} mode.",
        ]

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


async def _run_owner_largest_jobs(params: dict[str, Any], db: AsyncSession, current_user: User) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    top_n = _parse_bounded_int(
        params.get("top_n"),
        field_name="top_n",
        default=20,
        minimum=1,
        maximum=500,
    )
    min_sqft = _parse_bounded_float(
        params.get("min_sqft"),
        field_name="min_sqft",
        default=0,
        minimum=0,
        maximum=10_000_000,
    )
    order_by = str(params.get("order_by") or "sqft").strip().lower()
    if order_by not in {"sqft", "revenue"}:
        raise ValueError("order_by must be one of: sqft, revenue")

    response = await reports.get_owner_largest_jobs_report(
        start_date=start_date,
        end_date=end_date,
        top_n=top_n,
        min_sqft=min_sqft,
        order_by=order_by,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_weekly_fabrication_labor_cost(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    today = date.today()
    year = _parse_bounded_int(
        params.get("year"),
        field_name="year",
        default=today.year,
        minimum=2000,
        maximum=2100,
    )
    month = _parse_bounded_int(
        params.get("month"),
        field_name="month",
        default=today.month,
        minimum=1,
        maximum=12,
    )
    total_employees = _parse_bounded_int(
        params.get("total_employees"),
        field_name="total_employees",
        default=40,
        minimum=0,
        maximum=20000,
    )
    overhead_per_week = _parse_bounded_float(
        params.get("overhead_per_week"),
        field_name="overhead_per_week",
        default=38512.69,
        minimum=0,
        maximum=10000000,
    )
    week_ending_weekday = _parse_bounded_int(
        params.get("week_ending_weekday"),
        field_name="week_ending_weekday",
        default=4,
        minimum=0,
        maximum=6,
    )
    payroll_overrides_json = params.get("payroll_overrides_json")
    response = await reports.get_owner_weekly_fabrication_labor_cost_report(
        year=year,
        month=month,
        total_employees=total_employees,
        overhead_per_week=overhead_per_week,
        week_ending_weekday=week_ending_weekday,
        payroll_overrides_json=payroll_overrides_json,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_weekly_installer_labor_cost(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    today = date.today()
    year = _parse_bounded_int(
        params.get("year"),
        field_name="year",
        default=today.year,
        minimum=2000,
        maximum=2100,
    )
    month = _parse_bounded_int(
        params.get("month"),
        field_name="month",
        default=today.month,
        minimum=1,
        maximum=12,
    )
    total_employees = _parse_bounded_int(
        params.get("total_employees"),
        field_name="total_employees",
        default=40,
        minimum=0,
        maximum=20000,
    )
    overhead_per_week = _parse_bounded_float(
        params.get("overhead_per_week"),
        field_name="overhead_per_week",
        default=38512.69,
        minimum=0,
        maximum=10000000,
    )
    week_ending_weekday = _parse_bounded_int(
        params.get("week_ending_weekday"),
        field_name="week_ending_weekday",
        default=4,
        minimum=0,
        maximum=6,
    )
    payroll_overrides_json = params.get("payroll_overrides_json")
    response = await reports.get_owner_weekly_installer_labor_cost_report(
        year=year,
        month=month,
        total_employees=total_employees,
        overhead_per_week=overhead_per_week,
        week_ending_weekday=week_ending_weekday,
        payroll_overrides_json=payroll_overrides_json,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_installation_template(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    activity = str(params.get("activity") or "both").strip().lower()
    if activity not in {"both", "installation", "template"}:
        raise ValueError("activity must be one of: both, installation, template")
    limit = _parse_bounded_int(
        params.get("limit"),
        field_name="limit",
        default=250,
        minimum=1,
        maximum=2000,
    )
    response = await reports.get_owner_installation_template_report(
        start_date=start_date,
        end_date=end_date,
        activity=activity,
        limit=limit,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_monthly_install_completion(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    today = date.today()
    year = _parse_bounded_int(
        params.get("year"),
        field_name="year",
        default=today.year,
        minimum=2000,
        maximum=2100,
    )
    month = _parse_bounded_int(
        params.get("month"),
        field_name="month",
        default=today.month,
        minimum=1,
        maximum=12,
    )
    response = await reports.get_owner_monthly_install_completion_report(
        year=year,
        month=month,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_daily_install_completion(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    response = await reports.get_owner_daily_install_completion_report(
        start_date=start_date,
        end_date=end_date,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_monthly_cut_completion(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    today = date.today()
    year = _parse_bounded_int(
        params.get("year"),
        field_name="year",
        default=today.year,
        minimum=2000,
        maximum=2100,
    )
    month = _parse_bounded_int(
        params.get("month"),
        field_name="month",
        default=today.month,
        minimum=1,
        maximum=12,
    )
    response = await reports.get_owner_monthly_cut_completion_report(
        year=year,
        month=month,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_turnaround_times(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    today = date.today()
    year = _parse_bounded_int(
        params.get("year"),
        field_name="year",
        default=today.year,
        minimum=2000,
        maximum=2100,
    )
    month = _parse_bounded_int(
        params.get("month"),
        field_name="month",
        default=today.month,
        minimum=1,
        maximum=12,
    )
    limit = _parse_bounded_int(
        params.get("limit"),
        field_name="limit",
        default=2000,
        minimum=1,
        maximum=10000,
    )
    threshold_days_raw = params.get("threshold_days")
    threshold_days = None
    if threshold_days_raw not in (None, ""):
        threshold_days = _parse_bounded_int(
            threshold_days_raw,
            field_name="threshold_days",
            default=0,
            minimum=0,
            maximum=3650,
        )
    response = await reports.get_owner_turnaround_times_report(
        year=year,
        month=month,
        limit=limit,
        threshold_days=threshold_days,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_service_level(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    start_date = _parse_optional_date(params.get("start_date"), "start_date")
    end_date = _parse_optional_date(params.get("end_date"), "end_date")
    date_basis = str(params.get("date_basis") or "completed").strip().lower()
    if date_basis not in {"created", "scheduled", "completed"}:
        raise ValueError("date_basis must be one of: created, scheduled, completed")
    sla_days = _parse_bounded_int(
        params.get("sla_days"),
        field_name="sla_days",
        default=14,
        minimum=1,
        maximum=365,
    )
    breach_limit = _parse_bounded_int(
        params.get("breach_limit"),
        field_name="breach_limit",
        default=500,
        minimum=1,
        maximum=5000,
    )
    response = await reports.get_owner_service_level_report(
        start_date=start_date,
        end_date=end_date,
        date_basis=date_basis,
        sla_days=sla_days,
        breach_limit=breach_limit,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_owner_installer_rates(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    installer_id_raw = params.get("installer_id")
    installer_id = None
    if installer_id_raw not in (None, ""):
        installer_id = _parse_bounded_int(
            installer_id_raw,
            field_name="installer_id",
            default=1,
            minimum=1,
            maximum=10_000_000,
        )
    response = await reports.get_installer_rates(
        installer_id=installer_id,
        db=db,
        current_user=current_user,
    )
    return {
        "rates": _decode_success_response(response),
    }


async def _run_owner_ag_redos(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    _ = params
    response = await reports.get_ag_redo_report(
        db=db,
        current_user=current_user,
    )
    return {
        "rows": _decode_success_response(response),
    }


async def _run_platform_dashboard(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    time_period = str(params.get("time_period") or "all").strip().lower()
    if time_period not in {"all", "today", "this_week", "this_month"}:
        raise ValueError("time_period must be one of: all, today, this_week, this_month")
    response = await dashboard.get_dashboard(
        time_period=time_period,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_ops_stage_fabs(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    stage_name = str(params.get("stage_name") or "final_programming").strip().lower()
    skip = _parse_bounded_int(params.get("skip"), field_name="skip", default=0, minimum=0, maximum=1_000_000)
    limit = _parse_bounded_int(params.get("limit"), field_name="limit", default=100, minimum=1, maximum=1000)
    job_id_raw = params.get("job_id")
    status_id_raw = params.get("status_id")
    job_id = _parse_bounded_int(job_id_raw, field_name="job_id", default=1, minimum=1, maximum=10_000_000) if job_id_raw not in (None, "") else None
    status_id = _parse_bounded_int(status_id_raw, field_name="status_id", default=1, minimum=0, maximum=10_000_000) if status_id_raw not in (None, "") else None

    if stage_name == "final_programming":
        response = await fabs.get_pending_final_programming_fabs(
            skip=skip,
            limit=limit,
            job_id=job_id,
            drafter_id=None,
            status_id=status_id,
            shop_date_start=None,
            shop_date_end=None,
            fab_type=None,
            search=None,
            type=None,
            db=db,
            current_user=current_user,
        )
    else:
        response = await fabs.get_fabs_by_stage(
            stage_name=stage_name,
            skip=skip,
            limit=limit,
            job_id=job_id,
            status_id=status_id,
            db=db,
            current_user=current_user,
        )
    return _decode_success_response(response)


async def _run_ops_stages_overview(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    _ = params
    response = await fabs.get_all_stages(
        db=db,
        current_user=current_user,
    )
    return {
        "stages": _decode_success_response(response),
    }


async def _run_ops_shop_plans(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    skip = _parse_bounded_int(params.get("skip"), field_name="skip", default=0, minimum=0, maximum=1_000_000)
    limit = _parse_bounded_int(params.get("limit"), field_name="limit", default=100, minimum=1, maximum=1000)
    view = str(params.get("view") or "week").strip().lower()
    if view not in {"day", "week", "month"}:
        raise ValueError("view must be one of: day, week, month")
    reference_date = _parse_optional_date(params.get("reference_date"), "reference_date")
    fab_id_raw = params.get("fab_id")
    workstation_id_raw = params.get("workstation_id")
    planning_section_id_raw = params.get("planning_section_id")
    status_id_raw = params.get("status_id")
    operator_id_raw = params.get("operator_id")

    fab_id = _parse_bounded_int(fab_id_raw, field_name="fab_id", default=1, minimum=1, maximum=10_000_000) if fab_id_raw not in (None, "") else None
    workstation_id = _parse_bounded_int(workstation_id_raw, field_name="workstation_id", default=1, minimum=1, maximum=10_000_000) if workstation_id_raw not in (None, "") else None
    planning_section_id = _parse_bounded_int(planning_section_id_raw, field_name="planning_section_id", default=1, minimum=1, maximum=10_000_000) if planning_section_id_raw not in (None, "") else None
    status_id = _parse_bounded_int(status_id_raw, field_name="status_id", default=1, minimum=0, maximum=10_000_000) if status_id_raw not in (None, "") else None

    operator_id = None
    if operator_id_raw not in (None, ""):
        if isinstance(operator_id_raw, list):
            parsed_ids = []
            for raw in operator_id_raw:
                parsed_ids.append(_parse_bounded_int(raw, field_name="operator_id", default=1, minimum=1, maximum=10_000_000))
            operator_id = parsed_ids
        else:
            operator_id = [_parse_bounded_int(operator_id_raw, field_name="operator_id", default=1, minimum=1, maximum=10_000_000)]

    response = await shop_cut_plan.get_all_shop_plans(
        fab_id=fab_id,
        search_fab_id=None,
        fab_type=params.get("fab_type"),
        workstation_id=workstation_id,
        planning_section_id=planning_section_id,
        operator_id=operator_id,
        status_id=status_id,
        cut_type=params.get("cut_type"),
        month=None,
        year=None,
        search=params.get("search"),
        type=params.get("type"),
        view=view,
        reference_date=reference_date,
        skip=skip,
        limit=limit,
        request=None,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_ops_shop_plan_details(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    plan_id = _parse_bounded_int(params.get("plan_id"), field_name="plan_id", default=1, minimum=1, maximum=10_000_000)
    response = await shop_cut_plan.get_shop_plan(
        plan_id=plan_id,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_ops_shop_plans_by_fab(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    fab_id = _parse_bounded_int(params.get("fab_id"), field_name="fab_id", default=1, minimum=1, maximum=10_000_000)
    month_raw = params.get("month")
    year_raw = params.get("year")
    month = _parse_bounded_int(month_raw, field_name="month", default=date.today().month, minimum=1, maximum=12) if month_raw not in (None, "") else None
    year = _parse_bounded_int(year_raw, field_name="year", default=date.today().year, minimum=2000, maximum=2100) if year_raw not in (None, "") else None
    skip = _parse_bounded_int(params.get("skip"), field_name="skip", default=0, minimum=0, maximum=1_000_000)
    limit = _parse_bounded_int(params.get("limit"), field_name="limit", default=100, minimum=1, maximum=1000)

    response = await shop_cut_plan.get_shop_plans_by_fab_id(
        fab_id=fab_id,
        month=month,
        year=year,
        skip=skip,
        limit=limit,
        db=db,
        current_user=current_user,
    )
    return _decode_success_response(response)


async def _run_ops_operator_my_tasks(
    params: dict[str, Any],
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    view = str(params.get("view") or "week").strip().lower()
    if view not in {"day", "week", "month"}:
        raise ValueError("view must be one of: day, week, month")
    reference_date = _parse_optional_date(params.get("reference_date"), "reference_date")
    active_only_raw = params.get("active_only", False)
    if isinstance(active_only_raw, bool):
        active_only = active_only_raw
    elif isinstance(active_only_raw, str):
        active_only = active_only_raw.strip().lower() in {"true", "1", "yes", "on"}
    else:
        active_only = bool(active_only_raw)
    skip = _parse_bounded_int(params.get("skip"), field_name="skip", default=0, minimum=0, maximum=1_000_000)
    limit = _parse_bounded_int(params.get("limit"), field_name="limit", default=100, minimum=1, maximum=1000)
    response = await operators.get_current_operator_tasks(
        view=view,
        reference_date=reference_date,
        active_only=active_only,
        skip=skip,
        limit=limit,
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
    "owner.largest_jobs": MCPToolDefinition(
        name="owner.largest_jobs",
        description="Return top jobs ranked by square footage with job and account context.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "top_n": {"type": "integer", "minimum": 1, "maximum": 500, "default": 20},
                "min_sqft": {"type": "number", "minimum": 0, "default": 0},
                "order_by": {"type": "string", "enum": ["sqft", "revenue"], "default": "sqft"},
            },
        },
        sample_params={"top_n": 15, "min_sqft": 0, "order_by": "sqft"},
        result_summary="Job-level ranking sorted by sqft (or revenue) with fab counts and totals.",
    ),
    "owner.weekly_fabrication_labor_cost": MCPToolDefinition(
        name="owner.weekly_fabrication_labor_cost",
        description="Return weekly fabrication labor cost analysis with monthly and annual summary tables.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100, "default": 2026},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6},
                "total_employees": {"type": "integer", "minimum": 0, "maximum": 20000, "default": 40},
                "overhead_per_week": {"type": "number", "minimum": 0, "maximum": 10000000, "default": 38512.69},
                "week_ending_weekday": {"type": "integer", "minimum": 0, "maximum": 6, "default": 4},
                "payroll_overrides_json": {"type": "string"},
            },
        },
        sample_params={"year": 2026, "month": 6, "total_employees": 40},
        result_summary="Weekly fabrication labor economics with monthly totals and annual month-by-month rollups.",
    ),
    "owner.weekly_installer_labor_cost": MCPToolDefinition(
        name="owner.weekly_installer_labor_cost",
        description="Return weekly installer labor cost analysis with monthly and annual summary tables.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100, "default": 2026},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6},
                "total_employees": {"type": "integer", "minimum": 0, "maximum": 20000, "default": 40},
                "overhead_per_week": {"type": "number", "minimum": 0, "maximum": 10000000, "default": 38512.69},
                "week_ending_weekday": {"type": "integer", "minimum": 0, "maximum": 6, "default": 4},
                "payroll_overrides_json": {"type": "string"},
            },
        },
        sample_params={"year": 2026, "month": 6, "total_employees": 40},
        result_summary="Weekly installer labor economics with install-cost indicators and annual month summaries.",
    ),
    "owner.installation_template": MCPToolDefinition(
        name="owner.installation_template",
        description="Return combined installation/template activity rows with installer hours and completion context.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "activity": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 2000, "default": 250},
            },
        },
        sample_params={"activity": "both", "limit": 250},
        result_summary="Detailed installation/template rows for personnel and completion tracking.",
    ),
    "owner.monthly_install_completion": MCPToolDefinition(
        name="owner.monthly_install_completion",
        description="Return owner monthly install completion spreadsheet-style report.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100, "default": 2026},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6},
            },
        },
        sample_params={"year": 2026, "month": 6},
        result_summary="Monthly install completion rows with daily totals and financial summary.",
    ),
    "owner.daily_install_completion": MCPToolDefinition(
        name="owner.daily_install_completion",
        description="Return owner daily install completion rows across a date range.",
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
        result_summary="Daily install completion rows and date-bucket totals for operational review.",
    ),
    "owner.monthly_cut_completion": MCPToolDefinition(
        name="owner.monthly_cut_completion",
        description="Return owner monthly cut completion spreadsheet-style report.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100, "default": 2026},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6},
            },
        },
        sample_params={"year": 2026, "month": 6},
        result_summary="Monthly cut completion rows with daily totals and financial summary.",
    ),
    "owner.turnaround_times": MCPToolDefinition(
        name="owner.turnaround_times",
        description="Return stage-by-stage turnaround metrics for fabs completed in a selected month.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100, "default": 2026},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10000, "default": 2000},
                "threshold_days": {"type": "integer", "minimum": 0, "maximum": 3650},
            },
        },
        sample_params={"year": 2026, "month": 6, "threshold_days": 14},
        result_summary="Turnaround stage durations, summaries, and optional threshold exceedance analysis.",
    ),
    "owner.service_level": MCPToolDefinition(
        name="owner.service_level",
        description="Return service-level KPI widgets, heat map, and Fab bottleneck rows with SLA logic.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "date_basis": {"type": "string"},
                "sla_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 14},
                "breach_limit": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 500},
            },
        },
        sample_params={"start_date": "2026-06-01", "end_date": "2026-06-30", "sla_days": 14},
        result_summary="Service-level compliance, stage bottlenecks, and breach details for intervention planning.",
    ),
    "owner.installer_rates": MCPToolDefinition(
        name="owner.installer_rates",
        description="Return installer hourly rate history records.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "installer_id": {"type": "integer", "minimum": 1},
            },
        },
        sample_params={},
        result_summary="Installer rate history rows for labor cost calibration.",
    ),
    "owner.ag_redos": MCPToolDefinition(
        name="owner.ag_redos",
        description="Return AG redo rows with detailed FAB/job context.",
        resource="reports",
        action="read",
        input_schema={"type": "object", "properties": {}},
        sample_params={},
        result_summary="Detailed AG redo row set for root-cause drilldowns.",
    ),
    "platform.dashboard": MCPToolDefinition(
        name="platform.dashboard",
        description="Return platform dashboard KPIs and chart-ready operational snapshots.",
        resource="reports",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "time_period": {"type": "string"},
            },
        },
        sample_params={"time_period": "all"},
        result_summary="Cross-platform KPI snapshot for all/today/this_week/this_month periods.",
    ),
    "ops.stage_fabs": MCPToolDefinition(
        name="ops.stage_fabs",
        description="Return FAB queue rows for a workflow stage, including final-programming pending queue mode.",
        resource="fabs",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "stage_name": {"type": "string"},
                "skip": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
                "job_id": {"type": "integer", "minimum": 1},
                "status_id": {"type": "integer", "minimum": 0},
            },
        },
        sample_params={"stage_name": "final_programming", "limit": 100},
        result_summary="Workflow queue rows for assignment and throughput control.",
    ),
    "ops.stages_overview": MCPToolDefinition(
        name="ops.stages_overview",
        description="Return all workflow stages and queue counts.",
        resource="fabs",
        action="read",
        input_schema={"type": "object", "properties": {}},
        sample_params={},
        result_summary="Top-level workflow stage counts for bottleneck detection.",
    ),
    "ops.shop_plans": MCPToolDefinition(
        name="ops.shop_plans",
        description="Return shop planning calendar rows with filters for workstation/operator/FAB.",
        resource="shop_cut_plan",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "view": {"type": "string"},
                "reference_date": {"type": "string", "format": "date"},
                "fab_id": {"type": "integer", "minimum": 1},
                "workstation_id": {"type": "integer", "minimum": 1},
                "planning_section_id": {"type": "integer", "minimum": 1},
                "operator_id": {"type": "integer", "minimum": 1},
                "status_id": {"type": "integer", "minimum": 0},
                "fab_type": {"type": "string"},
                "cut_type": {"type": "string"},
                "search": {"type": "string"},
                "type": {"type": "string"},
                "skip": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
            },
        },
        sample_params={"view": "week", "limit": 100},
        result_summary="Shop schedule rows and grouped plans for daily/weekly/monthly operations.",
    ),
    "ops.shop_plan_details": MCPToolDefinition(
        name="ops.shop_plan_details",
        description="Return detailed data for a specific shop plan id.",
        resource="shop_cut_plan",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "plan_id": {"type": "integer", "minimum": 1},
            },
        },
        sample_params={"plan_id": 1},
        result_summary="Single-plan details with operator, workstation, and progress fields.",
    ),
    "ops.shop_plans_by_fab": MCPToolDefinition(
        name="ops.shop_plans_by_fab",
        description="Return shop plans scoped to one FAB.",
        resource="shop_cut_plan",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "fab_id": {"type": "integer", "minimum": 1},
                "month": {"type": "integer", "minimum": 1, "maximum": 12},
                "year": {"type": "integer", "minimum": 2000, "maximum": 2100},
                "skip": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
            },
        },
        sample_params={"fab_id": 1},
        result_summary="FAB-specific planning sequence for coordination and troubleshooting.",
    ),
    "ops.operator_my_tasks": MCPToolDefinition(
        name="ops.operator_my_tasks",
        description="Return currently logged-in operator task list for day/week/month views.",
        resource="operators",
        action="read",
        input_schema={
            "type": "object",
            "properties": {
                "view": {"type": "string"},
                "reference_date": {"type": "string", "format": "date"},
                "active_only": {"type": "boolean", "default": False},
                "skip": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
            },
        },
        sample_params={"view": "week", "active_only": False},
        result_summary="Operator workload and active tasks for live floor management.",
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
    "owner.largest_jobs": _run_owner_largest_jobs,
    "owner.weekly_fabrication_labor_cost": _run_owner_weekly_fabrication_labor_cost,
    "owner.weekly_installer_labor_cost": _run_owner_weekly_installer_labor_cost,
    "owner.installation_template": _run_owner_installation_template,
    "owner.monthly_install_completion": _run_owner_monthly_install_completion,
    "owner.daily_install_completion": _run_owner_daily_install_completion,
    "owner.monthly_cut_completion": _run_owner_monthly_cut_completion,
    "owner.turnaround_times": _run_owner_turnaround_times,
    "owner.service_level": _run_owner_service_level,
    "owner.installer_rates": _run_owner_installer_rates,
    "owner.ag_redos": _run_owner_ag_redos,
    "platform.dashboard": _run_platform_dashboard,
    "ops.stage_fabs": _run_ops_stage_fabs,
    "ops.stages_overview": _run_ops_stages_overview,
    "ops.shop_plans": _run_ops_shop_plans,
    "ops.shop_plan_details": _run_ops_shop_plan_details,
    "ops.shop_plans_by_fab": _run_ops_shop_plans_by_fab,
    "ops.operator_my_tasks": _run_ops_operator_my_tasks,
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
