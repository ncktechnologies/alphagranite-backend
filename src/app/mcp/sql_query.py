"""Option B: guarded, read-only text-to-SQL.

SECURITY MODEL (defense in depth):
  1. Disabled by default. Enable explicitly with MCP_AI_ENABLE_SQL=true.
  2. Only a single SELECT/WITH statement is allowed. Any DML/DDL, multiple
     statements, comments, or dangerous functions are rejected before execution.
  3. A sensitive-table/column blocklist prevents access to credentials/PII.
  4. Execution happens inside a READ ONLY transaction with a statement_timeout
     and is always rolled back, so no write can ever persist.
  5. Results are row-capped.

Even with all of this, for production you should also point the app (or a
dedicated SQL role) at a least-privilege, read-only database user. App-level
guards are necessary but a read-only DB role is the strongest backstop.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

from sqlalchemy import text

from src.app.database import engine


logger = logging.getLogger(__name__)


class SQLGuardError(ValueError):
    """Raised when a generated SQL statement fails safety validation."""


_FORBIDDEN_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "grant", "revoke", "merge", "replace", "call", "do", "vacuum", "analyze",
    "attach", "detach", "copy", "into", "set", "reset", "lock", "comment",
    "reindex", "cluster", "refresh", "begin", "commit", "rollback", "savepoint",
    "prepare", "execute", "deallocate", "listen", "notify", "load", "import",
}

_FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir",
    "lo_import", "lo_export", "dblink", "pg_stat_file", "current_setting",
    "set_config", "pg_terminate_backend", "pg_cancel_backend", "txid_current",
    "query_to_xml", "version",
}

# Tables / identifiers that must never be exposed via free-form SQL.
_BLOCKED_IDENTIFIERS = {
    "users", "user", "audit_trails", "audit_trail", "alembic_version",
    "roles", "role", "permissions", "permission", "role_permissions",
    "role_permission", "user_roles", "user_role", "files", "file",
    "password", "passwords", "token", "tokens", "secret", "secrets",
    "api_key", "api_keys", "credential", "credentials",
}

_BLOCKED_COLUMN_SUBSTRINGS = ("password", "hashed", "secret", "token", "api_key", "ssn")


def sql_enabled() -> bool:
    return os.getenv("MCP_AI_ENABLE_SQL", "false").strip().lower() in {"1", "true", "yes", "on"}


def _sql_max_rows() -> int:
    raw = os.getenv("MCP_AI_SQL_MAX_ROWS", "200").strip()
    try:
        value = int(raw)
    except ValueError:
        return 200
    return max(1, min(value, 2000))


def _sql_timeout_ms() -> int:
    raw = os.getenv("MCP_AI_SQL_TIMEOUT_MS", "5000").strip()
    try:
        value = int(raw)
    except ValueError:
        return 5000
    return max(250, min(value, 30000))


def validate_select_sql(sql: str) -> str:
    """Validate and normalize a read-only SELECT/WITH statement.

    Returns the cleaned SQL (with an enforced LIMIT) or raises SQLGuardError.
    """
    if not sql or not sql.strip():
        raise SQLGuardError("Empty SQL.")

    cleaned = sql.strip()

    # Strip a single trailing semicolon; reject any internal semicolons
    # (defends against stacked statements).
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    if ";" in cleaned:
        raise SQLGuardError("Multiple statements are not allowed.")

    # Reject SQL comments outright (block comment-based bypasses).
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        raise SQLGuardError("SQL comments are not allowed.")

    lowered = cleaned.lower()

    # Must be a read-only query.
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise SQLGuardError("Only SELECT / WITH queries are allowed.")

    # Tokenize on word boundaries for keyword / identifier checks.
    tokens = set(re.findall(r"[a-z_][a-z0-9_]*", lowered))

    forbidden_hits = tokens & _FORBIDDEN_KEYWORDS
    if forbidden_hits:
        raise SQLGuardError(f"Disallowed keyword(s): {', '.join(sorted(forbidden_hits))}.")

    function_hits = tokens & _FORBIDDEN_FUNCTIONS
    if function_hits:
        raise SQLGuardError(f"Disallowed function(s): {', '.join(sorted(function_hits))}.")

    blocked_hits = tokens & _BLOCKED_IDENTIFIERS
    if blocked_hits:
        raise SQLGuardError(f"Access to restricted table(s) is not allowed: {', '.join(sorted(blocked_hits))}.")

    for token in tokens:
        if any(substr in token for substr in _BLOCKED_COLUMN_SUBSTRINGS):
            raise SQLGuardError("Access to restricted column(s) is not allowed.")

    # Block PostgreSQL system catalogs / information_schema exposure.
    if "pg_" in lowered or "information_schema" in lowered:
        raise SQLGuardError("Access to system catalogs is not allowed.")

    # Enforce a LIMIT. If the model didn't add one, append it.
    max_rows = _sql_max_rows()
    if not re.search(r"\blimit\s+\d+", lowered):
        cleaned = f"{cleaned}\nLIMIT {max_rows}"

    return cleaned


async def execute_select_sql(sql: str) -> dict[str, Any]:
    """Execute a validated SELECT in a rolled-back READ ONLY transaction.

    Returns {"columns": [...], "rows": [ {col: val} ], "row_count": n,
             "truncated": bool, "sql": cleaned_sql}.
    """
    if not sql_enabled():
        raise SQLGuardError("SQL querying is disabled (set MCP_AI_ENABLE_SQL=true to enable).")

    cleaned = validate_select_sql(sql)
    max_rows = _sql_max_rows()
    timeout_ms = _sql_timeout_ms()

    async with engine.connect() as conn:
        # Open an explicit transaction we will always roll back.
        trans = await conn.begin()
        try:
            await conn.execute(text("SET TRANSACTION READ ONLY"))
            await conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))

            result = await conn.execute(text(cleaned))
            columns = list(result.keys())
            fetched = result.fetchmany(max_rows + 1)
            truncated = len(fetched) > max_rows
            rows_data = fetched[:max_rows]

            rows: list[dict[str, Any]] = []
            for row in rows_data:
                mapping = dict(zip(columns, row))
                rows.append({key: _jsonable(value) for key, value in mapping.items()})

            logger.info("mcp.sql executed rows=%s truncated=%s", len(rows), truncated)
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
                "sql": cleaned,
            }
        finally:
            # Never commit. Roll back to guarantee zero side effects.
            await trans.rollback()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


_SCHEMA_CACHE: Optional[str] = None


async def build_schema_context(*, max_tables: int = 40, max_cols_per_table: int = 25) -> str:
    """Introspect public-schema tables/columns (excluding blocked ones).

    Returns a compact text description for grounding SQL generation. Cached for
    the process lifetime. Runs read-only against information_schema (internal
    app query, not user-supplied SQL).
    """
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    statement = text(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )

    tables: dict[str, list[str]] = {}
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            await conn.execute(text("SET TRANSACTION READ ONLY"))
            result = await conn.execute(statement)
            for table_name, column_name, data_type in result.fetchall():
                name_lower = (table_name or "").lower()
                if name_lower in _BLOCKED_IDENTIFIERS:
                    continue
                col_lower = (column_name or "").lower()
                if any(substr in col_lower for substr in _BLOCKED_COLUMN_SUBSTRINGS):
                    continue
                tables.setdefault(table_name, [])
                if len(tables[table_name]) < max_cols_per_table:
                    tables[table_name].append(f"{column_name}:{data_type}")
        finally:
            await trans.rollback()

    lines: list[str] = []
    for table_name in sorted(tables.keys())[:max_tables]:
        cols = ", ".join(tables[table_name])
        lines.append(f"{table_name}({cols})")

    _SCHEMA_CACHE = "\n".join(lines)
    logger.info("mcp.sql schema_context_built tables=%s", min(len(tables), max_tables))
    return _SCHEMA_CACHE
