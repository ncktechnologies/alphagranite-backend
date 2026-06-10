## Plan: MCP Per-Tool Authorization Hardening

Strengthen MCP so each tool executes only when the user has permission for that tool’s owning resource (reports, fabs, shop_cut_plan, operators), while preserving current ask UX, planner behavior, and audit logging.

**Steps**
1. Add resource-authorization metadata checks in MCP runtime. Keep existing endpoint-level reports permission as a coarse gate, but add strict per-tool checks before invocation in both `/mcp/tools/{tool_name}/invoke` and `/mcp/ask`. This is the primary blocking step.
2. Implement a reusable permission helper path in MCP router flow. Resolve the selected tool definition, map its `resource` to `PermissionChecker(resource, "read")` semantics, and reject unauthorized tool execution with explicit 403 detail. Depends on step 1.
3. Enforce checks for both deterministic and LLM-selected tools. Apply checks after tool selection and before execution so LLM routing cannot bypass RBAC. Depends on step 2.
4. Extend audit trail payloads. Log authorization pass/fail context (`tool`, `resource`, `selection_source`, `resolved_params` subset-safe) without leaking sensitive payloads. Depends on step 2.
5. Add focused regression tests. Cover allowed/denied combinations per tool family for both invoke and ask endpoints, including deterministic and LLM-fallback routes. Depends on steps 2 and 3.
6. Validate backward compatibility. Confirm existing reports tools behavior remains unchanged for authorized users and unauthorized users receive clear permission failures. Depends on steps 3 and 5.

**Relevant files**
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/routers/mcp.py` — Add per-tool authorization checks in ask and invoke execution paths.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/mcp/report_tools.py` — Source of tool-to-resource metadata (`resource` field) used to enforce RBAC.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/utils/permissions.py` — Existing permission contract to reuse (no duplicate RBAC logic).
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/service/background.py` — Audit logging helper for authorization outcomes.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/tests` — Add or update MCP authorization tests.

**Verification**
1. Authorized user can execute tools for all granted resources through both `/invoke` and `/ask`.
2. User missing `reports` can’t execute reports-family tools; user missing `operators` can’t execute `ops.operator_my_tasks`; same pattern for `fabs` and `shop_cut_plan`.
3. LLM-selected tool that user lacks permission for returns deterministic 403 and does not execute.
4. Audit logs record authorization denial and approval events with tool/resource/source.
5. Existing report tool responses remain stable for authorized users.

**Decisions**
- Keep existing reports gate as coarse pre-check for now, but add strict per-tool authorization as authoritative execution gate.
- Use tool definition `resource` field as the single RBAC mapping source.
- Fail closed: if resource mapping is missing/invalid, deny execution.

**Further Considerations**
1. Optional follow-up: split `/mcp/ask` coarse permission from `reports` to a new `mcp` action-menu resource once role seeds are ready.
2. Optional follow-up: add tool visibility filtering in `/mcp/tools` so users only see tools they can execute.
3. Optional follow-up: include `required_permission` in tool metadata response for frontend UX hints.
