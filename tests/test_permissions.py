from types import SimpleNamespace

import pytest

from src.app.routers import department, employee
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


def create_only_db(resource):
	permission = SimpleNamespace(
		can_create=True,
		can_read=False,
		can_update=False,
		can_delete=False,
	)
	return QueuedSession(
		[
			QueryResult(rows=[]),
			QueryResult(scalar=SimpleNamespace(id=5, code=resource)),
			QueryResult(rows=[(SimpleNamespace(role_id=10), permission)]),
		]
	)


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["employees", "departments"])
async def test_create_permission_accepts_legacy_direct_role(resource):
	current_user = SimpleNamespace(id=7, role_id=10, is_super_admin=False)

	authorized_user = await PermissionChecker(resource, "create")(
		db=create_only_db(resource),
		current_user=current_user,
	)

	assert authorized_user is current_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
	("router", "endpoint", "resource"),
	[
		(employee.employee_router, employee.update_employee, "employees"),
		(department.router, department.update_department, "departments"),
	],
)
async def test_update_routes_accept_create_permission(router, endpoint, resource):
	route = next(route for route in router.routes if route.endpoint is endpoint)
	permission_dependency = next(
		dependency.call
		for dependency in route.dependant.dependencies
		if dependency.name == "current_user"
	)
	current_user = SimpleNamespace(id=7, role_id=10, is_super_admin=False)

	authorized_user = await permission_dependency(
		db=create_only_db(resource),
		current_user=current_user,
	)

	assert authorized_user is current_user
