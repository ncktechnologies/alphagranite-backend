from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.user import User
from src.app.interface.response_wrappers import SuccessResponse
from src.app.service.background import save_audit_trail
from src.app.mcp.report_tools import (
    get_report_tool_definition,
    invoke_report_tool,
    list_report_tools,
    sanitize_params_for_tool,
    select_tool_for_question,
    suggest_tools_for_question,
    summarize_tool_result,
)
from src.app.service.ai_provider import maybe_generate_advisor_response, maybe_plan_tool_with_llm
from src.app.utils.helpers import error_response, success_response
from src.app.utils.permissions import PermissionChecker


router = APIRouter(prefix="/mcp", tags=["MCP"])
logger = logging.getLogger(__name__)


class MCPToolInvokeRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


class MCPQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    response_mode: str = Field(default="standard")
    focus: str = Field(default="mixed")


@router.get("/tools", response_model=SuccessResponse[list[dict]])
async def get_mcp_tools(
    current_user: User = Depends(PermissionChecker("reports", "read")),
):
    _ = current_user
    return success_response(list_report_tools(), "MCP tools retrieved successfully")


@router.get("/tools/{tool_name}", response_model=SuccessResponse[dict])
async def get_mcp_tool_details(
    tool_name: str,
    current_user: User = Depends(PermissionChecker("reports", "read")),
):
    _ = current_user
    tool_definition = get_report_tool_definition(tool_name)
    if tool_definition is None:
        raise error_response("MCP tool not found", 404)

    return success_response(
        {
            "name": tool_definition.name,
            "description": tool_definition.description,
            "resource": tool_definition.resource,
            "action": tool_definition.action,
            "input_schema": tool_definition.input_schema,
            "sample_params": tool_definition.sample_params,
            "result_summary": tool_definition.result_summary,
        },
        "MCP tool retrieved successfully",
    )


@router.post("/tools/{tool_name}/invoke", response_model=SuccessResponse[dict])
async def run_mcp_tool(
    tool_name: str,
    payload: MCPToolInvokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reports", "read")),
):
    tool_definition = get_report_tool_definition(tool_name)
    if tool_definition is None:
        raise error_response("MCP tool not found", 404)

    cleaned_params = sanitize_params_for_tool(tool_definition.name, payload.params)

    try:
        result = await invoke_report_tool(
            tool_name,
            cleaned_params,
            db=db,
            current_user=current_user,
        )
    except ValueError as exc:
        raise error_response(str(exc), 400)

    await save_audit_trail(
        db,
        "mcp_tool_invoked",
        current_user.id,
        f"MCP tool invoked: {tool_definition.name} params={cleaned_params}",
        0,
    )

    return success_response(
        {
            "tool": tool_definition.name,
            "description": tool_definition.description,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "params": cleaned_params,
            "result": result,
        },
        "MCP tool executed successfully",
    )


@router.post("/ask", response_model=SuccessResponse[dict])
async def ask_mcp_bi_question(
    payload: MCPQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reports", "read")),
):
    logger.info(
        "mcp.ask request_received user_id=%s question_preview=%s explicit_params=%s",
        current_user.id,
        payload.question[:160],
        payload.params,
    )

    full_tool_catalog = list_report_tools()
    candidate_rankings = suggest_tools_for_question(payload.question, limit=12)
    candidate_names = [item.get("tool_name") for item in candidate_rankings if item.get("tool_name")]
    candidate_set = set(candidate_names)

    tool_catalog = [tool for tool in full_tool_catalog if tool.get("name") in candidate_set] if candidate_set else []
    if not tool_catalog:
        tool_catalog = full_tool_catalog

    logger.info(
        "mcp.ask planner_candidates count=%s names=%s",
        len(tool_catalog),
        [item.get("name") for item in tool_catalog],
    )

    llm_plan = await maybe_plan_tool_with_llm(payload.question, tool_catalog)

    if llm_plan is not None:
        selection = llm_plan.selection
        source = "llm"
        provider = llm_plan.provider
        model = llm_plan.model
    else:
        try:
            selection = select_tool_for_question(payload.question)
        except ValueError as exc:
            raise error_response(str(exc), 400)
        source = "deterministic"
        provider = None
        model = None

    logger.info(
        "mcp.ask planner_decision source=%s provider=%s model=%s selected_tool=%s confidence=%s",
        source,
        provider,
        model,
        selection.tool_name,
        selection.confidence,
    )

    resolved_params = sanitize_params_for_tool(
        selection.tool_name,
        {
            **dict(selection.params),
            **(payload.params or {}),
        },
    )

    tool_definition = get_report_tool_definition(selection.tool_name)
    if tool_definition is None:
        raise error_response("No MCP tool matched the question", 404)

    try:
        result = await invoke_report_tool(
            selection.tool_name,
            resolved_params,
            db=db,
            current_user=current_user,
        )
    except ValueError as exc:
        raise error_response(str(exc), 400)

    logger.info(
        "mcp.ask tool_invoked source=%s tool=%s resolved_params=%s",
        source,
        selection.tool_name,
        resolved_params,
    )

    insights = summarize_tool_result(selection.tool_name, result)

    advisor_response = await maybe_generate_advisor_response(
        payload.question,
        selection.tool_name,
        resolved_params,
        insights,
        result,
        response_mode=payload.response_mode,
        focus=payload.focus,
    )

    await save_audit_trail(
        db,
        "mcp_bi_question",
        current_user.id,
        f"MCP BI question matched tool={selection.tool_name} source={source} provider={provider} model={model} "
        f"question={payload.question} params={resolved_params}",
        0,
    )

    if advisor_response is not None:
        logger.info(
            "mcp.ask advisor_ready provider=%s model=%s tool=%s",
            advisor_response.provider,
            advisor_response.model,
            selection.tool_name,
        )

    return success_response(
        {
            "question": payload.question,
            "matched_tool": selection.tool_name,
            "confidence": selection.confidence,
            "rationale": selection.rationale,
            "source": source,
            "provider": provider,
            "model": model,
            "planner_candidates": candidate_rankings,
            "resolved_params": resolved_params,
            "response_mode": payload.response_mode,
            "focus": payload.focus,
            "insights": insights,
            "advisor": advisor_response.advisor if advisor_response is not None else None,
            "advisor_provider": advisor_response.provider if advisor_response is not None else None,
            "advisor_model": advisor_response.model if advisor_response is not None else None,
            "result": result,
        },
        "MCP BI question answered successfully",
    )
