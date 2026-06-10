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
    enrich_params_from_question,
    get_report_tool_definition,
    invoke_report_tool,
    list_report_tools,
    sanitize_params_for_tool,
    select_tool_for_question,
    suggest_tools_for_question,
    summarize_tool_result,
)
from src.app.mcp.multi_tool import CONTEXT_PACK_TOOL, is_broad_question, run_context_pack
from src.app.mcp.qa_history import record_feedback, retrieve_related_qa, store_qa_history
from src.app.mcp.sql_query import (
    SQLGuardError,
    build_schema_context,
    execute_select_sql,
    sql_enabled,
)
from src.app.service.ai_provider import (
    CONVERSATIONAL_TOOL,
    maybe_generate_advisor_response,
    maybe_generate_conversational_response,
    maybe_generate_sql,
    maybe_plan_tool_with_llm,
)
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
    allow_context_pack: bool = Field(default=True)
    prefer_sql: bool = Field(default=False)


class MCPFeedbackRequest(BaseModel):
    history_id: int = Field(..., ge=1)
    feedback: int = Field(..., ge=-1, le=1)


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


async def _attempt_sql_answer(
    *,
    payload: "MCPQuestionRequest",
    current_user: User,
    db: AsyncSession,
    related_qa: list[dict[str, Any]],
    candidate_rankings: list[dict[str, Any]],
):
    """Option B: guarded read-only SQL fallback.

    Returns a success_response on success, or None to let the caller fall back
    to a conversational reply. Never raises and never mutates data.
    """
    try:
        schema_context = await build_schema_context()
    except Exception:
        logger.exception("mcp.ask sql_schema_failed")
        return None
    if not schema_context:
        return None

    generated = await maybe_generate_sql(payload.question, schema_context)
    if not generated or not generated.get("sql"):
        return None

    try:
        sql_result = await execute_select_sql(generated["sql"])
    except SQLGuardError as exc:
        logger.warning("mcp.ask sql_rejected reason=%s", exc)
        return None
    except Exception:
        logger.exception("mcp.ask sql_execution_failed")
        return None

    row_count = sql_result.get("row_count", 0)
    columns = sql_result.get("columns", [])
    insights = [
        f"Ran a read-only SQL query returning {row_count} row(s).",
        f"Columns: {', '.join(columns) if columns else 'none'}.",
    ]
    if sql_result.get("truncated"):
        insights.append("Results were truncated to the row cap; refine the question for a narrower set.")

    advisor_response = await maybe_generate_advisor_response(
        payload.question,
        "sql.query",
        {"sql": sql_result.get("sql")},
        insights,
        sql_result,
        response_mode=payload.response_mode,
        focus=payload.focus,
        prior_qa=related_qa,
    )

    await store_qa_history(
        user_id=current_user.id,
        question=payload.question,
        mode="sql",
        matched_tool="sql.query",
        answer_summary=advisor_response.advisor.get("executive_summary") if advisor_response is not None else None,
        answer_json=advisor_response.advisor if advisor_response is not None else None,
        provider=advisor_response.provider if advisor_response is not None else None,
        model=advisor_response.model if advisor_response is not None else None,
    )

    await save_audit_trail(
        db,
        "mcp_bi_question",
        current_user.id,
        f"MCP BI question answered via SQL rows={row_count} question={payload.question}",
        0,
    )

    logger.info("mcp.ask sql_path_ready rows=%s", row_count)

    return success_response(
        {
            "question": payload.question,
            "matched_tool": "sql.query",
            "mode": "sql",
            "confidence": generated.get("confidence", "medium"),
            "rationale": generated.get("rationale", "Generated a read-only SQL query."),
            "source": "sql",
            "provider": generated.get("provider"),
            "model": generated.get("model"),
            "planner_candidates": candidate_rankings,
            "resolved_params": {"sql": sql_result.get("sql")},
            "response_mode": payload.response_mode,
            "focus": payload.focus,
            "related_qa": related_qa,
            "insights": insights,
            "advisor": advisor_response.advisor if advisor_response is not None else None,
            "advisor_provider": advisor_response.provider if advisor_response is not None else None,
            "advisor_model": advisor_response.model if advisor_response is not None else None,
            "result": sql_result,
        },
        "MCP BI question answered successfully",
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

    # Option C: surface relevant prior Q&A (recency + keyword overlap) for continuity.
    related_qa = await retrieve_related_qa(
        db=db,
        user_id=current_user.id,
        question=payload.question,
        limit=3,
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

    # Option A: broad / cross-domain questions get a multi-tool context pack.
    if payload.allow_context_pack and is_broad_question(payload.question):
        logger.info("mcp.ask context_pack_path question_preview=%s", payload.question[:120])
        pack = await run_context_pack(payload.question, db=db, current_user=current_user)
        pack_insights = pack.get("insights", [])

        advisor_response = await maybe_generate_advisor_response(
            payload.question,
            CONTEXT_PACK_TOOL,
            {},
            pack_insights,
            pack,
            response_mode=payload.response_mode,
            focus=payload.focus,
            prior_qa=related_qa,
        )

        await store_qa_history(
            user_id=current_user.id,
            question=payload.question,
            mode="context_pack",
            matched_tool=None,
            answer_summary=advisor_response.advisor.get("executive_summary") if advisor_response else None,
            answer_json=advisor_response.advisor if advisor_response else None,
            provider=advisor_response.provider if advisor_response else None,
            model=advisor_response.model if advisor_response else None,
        )

        await save_audit_trail(
            db,
            "mcp_bi_question",
            current_user.id,
            f"MCP BI question answered via context_pack tools={pack.get('tools_run')} "
            f"question={payload.question}",
            0,
        )

        return success_response(
            {
                "question": payload.question,
                "matched_tool": None,
                "mode": "context_pack",
                "confidence": "high",
                "rationale": "Broad question answered across multiple reports.",
                "source": "context_pack",
                "provider": advisor_response.provider if advisor_response else None,
                "model": advisor_response.model if advisor_response else None,
                "planner_candidates": candidate_rankings,
                "tools_run": pack.get("tools_run", []),
                "tool_errors": pack.get("errors", {}),
                "resolved_params": {},
                "response_mode": payload.response_mode,
                "focus": payload.focus,
                "related_qa": related_qa,
                "insights": pack_insights,
                "advisor": advisor_response.advisor if advisor_response else None,
                "advisor_provider": advisor_response.provider if advisor_response else None,
                "advisor_model": advisor_response.model if advisor_response else None,
                "result": pack.get("sections", {}),
            },
            "MCP BI question answered successfully",
        )

    llm_plan = await maybe_plan_tool_with_llm(payload.question, tool_catalog)

    if llm_plan is not None:
        selection = llm_plan.selection
        source = "llm"
        provider = llm_plan.provider
        model = llm_plan.model

        # Planner rescue: if the LLM returns no-tool, but deterministic scoring
        # strongly indicates a concrete MCP report, prefer the report path.
        if selection.tool_name == CONVERSATIONAL_TOOL:
            try:
                deterministic_selection = select_tool_for_question(payload.question)
            except ValueError:
                deterministic_selection = None

            top_points = 0
            if candidate_rankings:
                raw_points = candidate_rankings[0].get("points")
                try:
                    top_points = int(raw_points)
                except (TypeError, ValueError):
                    top_points = 0

            if (
                deterministic_selection is not None
                and deterministic_selection.tool_name != CONVERSATIONAL_TOOL
                and deterministic_selection.confidence == "high"
                and top_points >= 9
            ):
                logger.info(
                    "mcp.ask planner_rescue_applied llm_tool=%s rescue_tool=%s top_points=%s",
                    selection.tool_name,
                    deterministic_selection.tool_name,
                    top_points,
                )
                selection = deterministic_selection
                source = "deterministic_rescue"
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

    if selection.tool_name == CONVERSATIONAL_TOOL:
        # Option B: when enabled, try a guarded read-only SQL answer before
        # falling back to a purely conversational reply.
        if sql_enabled():
            sql_outcome = await _attempt_sql_answer(
                payload=payload,
                current_user=current_user,
                db=db,
                related_qa=related_qa,
                candidate_rankings=candidate_rankings,
            )
            if sql_outcome is not None:
                return sql_outcome

        logger.info("mcp.ask conversational_path source=%s provider=%s", source, provider)
        advisor_response = await maybe_generate_conversational_response(
            payload.question,
            response_mode=payload.response_mode,
            focus=payload.focus,
        )

        await store_qa_history(
            user_id=current_user.id,
            question=payload.question,
            mode="conversational",
            matched_tool=None,
            answer_summary=advisor_response.advisor.get("executive_summary"),
            answer_json=advisor_response.advisor,
            provider=advisor_response.provider,
            model=advisor_response.model,
        )

        await save_audit_trail(
            db,
            "mcp_bi_question",
            current_user.id,
            f"MCP BI question answered conversationally source={source} provider={provider} model={model} "
            f"question={payload.question}",
            0,
        )

        logger.info(
            "mcp.ask conversational_ready advisor_provider=%s advisor_model=%s",
            advisor_response.provider,
            advisor_response.model,
        )

        return success_response(
            {
                "question": payload.question,
                "matched_tool": None,
                "mode": "conversational",
                "confidence": selection.confidence,
                "rationale": selection.rationale,
                "source": source,
                "provider": provider,
                "model": model,
                "planner_candidates": candidate_rankings,
                "resolved_params": {},
                "response_mode": payload.response_mode,
                "focus": payload.focus,
                "related_qa": related_qa,
                "insights": [],
                "advisor": advisor_response.advisor,
                "advisor_provider": advisor_response.provider,
                "advisor_model": advisor_response.model,
                "result": None,
            },
            "MCP BI question answered successfully",
        )

    resolved_params = sanitize_params_for_tool(
        selection.tool_name,
        {
            **enrich_params_from_question(payload.question, selection.tool_name),
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
        prior_qa=related_qa,
    )

    await store_qa_history(
        user_id=current_user.id,
        question=payload.question,
        mode="report",
        matched_tool=selection.tool_name,
        answer_summary=advisor_response.advisor.get("executive_summary") if advisor_response is not None else None,
        answer_json=advisor_response.advisor if advisor_response is not None else None,
        provider=advisor_response.provider if advisor_response is not None else None,
        model=advisor_response.model if advisor_response is not None else None,
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
            "mode": "report",
            "confidence": selection.confidence,
            "rationale": selection.rationale,
            "source": source,
            "provider": provider,
            "model": model,
            "planner_candidates": candidate_rankings,
            "resolved_params": resolved_params,
            "response_mode": payload.response_mode,
            "focus": payload.focus,
            "related_qa": related_qa,
            "insights": insights,
            "advisor": advisor_response.advisor if advisor_response is not None else None,
            "advisor_provider": advisor_response.provider if advisor_response is not None else None,
            "advisor_model": advisor_response.model if advisor_response is not None else None,
            "result": result,
        },
        "MCP BI question answered successfully",
    )


@router.post("/feedback", response_model=SuccessResponse[dict])
async def submit_mcp_feedback(
    payload: MCPFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reports", "read")),
):
    """Record thumbs up/down on a prior MCP answer (Option C learning signal).

    Positive feedback boosts an answer's relevance for future retrieval.
    """
    updated = await record_feedback(
        db=db,
        history_id=payload.history_id,
        user_id=current_user.id,
        feedback=payload.feedback,
    )
    if not updated:
        raise error_response("Feedback target not found", 404)

    return success_response(
        {"history_id": payload.history_id, "feedback": payload.feedback},
        "Feedback recorded successfully",
    )
