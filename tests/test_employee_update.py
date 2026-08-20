from types import SimpleNamespace

import pytest

from src.app.routers import employee as employee_router


@pytest.mark.asyncio
async def test_update_employee_accepts_department_form_field(monkeypatch):
    captured = {}

    async def fake_call_service(service_func, **kwargs):
        captured["data"] = kwargs["data"]
        return SimpleNamespace(home_address=None)

    async def fake_enrich_employee_with_profile_image(db, employee):
        return {"id": 1, "department": captured["data"].department_id}

    monkeypatch.setattr(employee_router, "call_service", fake_call_service)
    monkeypatch.setattr(employee_router, "enrich_employee_with_profile_image", fake_enrich_employee_with_profile_image)

    response = await employee_router.update_employee(
        employee_id=1,
        first_name=None,
        last_name=None,
        email=None,
        phone_number=None,
        department_id=None,
        department="2",
        gender=None,
        home_address=None,
        role_id=None,
        hcp_employee_id=None,
        profile_image=None,
        current_user=SimpleNamespace(id=7),
        db=object(),
    )

    assert captured["data"].department_id == 2
    assert response["success"] is True
    assert response["data"]["department"] == 2