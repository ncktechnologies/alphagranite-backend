import ast
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest


def scheduler_namespace():
    source = Path(__file__).resolve().parents[1] / "src/app/service/monthly_end_of_month_status_report.py"
    tree = ast.parse(source.read_text())
    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {
            "start_monthly_status_report_scheduler",
            "_run_monthly_status_report_scheduler",
        }
    ]
    namespace = {
        "os": os,
        "asyncio": Mock(),
        "logger": Mock(),
        "_scheduler_task": None,
        "_scheduler_loop": Mock(),
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("enabled", ["false", "FALSE", "0", ""])
def test_disabled_scheduler_does_not_create_task(monkeypatch, enabled):
    monkeypatch.setenv("EOM_STATUS_REPORT_ENABLED", enabled)
    namespace = scheduler_namespace()

    namespace["start_monthly_status_report_scheduler"]()

    namespace["asyncio"].create_task.assert_not_called()


def test_enabled_scheduler_creates_only_one_task(monkeypatch):
    monkeypatch.setenv("EOM_STATUS_REPORT_ENABLED", "true")
    namespace = scheduler_namespace()
    namespace["asyncio"].create_task.return_value.done.return_value = False

    namespace["start_monthly_status_report_scheduler"]()
    namespace["start_monthly_status_report_scheduler"]()

    namespace["asyncio"].create_task.assert_called_once()


def test_scheduler_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("EOM_STATUS_REPORT_ENABLED", raising=False)
    namespace = scheduler_namespace()

    namespace["start_monthly_status_report_scheduler"]()

    namespace["asyncio"].create_task.assert_not_called()


def test_standalone_runner_waits_for_scheduler(monkeypatch):
    monkeypatch.setenv("EOM_STATUS_REPORT_ENABLED", "true")
    namespace = scheduler_namespace()
    namespace["asyncio"] = asyncio
    namespace["_scheduler_loop"] = AsyncMock()

    asyncio.run(namespace["_run_monthly_status_report_scheduler"]())

    namespace["_scheduler_loop"].assert_awaited_once()
    assert namespace["_scheduler_task"].done()


def test_standalone_runner_exits_when_disabled(monkeypatch):
    monkeypatch.setenv("EOM_STATUS_REPORT_ENABLED", "false")
    namespace = scheduler_namespace()
    namespace["asyncio"] = asyncio
    namespace["_scheduler_loop"] = AsyncMock()

    asyncio.run(namespace["_run_monthly_status_report_scheduler"]())

    namespace["_scheduler_loop"].assert_not_called()


@pytest.mark.parametrize(
    "entrypoint",
    [
        "src.app.service.monthly_end_of_month_status_report",
        "src.app.tasks.hcp_payroll_tasks",
    ],
)
def test_standalone_entrypoint_resolves_models(entrypoint):
    # Fresh interpreter, matching the monthly_reports/celery_worker containers,
    # so models imported by other tests can't mask a missing relationship or
    # foreign-key target. jobs.company_id has no model in the API either.
    code = (
        f"import {entrypoint}\n"
        "from sqlalchemy.orm import configure_mappers\n"
        "from sqlmodel import SQLModel\n"
        "configure_mappers()\n"
        "for table in SQLModel.metadata.tables.values():\n"
        "    for fk in table.foreign_keys:\n"
        "        if fk.target_fullname != 'companies.id':\n"
        "            fk.column\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
