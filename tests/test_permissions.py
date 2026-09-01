from types import SimpleNamespace

import pytest

from src.app.utils.permissions import PermissionChecker


class QueryResult:
    def __init__(self, *, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def all(self):
        return self._rows

    def scalars(self):
        return self

    def first(self):
        return self._scalar


class QueuedSession:
    def __init__(self, results):
        self._results = iter(results)

    async def execute(self, statement):
        return next(self._results)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("resource", "action"),
    [
        ("employees", "update"),
        ("departments", "create"),
        ("departments", "update"),
    ],
)
async def test_permission_checker_accepts_permission_from_any_assigned_role(resource, action):
    denied_permission = SimpleNamespace(
        can_create=False,
        can_read=False,
        can_update=False,
        can_delete=False,
    )
    granted_permission = SimpleNamespace(
        can_create=action == "create",
        can_read=False,
        can_update=action == "update",
        can_delete=False,
    )
    db = QueuedSession(
        [
            QueryResult(rows=[(10,), (20,)]),
            QueryResult(scalar=SimpleNamespace(id=5, code=resource)),
            QueryResult(
                rows=[
                    (SimpleNamespace(role_id=10), denied_permission),
                    (SimpleNamespace(role_id=20), granted_permission),
                ]
            ),
        ]
    )
    current_user = SimpleNamespace(id=7, is_super_admin=False)

    authorized_user = await PermissionChecker(resource, action)(
        db=db,
        current_user=current_user,
    )

    assert authorized_user is current_user