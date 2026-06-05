from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from src.app.mcp.report_tools import NLToolSelection, get_report_tool_definition, sanitize_params_for_tool


@dataclass(frozen=True)
class AIPlannerResult:
    selection: NLToolSelection
    provider: str
    model: str


def _is_enabled() -> bool:
    return os.getenv("MCP_AI_ENABLE_LLM", "false").strip().lower() in {"1", "true", "yes", "on"}


def _extract_json_object(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
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


def _build_planner_prompt(question: str, tool_catalog: list[dict[str, Any]]) -> str:
    catalog_lines = []
    for tool in tool_catalog:
        catalog_lines.append(
            f"- {tool.get('name')}: {tool.get('description')} | params schema: {json.dumps(tool.get('input_schema', {}))}"
        )

    return (
        "You are a BI tool planner. Select exactly one tool from the allowlist and return strict JSON only.\n"
        "Do not include markdown, commentary, or extra keys.\n"
        "JSON schema:\n"
        '{"tool_name":"string","confidence":"high|medium|low","rationale":"string","params":{}}\n\n'
        "Rules:\n"
        "1) tool_name must be one of allowlisted names.\n"
        "2) params must only include fields valid for that tool schema.\n"
        "3) Infer date windows when user asks this/last week/month, else use empty params.\n"
        "4) Keep rationale short and factual.\n\n"
        f"Allowlisted tools:\n{chr(10).join(catalog_lines)}\n\n"
        f"User question: {question}\n"
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
            return parsed if isinstance(parsed, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def _call_claude(question: str, tool_catalog: list[dict[str, Any]], timeout_seconds: int) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()
    if not api_key:
        return None

    payload = {
        "model": model,
        "max_tokens": 450,
        "temperature": 0,
        "messages": [
            {"role": "user", "content": _build_planner_prompt(question, tool_catalog)}
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    parsed = _post_json("https://api.anthropic.com/v1/messages", payload, headers, timeout_seconds)
    if not parsed:
        return None

    content = parsed.get("content") or []
    if not content or not isinstance(content, list):
        return None
    text_chunks = [chunk.get("text", "") for chunk in content if isinstance(chunk, dict)]
    output = _extract_json_object("\n".join(text_chunks))
    if output is None:
        return None
    return output, model


def _call_gemini(question: str, tool_catalog: list[dict[str, Any]], timeout_seconds: int) -> Optional[tuple[dict[str, Any], str]]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro").strip()
    if not api_key:
        return None

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _build_planner_prompt(question, tool_catalog)}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 400,
        },
    }
    headers = {"content-type": "application/json"}
    parsed = _post_json(endpoint, payload, headers, timeout_seconds)
    if not parsed:
        return None

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
    return output, model


def _normalize_selection(raw: dict[str, Any], provider: str) -> Optional[NLToolSelection]:
    tool_name = str(raw.get("tool_name") or "").strip().lower()
    if not tool_name or get_report_tool_definition(tool_name) is None:
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
    if not _is_enabled():
        return None

    timeout_seconds = int(os.getenv("MCP_AI_TIMEOUT_SECONDS", "20") or 20)
    primary = os.getenv("MCP_AI_PRIMARY_PROVIDER", "claude").strip().lower()
    secondary = os.getenv("MCP_AI_SECONDARY_PROVIDER", "gemini").strip().lower()
    provider_order = [p for p in [primary, secondary] if p in {"claude", "gemini"}]
    if not provider_order:
        provider_order = ["claude", "gemini"]

    for provider in provider_order:
        try:
            if provider == "claude":
                candidate = await asyncio.to_thread(_call_claude, question, tool_catalog, timeout_seconds)
            else:
                candidate = await asyncio.to_thread(_call_gemini, question, tool_catalog, timeout_seconds)
        except Exception:
            candidate = None

        if not candidate:
            continue

        raw_selection, model = candidate
        normalized = _normalize_selection(raw_selection, provider)
        if normalized is None:
            continue

        return AIPlannerResult(selection=normalized, provider=provider, model=model)

    return None
