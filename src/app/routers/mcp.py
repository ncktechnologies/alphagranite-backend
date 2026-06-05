from __future__ import annotations

from datetime import datetime, timezone
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
    select_tool_for_question,
    summarize_tool_result,
)
from src.app.utils.helpers import error_response, success_response
from src.app.utils.permissions import PermissionChecker


router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPToolInvokeRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


class MCPQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


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

    try:
        result = await invoke_report_tool(
            tool_name,
            payload.params,
            db=db,
            current_user=current_user,
        )
    except ValueError as exc:
        raise error_response(str(exc), 400)

    await save_audit_trail(
        db,
        "mcp_tool_invoked",
        current_user.id,
        f"MCP tool invoked: {tool_definition.name} params={payload.params}",
        0,
    )

    return success_response(
        {
            "tool": tool_definition.name,
            "description": tool_definition.description,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "params": payload.params,
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
    try:
        selection = select_tool_for_question(payload.question)
    except ValueError as exc:
        raise error_response(str(exc), 400)

    resolved_params = dict(selection.params)
    resolved_params.update(payload.params or {})

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

    insights = summarize_tool_result(selection.tool_name, result)

    await save_audit_trail(
        db,
        "mcp_bi_question",
        current_user.id,
        f"MCP BI question matched tool={selection.tool_name} question={payload.question} params={resolved_params}",
        0,
    )

    return success_response(
        {
            "question": payload.question,
            "matched_tool": selection.tool_name,
            "confidence": selection.confidence,
            "rationale": selection.rationale,
            "resolved_params": resolved_params,
            "insights": insights,
            "result": result,
        },
        "MCP BI question answered successfully",
    )
