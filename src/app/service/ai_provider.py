from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from src.app.mcp.report_tools import NLToolSelection, get_report_tool_definition, sanitize_params_for_tool


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIPlannerResult:
    selection: NLToolSelection
    provider: str
    model: str


@dataclass(frozen=True)
class AIAdvisorResult:
    advisor: dict[str, Any]
    provider: str
    model: str


def _is_enabled() -> bool:
    return os.getenv("MCP_AI_ENABLE_LLM", "false").strip().lower() in {"1", "true", "yes", "on"}


def _key_present(value: str) -> bool:
    return bool((value or "").strip())


def _int_env(name: str, default: int, minimum: int = 1, maximum: int = 65535) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        parsed = int(raw_value)
    except ValueError:
        return default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed


def _extract_json_object(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    text = text.strip()

    # Handle fenced responses like ```json ... ```
    if text.startswith("```"):
        fence_end = text.rfind("```")
        if fence_end > 2:
            inner = text[3:fence_end].strip()
            if inner.lower().startswith("json"):
                inner = inner[4:].strip()
            text = inner

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    # Try parsing the first balanced JSON object in the text.
    in_string = False
    escaped = False
    depth = 0
    start_idx = -1
    for idx, ch in enumerate(text):
        if ch == "\\" and in_string:
            escaped = not escaped
            continue
        if ch == '"' and not escaped:
            in_string = not in_string
        escaped = False

        if in_string:
            continue

        if ch == "{":
            if depth == 0:
                start_idx = idx
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start_idx >= 0:
                candidate = text[start_idx : idx + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _anthropic_agent_id() -> str:
    return os.getenv("ANTHROPIC_AGENT_ID", "").strip()


def _extract_text_from_anthropic_payload(parsed: dict[str, Any]) -> str:
    if not isinstance(parsed, dict):
        return ""

    direct_text = parsed.get("output_text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text

    text_parts: list[str] = []

    content = parsed.get("content")
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_text = block.get("text")
            if isinstance(block_text, str) and block_text.strip():
                text_parts.append(block_text)
                continue
            nested_content = block.get("content")
            if isinstance(nested_content, list):
                for nested_block in nested_content:
                    if isinstance(nested_block, dict):
                        nested_text = nested_block.get("text")
                        if isinstance(nested_text, str) and nested_text.strip():
                            text_parts.append(nested_text)

    if text_parts:
        return "\n".join(text_parts)

    result = parsed.get("result")
    if isinstance(result, dict):
        nested_text = _extract_text_from_anthropic_payload(result)
        if nested_text:
            return nested_text

    return ""


def _call_anthropic_agent_json(
    prompt: str,
    timeout_seconds: int,
    *,
    max_tokens: Optional[int] = None,
    phase: str,
) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    agent_id = _anthropic_agent_id()
    if not api_key or not agent_id:
        logger.info(
            "mcp.ai anthropic_agent_skipped phase=%s key_present=%s agent_id_present=%s",
            phase,
            _key_present(api_key),
            bool(agent_id),
        )
        return None

    endpoint = os.getenv(
        "ANTHROPIC_AGENT_ENDPOINT",
        f"https://api.anthropic.com/v1/agents/{urllib.parse.quote(agent_id)}/messages",
    ).strip()
    model_hint = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()
    max_token_budget = max_tokens or _int_env("MCP_AI_ADVISOR_MAX_TOKENS", 1200, minimum=256, maximum=8192)

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_token_budget,
        "temperature": 0,
        "metadata": {
            "phase": phase,
            "model_hint": model_hint,
        },
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    beta_header = os.getenv("ANTHROPIC_BETA_HEADER", "").strip()
    if beta_header:
        headers["anthropic-beta"] = beta_header

    logger.info(
        "mcp.ai anthropic_agent_request_start phase=%s endpoint=%s agent_id=%s beta_header_present=%s max_tokens=%s",
        phase,
        endpoint,
        agent_id,
        bool(beta_header),
        max_token_budget,
    )

    parsed = _post_json(endpoint, payload, headers, timeout_seconds)
    if not parsed:
        logger.warning(
            "mcp.ai anthropic_agent_no_payload phase=%s agent_id=%s endpoint=%s",
            phase,
            agent_id,
            endpoint,
        )
        return None

    text = _extract_text_from_anthropic_payload(parsed)
    output = _extract_json_object(text)
    if output is None:
        logger.warning(
            "mcp.ai anthropic_agent_invalid_json phase=%s agent_id=%s text_preview=%s",
            phase,
            agent_id,
            text[:300],
        )
        return None

    logger.info("mcp.ai anthropic_agent_request_success phase=%s agent_id=%s", phase, agent_id)

    return output, f"agent:{agent_id}"


def _build_planner_prompt(question: str, tool_catalog: list[dict[str, Any]]) -> str:
    catalog_lines = []
    for tool in tool_catalog:
        schema = tool.get("input_schema") or {}
        params = list((schema.get("properties") or {}).keys())
        catalog_lines.append(f"- {tool.get('name')} | params: {', '.join(params) if params else 'none'}")

    return (
        "Return a single JSON object only. No markdown. No explanations.\n"
        '{"tool_name":"string","confidence":"high|medium|low","rationale":"string","params":{}}\n'
        "Rules: choose exactly one allowlisted tool; params must only use allowed keys; keep rationale under 12 words.\n"
        f"Tools:\n{chr(10).join(catalog_lines)}\n"
        f"Question: {question}\n"
    )


def _build_advisor_prompt(
    question: str,
    tool_name: str,
    resolved_params: dict[str, Any],
    insights: list[str],
    result: dict[str, Any],
    *,
    response_mode: str,
    focus: str,
) -> str:
    evidence_summary = _build_evidence_summary(result, insights)
    style_instruction = {
        "brief": "Keep total output compact and prioritize the most critical points.",
        "standard": "Provide balanced detail across findings, risks, and actions.",
        "deep": "Provide comprehensive detail with nuanced metric and risk breakdown.",
    }.get(response_mode, "Provide balanced detail across findings, risks, and actions.")

    payload = {
        "question": question,
        "tool_name": tool_name,
        "resolved_params": resolved_params,
        "insights": insights,
        "focus": focus,
        "response_mode": response_mode,
        "evidence_summary": evidence_summary,
        "result_preview": _build_result_preview(result),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        "You are an operations advisor for a granite fabrication business.\n"
        "Write a practical, decision-ready response based only on provided data.\n"
        "Do not invent facts. Do not mention that you are an AI.\n"
        "Return a single JSON object only.\n"
        '{"executive_summary":"string","what_this_means":"string","key_findings":["string"],"metric_breakdown":["string"],"risk_flags":["string"],"recommended_actions":["string"],"assumptions_and_gaps":["string"],"next_questions":["string"],"priority":"high|medium|low","conversation_reply":"string","evidence":["string"]}\n'
        "Rules:\n"
        "- Answer first, then explain.\n"
        "- Include quantified findings when numbers are available.\n"
        "- Include explicit gaps when data is missing.\n"
        "- Keep recommendations actionable and prioritized.\n"
        "- Evidence must reference concrete keys from context (example: summary.row_count, rows[0].total_sqft).\n"
        f"- {style_instruction}\n"
        f"Context:\n{payload_json}\n"
    )


def _build_result_preview(result: dict[str, Any], max_list_items: int = 5, max_keys: int = 12) -> dict[str, Any]:
    preview: dict[str, Any] = {}
    for idx, (key, value) in enumerate((result or {}).items()):
        if idx >= max_keys:
            break
        if isinstance(value, list):
            preview[key] = value[:max_list_items]
        elif isinstance(value, dict):
            preview[key] = {k: value[k] for k in list(value.keys())[:max_keys]}
        else:
            preview[key] = value
    return preview


def _build_evidence_summary(result: dict[str, Any], insights: list[str]) -> dict[str, Any]:
    row_collections: list[dict[str, Any]] = []
    key_metrics: dict[str, Any] = {}
    for key, value in (result or {}).items():
        if isinstance(value, list):
            row_collections.append({"key": key, "count": len(value)})
            if value and isinstance(value[0], dict):
                row_collections[-1]["sample_keys"] = list(value[0].keys())[:8]
        elif isinstance(value, dict) and key in {"summary", "kpis", "filters", "period"}:
            numeric_items = {
                nested_key: nested_value
                for nested_key, nested_value in value.items()
                if isinstance(nested_value, (int, float))
            }
            if numeric_items:
                key_metrics[key] = numeric_items

    missing_signals: list[str] = []
    if not row_collections:
        missing_signals.append("no_row_collections_detected")
    if not key_metrics:
        missing_signals.append("no_numeric_metric_blocks_detected")

    return {
        "insights": insights,
        "row_collections": row_collections[:12],
        "key_metrics": key_metrics,
        "missing_signals": missing_signals,
    }


def _call_json_claude(
    prompt: str,
    timeout_seconds: int,
    *,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    resolved_model = (model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")).strip()
    resolved_max_tokens = max_tokens or _int_env("MCP_AI_ADVISOR_MAX_TOKENS", 1200, minimum=256, maximum=8192)
    if not api_key:
        logger.info("mcp.ai claude_advisor_skipped reason=missing_api_key")
        return None

    try:
        agent_result = _call_anthropic_agent_json(
            prompt,
            timeout_seconds,
            max_tokens=resolved_max_tokens,
            phase="advisor",
        )
        if agent_result is not None:
            logger.info("mcp.ai advisor_success_via_agent model=%s", agent_result[1])
            return agent_result

        logger.info(
            "mcp.ai claude_advisor_messages_request_start model=%s timeout=%s max_tokens=%s",
            resolved_model,
            timeout_seconds,
            resolved_max_tokens,
        )
        payload = {
            "model": resolved_model,
            "max_tokens": resolved_max_tokens,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        parsed = _post_json("https://api.anthropic.com/v1/messages", payload, headers, timeout_seconds)
        if not parsed:
            logger.warning(
                "mcp.ai claude_advisor_messages_no_payload model=%s timeout=%s",
                resolved_model,
                timeout_seconds,
            )
            return None

        content = parsed.get("content") or []
        if not content or not isinstance(content, list):
            logger.warning("mcp.ai claude_advisor_messages_empty_content model=%s", resolved_model)
            return None
        text_chunks = [chunk.get("text", "") for chunk in content if isinstance(chunk, dict)]
        output = _extract_json_object("\n".join(text_chunks))
        if output is None:
            logger.warning("mcp.ai claude_advisor_messages_invalid_json model=%s", resolved_model)
            return None
        logger.info("mcp.ai claude_advisor_messages_success model=%s", resolved_model)
        return output, resolved_model
    except Exception:
        logger.exception(
            "mcp.ai claude_advisor_exception model=%s timeout=%s agent_id_present=%s",
            resolved_model,
            timeout_seconds,
            bool(_anthropic_agent_id()),
        )
        return None


def _call_json_gemini(
    prompt: str,
    timeout_seconds: int,
    *,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    resolved_model = (model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")).strip()
    max_output_tokens = max_tokens or _int_env("MCP_AI_ADVISOR_MAX_TOKENS", 1024, minimum=256, maximum=8192)
    if not api_key:
        return None

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(resolved_model)}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "executive_summary": {"type": "STRING"},
                    "what_this_means": {"type": "STRING"},
                    "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "metric_breakdown": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "risk_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "recommended_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "assumptions_and_gaps": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "next_questions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "priority": {"type": "STRING", "enum": ["high", "medium", "low"]},
                    "conversation_reply": {"type": "STRING"},
                    "evidence": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": [
                    "executive_summary",
                    "what_this_means",
                    "key_findings",
                    "metric_breakdown",
                    "risk_flags",
                    "recommended_actions",
                    "assumptions_and_gaps",
                    "next_questions",
                    "priority",
                    "conversation_reply",
                    "evidence",
                ],
            },
        },
    }
    headers = {"content-type": "application/json"}
    parsed = _post_json(endpoint, payload, headers, timeout_seconds)
    if not parsed:
        return None

    try:
        logger.info("mcp.ai advisor_raw_response model=%s payload=%s", resolved_model, json.dumps(parsed))
    except (TypeError, ValueError):
        logger.info("mcp.ai advisor_raw_response model=%s payload=%s", resolved_model, str(parsed))

    candidates = parsed.get("candidates") or []
    if not candidates:
        return None
    first = candidates[0] if isinstance(candidates[0], dict) else {}
    content = first.get("content") or {}
    parts = content.get("parts") or []
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
    output = _extract_json_object(text)
    if output is None:
        return None
    return output, resolved_model


def _normalize_advisor_output(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    summary = str(raw.get("executive_summary") or raw.get("summary") or "").strip()
    what_this_means = str(raw.get("what_this_means") or "").strip()
    key_findings = raw.get("key_findings") if isinstance(raw.get("key_findings"), list) else []
    metric_breakdown = raw.get("metric_breakdown") if isinstance(raw.get("metric_breakdown"), list) else []
    risk_flags = raw.get("risk_flags") if isinstance(raw.get("risk_flags"), list) else []
    likely_causes = raw.get("likely_causes") if isinstance(raw.get("likely_causes"), list) else []
    recommended_actions = raw.get("recommended_actions") if isinstance(raw.get("recommended_actions"), list) else []
    assumptions_and_gaps = raw.get("assumptions_and_gaps") if isinstance(raw.get("assumptions_and_gaps"), list) else []
    next_questions = raw.get("next_questions") if isinstance(raw.get("next_questions"), list) else []
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), list) else []
    priority = str(raw.get("priority") or "medium").strip().lower()
    if priority not in {"high", "medium", "low"}:
        priority = "medium"
    follow_up_question = str(raw.get("follow_up_question") or "").strip()
    conversation_reply = str(raw.get("conversation_reply") or "").strip()

    if not summary or not what_this_means or not conversation_reply:
        return None

    normalized_key_findings = [str(item).strip() for item in key_findings if str(item).strip()]
    if not normalized_key_findings:
        normalized_key_findings = [summary]

    normalized_metric_breakdown = [str(item).strip() for item in metric_breakdown if str(item).strip()]
    normalized_risk_flags = [str(item).strip() for item in risk_flags if str(item).strip()]
    if not normalized_risk_flags:
        normalized_risk_flags = [str(item).strip() for item in likely_causes if str(item).strip()]

    normalized_recommended_actions = [str(item).strip() for item in recommended_actions if str(item).strip()]
    normalized_assumptions_and_gaps = [str(item).strip() for item in assumptions_and_gaps if str(item).strip()]
    normalized_next_questions = [str(item).strip() for item in next_questions if str(item).strip()]
    if not normalized_next_questions and follow_up_question:
        normalized_next_questions = [follow_up_question]

    normalized_evidence = [str(item).strip() for item in evidence if str(item).strip()]
    if not normalized_evidence:
        normalized_evidence = ["insights[0]"]

    return {
        "executive_summary": summary,
        "what_this_means": what_this_means,
        "key_findings": normalized_key_findings,
        "metric_breakdown": normalized_metric_breakdown,
        "risk_flags": normalized_risk_flags,
        "recommended_actions": normalized_recommended_actions,
        "assumptions_and_gaps": normalized_assumptions_and_gaps,
        "next_questions": normalized_next_questions,
        "evidence": normalized_evidence,
        "priority": priority,
        "conversation_reply": conversation_reply,
        # Backward-compatible aliases for existing clients.
        "summary": summary,
        "likely_causes": normalized_risk_flags,
        "follow_up_question": normalized_next_questions[0] if normalized_next_questions else "",
    }


def _build_local_advisor_output(
    question: str,
    tool_name: str,
    insights: list[str],
    result: dict[str, Any],
    *,
    response_mode: str,
    focus: str,
) -> dict[str, Any]:
    summary = " ".join(insights[:2]).strip()
    if not summary:
        summary = "The report returned structured operational data."

    what_this_means = "This suggests a workflow bottleneck that should be reviewed at the busiest stage first."
    likely_causes: list[str] = [
        "Work is entering this stage faster than it is leaving it.",
        "Upstream handoffs may be delayed or incomplete.",
    ]
    recommended_actions: list[str] = [
        "Review aging work in the busiest stage daily.",
        "Check upstream handoff quality for missing or incomplete jobs.",
        "Align capacity, scheduling, and follow-up on stalled work.",
    ]
    priority = "high"

    if tool_name == "owner.shop_status":
        stage_status = result.get("stage_status") or []
        if stage_status:
            most_loaded = max(stage_status, key=lambda row: row.get("fab_count", 0))
            most_stalled = max(stage_status, key=lambda row: row.get("stalled_over_14_days", 0))
            stage = most_loaded.get("stage")
            stalled_stage = most_stalled.get("stage")
            summary = (
                f"{stage} is the main bottleneck with {most_loaded.get('fab_count', 0)} fabs, while {stalled_stage} has the highest stalled count."
            )
            what_this_means = (
                f"Work is backing up late in the flow, which usually means downstream capacity or upstream handoff discipline needs attention."
            )
            likely_causes = [
                f"{stage} is absorbing more work than the team can clear quickly.",
                "Earlier stages may be releasing work before downstream capacity is ready.",
                "Aging work may not be getting escalated fast enough.",
            ]
            recommended_actions = [
                f"Triage {stage} daily and clear the oldest items first.",
                "Review handoff criteria from upstream stages so work arrives cleaner.",
                "Set a weekly limit for aged work and escalations.",
            ]

    if tool_name == "owner.redo_analysis":
        summary_data = result.get("summary") or {}
        summary = (
            f"Redo is running at {summary_data.get('redo_rate_percent', 0)}% across {summary_data.get('total_fabs', 0)} fabs."
        )
        what_this_means = "Rework is concentrated enough to affect throughput and likely points to a process or handoff issue."
        likely_causes = [
            "Incomplete or inconsistent upstream information.",
            "Quality issues are getting discovered late.",
            "A few accounts or jobs may be creating repeated churn.",
        ]
        recommended_actions = [
            "Review the top redo accounts and jobs with the team.",
            "Standardize handoff checks before work moves downstream.",
            "Track repeat redo causes weekly until the pattern drops.",
        ]

    follow_up_question = "Do you want me to break this down by account, stage, or week?"
    conversation_reply = (
        f"{summary} {what_this_means} Recommended next steps: "
        + "; ".join(recommended_actions[:3])
    ).strip()

    evidence_summary = _build_evidence_summary(result, insights)
    metric_breakdown = [f"{item.get('key')}: {item.get('count')} rows" for item in evidence_summary.get("row_collections", [])]
    assumptions_and_gaps = []
    if evidence_summary.get("missing_signals"):
        assumptions_and_gaps = [
            "Some requested breakdown fields are not present in the selected tool result.",
            "Consider running a more specific ranking/detail tool for deeper attribution.",
        ]

    return {
        "executive_summary": summary,
        "summary": summary,
        "what_this_means": what_this_means,
        "key_findings": [summary],
        "metric_breakdown": metric_breakdown,
        "risk_flags": likely_causes,
        "likely_causes": likely_causes,
        "recommended_actions": recommended_actions,
        "assumptions_and_gaps": assumptions_and_gaps,
        "next_questions": [follow_up_question],
        "evidence": ["insights[0]", "evidence_summary.row_collections"],
        "priority": priority,
        "follow_up_question": follow_up_question,
        "conversation_reply": conversation_reply,
        "question": question,
        "response_mode": response_mode,
        "focus": focus,
    }


def _normalize_response_mode(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"brief", "standard", "deep"}:
        return normalized
    env_default = os.getenv("MCP_AI_ADVISOR_DETAIL_LEVEL", "standard").strip().lower()
    if env_default in {"brief", "standard", "deep"}:
        return env_default
    return "standard"


def _normalize_focus(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"finance", "operations", "dispatch", "quality", "mixed"}:
        return normalized
    return "mixed"


def _advisor_max_tokens_for_mode(response_mode: str) -> int:
    base = _int_env("MCP_AI_ADVISOR_MAX_TOKENS", 1200, minimum=256, maximum=8192)
    if response_mode == "brief":
        return min(base, 900)
    if response_mode == "deep":
        return _int_env("MCP_AI_ADVISOR_MAX_TOKENS_DEEP", min(base + 1200, 8192), minimum=512, maximum=8192)
    return base


async def maybe_generate_advisor_response(
    question: str,
    tool_name: str,
    resolved_params: dict[str, Any],
    insights: list[str],
    result: dict[str, Any],
    *,
    response_mode: str = "standard",
    focus: str = "mixed",
) -> Optional[AIAdvisorResult]:
    if not _is_enabled():
        return None

    timeout_seconds = int(os.getenv("MCP_AI_TIMEOUT_SECONDS", "20") or 20)
    normalized_response_mode = _normalize_response_mode(response_mode)
    normalized_focus = _normalize_focus(focus)
    advisor_max_tokens = _advisor_max_tokens_for_mode(normalized_response_mode)
    primary = os.getenv("MCP_AI_PRIMARY_PROVIDER", "gemini").strip().lower()
    secondary = os.getenv("MCP_AI_SECONDARY_PROVIDER", "gemini").strip().lower()
    provider_order = [p for p in [primary, secondary] if p in {"claude", "gemini"}]
    provider_order = list(dict.fromkeys(provider_order))
    if not provider_order:
        provider_order = ["gemini", "claude"]

    prompt = _build_advisor_prompt(
        question,
        tool_name,
        resolved_params,
        insights,
        result,
        response_mode=normalized_response_mode,
        focus=normalized_focus,
    )
    logger.info(
        "mcp.ai advisor_start primary=%s secondary=%s order=%s timeout=%s tool_name=%s response_mode=%s focus=%s question_preview=%s",
        primary,
        secondary,
        provider_order,
        timeout_seconds,
        tool_name,
        normalized_response_mode,
        normalized_focus,
        question[:120],
    )

    for provider in provider_order:
        try:
            if provider == "gemini":
                candidate = await asyncio.to_thread(
                    _call_json_gemini,
                    prompt,
                    timeout_seconds,
                    max_tokens=advisor_max_tokens,
                )
            else:
                candidate = await asyncio.to_thread(
                    _call_json_claude,
                    prompt,
                    timeout_seconds,
                    max_tokens=advisor_max_tokens,
                )
        except Exception:
            logger.exception("mcp.ai advisor_provider_exception provider=%s", provider)
            candidate = None

        if not candidate:
            logger.info("mcp.ai advisor_provider_no_candidate provider=%s", provider)
            continue

        raw_advisor, model = candidate
        normalized = _normalize_advisor_output(raw_advisor)
        if normalized is None:
            logger.info("mcp.ai advisor_provider_invalid_output provider=%s model=%s", provider, model)
            continue

        normalized["response_mode"] = normalized_response_mode
        normalized["focus"] = normalized_focus
        logger.info(
            "mcp.ai advisor_success provider=%s model=%s tool_name=%s response_mode=%s focus=%s",
            provider,
            model,
            tool_name,
            normalized_response_mode,
            normalized_focus,
        )
        return AIAdvisorResult(advisor=normalized, provider=provider, model=model)

    logger.info("mcp.ai advisor_fallback_rule_based reason=no_valid_provider_result tool_name=%s", tool_name)
    return AIAdvisorResult(
        advisor=_build_local_advisor_output(
            question,
            tool_name,
            insights,
            result,
            response_mode=normalized_response_mode,
            focus=normalized_focus,
        ),
        provider="local",
        model="rule-based",
    )


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout_seconds: int) -> Optional[dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            logger.info("mcp.ai provider_http_success url=%s timeout=%s", url, timeout_seconds)
            return parsed if isinstance(parsed, dict) else None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        logger.warning(
            "mcp.ai provider_http_error url=%s status=%s reason=%s body_preview=%s",
            url,
            getattr(exc, "code", None),
            getattr(exc, "reason", None),
            (body or "")[:300],
        )
        return None
    except urllib.error.URLError as exc:
        logger.warning("mcp.ai provider_network_error url=%s reason=%s", url, getattr(exc, "reason", None))
        return None
    except TimeoutError:
        logger.warning("mcp.ai provider_timeout url=%s timeout=%s", url, timeout_seconds)
        return None
    except json.JSONDecodeError:
        logger.warning("mcp.ai provider_json_decode_error url=%s", url)
        return None


def _call_claude(question: str, tool_catalog: list[dict[str, Any]], timeout_seconds: int) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()
    if not api_key:
        logger.info("mcp.ai claude_skipped reason=missing_api_key")
        return None

    try:
        logger.info(
            "mcp.ai claude_request_start model=%s timeout=%s tool_count=%s question_preview=%s",
            model,
            timeout_seconds,
            len(tool_catalog),
            question[:120],
        )

        planner_prompt = _build_planner_prompt(question, tool_catalog)
        agent_result = _call_anthropic_agent_json(
            planner_prompt,
            timeout_seconds,
            max_tokens=2048,
            phase="planner",
        )
        if agent_result is not None:
            logger.info("mcp.ai planner_success_via_agent model=%s", agent_result[1])
            return agent_result

        logger.info(
            "mcp.ai claude_planner_messages_request_start model=%s timeout=%s max_tokens=4096",
            model,
            timeout_seconds,
        )
        payload = {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": planner_prompt}
            ],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        parsed = _post_json("https://api.anthropic.com/v1/messages", payload, headers, timeout_seconds)
        if not parsed:
            logger.warning("mcp.ai claude_request_no_payload model=%s", model)
            return None

        content = parsed.get("content") or []
        if not content or not isinstance(content, list):
            logger.warning("mcp.ai claude_empty_content model=%s", model)
            return None
        text_chunks = [chunk.get("text", "") for chunk in content if isinstance(chunk, dict)]
        output = _extract_json_object("\n".join(text_chunks))
        if output is None:
            logger.warning("mcp.ai claude_invalid_json_response model=%s", model)
            return None
        logger.info("mcp.ai claude_request_success model=%s", model)
        return output, model
    except Exception:
        logger.exception(
            "mcp.ai claude_planner_exception model=%s timeout=%s agent_id_present=%s",
            model,
            timeout_seconds,
            bool(_anthropic_agent_id()),
        )
        return None


def _call_gemini(question: str, tool_catalog: list[dict[str, Any]], timeout_seconds: int) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    if not api_key:
        logger.info("mcp.ai gemini_skipped reason=missing_api_key")
        return None

    logger.info(
        "mcp.ai gemini_request_start model=%s timeout=%s tool_count=%s key_present=%s question_preview=%s",
        model,
        timeout_seconds,
        len(tool_catalog),
        _key_present(api_key),
        question[:120],
    )

    def _request_for_model(request_model: str) -> Optional[tuple[dict[str, Any], str]]:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{urllib.parse.quote(request_model)}:generateContent?key={urllib.parse.quote(api_key)}"
        )
        payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _build_planner_prompt(question, tool_catalog)}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "tool_name": {"type": "STRING"},
                    "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
                    "rationale": {"type": "STRING"},
                    "params": {"type": "OBJECT"},
                },
                "required": ["tool_name", "confidence", "rationale", "params"],
            },
        },
        }
        headers = {"content-type": "application/json"}
        parsed = _post_json(endpoint, payload, headers, timeout_seconds)
        if not parsed:
            logger.info("mcp.ai gemini_request_no_payload model=%s", request_model)
            return None

        try:
            logger.info("mcp.ai gemini_raw_response model=%s payload=%s", request_model, json.dumps(parsed))
        except (TypeError, ValueError):
            logger.info("mcp.ai gemini_raw_response model=%s payload=%s", request_model, str(parsed))

        candidates = parsed.get("candidates") or []
        if not candidates:
            logger.info("mcp.ai gemini_empty_candidates model=%s", request_model)
            return None

        first = candidates[0] if isinstance(candidates[0], dict) else {}
        finish_reason = first.get("finishReason")
        logger.info("mcp.ai gemini_finish_reason model=%s finish_reason=%s", request_model, finish_reason)

        content = first.get("content") or {}
        parts = content.get("parts") or []
        text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
        output = _extract_json_object(text)
        if output is None:
            logger.info(
                "mcp.ai gemini_invalid_json_response model=%s finish_reason=%s response_preview=%s",
                request_model,
                finish_reason,
                text[:300],
            )
            return None

        logger.info("mcp.ai gemini_request_success model=%s", request_model)
        return output, request_model

    first_try = _request_for_model(model)
    if first_try is not None:
        return first_try

    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "").strip()
    if fallback_model and fallback_model != model:
        logger.info("mcp.ai gemini_retry_with_fallback_model from=%s to=%s", model, fallback_model)
        return _request_for_model(fallback_model)

    return None


def _normalize_selection(raw: dict[str, Any], provider: str) -> Optional[NLToolSelection]:
    tool_name = str(raw.get("tool_name") or "").strip().lower()
    if not tool_name or get_report_tool_definition(tool_name) is None:
        logger.info("mcp.ai planner_invalid_tool provider=%s tool_name=%s", provider, tool_name)
        return None

    confidence = str(raw.get("confidence") or "medium").strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    rationale = str(raw.get("rationale") or f"Planned by {provider}.").strip()
    params = raw.get("params") if isinstance(raw.get("params"), dict) else {}
    cleaned_params = sanitize_params_for_tool(tool_name, params)

    return NLToolSelection(
        tool_name=tool_name,
        confidence=confidence,
        rationale=rationale,
        params=cleaned_params,
    )


async def maybe_plan_tool_with_llm(question: str, tool_catalog: list[dict[str, Any]]) -> Optional[AIPlannerResult]:
    """Attempt provider-based planning; return None when disabled/unavailable/invalid.

    This function never raises by design so callers can safely fallback.
    """
    enabled = _is_enabled()
    if not enabled:
        logger.info("mcp.ai planner_disabled")
        return None

    timeout_seconds = int(os.getenv("MCP_AI_TIMEOUT_SECONDS", "20") or 20)
    primary = os.getenv("MCP_AI_PRIMARY_PROVIDER", "claude").strip().lower()
    secondary = os.getenv("MCP_AI_SECONDARY_PROVIDER", "gemini").strip().lower()
    provider_order = [p for p in [primary, secondary] if p in {"claude", "gemini"}]
    provider_order = list(dict.fromkeys(provider_order))
    if not provider_order:
        provider_order = ["claude", "gemini"]

    logger.info(
        "mcp.ai planner_start enabled=%s primary=%s secondary=%s order=%s timeout=%s tool_count=%s question_preview=%s",
        enabled,
        primary,
        secondary,
        provider_order,
        timeout_seconds,
        len(tool_catalog),
        question[:120],
    )

    for provider in provider_order:
        try:
            if provider == "claude":
                candidate = await asyncio.to_thread(_call_claude, question, tool_catalog, timeout_seconds)
            else:
                candidate = await asyncio.to_thread(_call_gemini, question, tool_catalog, timeout_seconds)
        except Exception:
            logger.exception("mcp.ai planner_provider_exception provider=%s", provider)
            candidate = None

        if not candidate:
            logger.info("mcp.ai planner_provider_no_candidate provider=%s", provider)
            continue

        raw_selection, model = candidate
        normalized = _normalize_selection(raw_selection, provider)
        if normalized is None:
            logger.info("mcp.ai planner_provider_invalid_selection provider=%s", provider)
            continue

        logger.info(
            "mcp.ai planner_success provider=%s model=%s tool_name=%s confidence=%s",
            provider,
            model,
            normalized.tool_name,
            normalized.confidence,
        )
        return AIPlannerResult(selection=normalized, provider=provider, model=model)

    logger.info("mcp.ai planner_fallback_to_deterministic reason=no_valid_provider_result")
    return None
