from typing import Optional

from fastapi import Request, Response

from src.app.service.background import save_audit_event
from src.app.utils.config import SessionLocal


MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _normalize_path(path: str) -> str:
    path = path.strip("/")
    if path.startswith("api/v1/"):
        return path[len("api/v1/"):]
    return path


def _resource_type_from_path(path: str) -> str:
    normalized = _normalize_path(path)
    if not normalized:
        return "root"
    return normalized.split("/")[0]


def _record_id_from_path(path: str) -> Optional[int]:
    normalized = _normalize_path(path)
    for token in normalized.split("/"):
        if token.isdigit():
            return int(token)
    return None


def _user_id_from_request(request: Request) -> int:
    payload = getattr(request.state, "user", None)
    if isinstance(payload, dict):
        return int(payload.get("user_id") or 0)
    return 0


async def log_platform_audit_event(request: Request, response: Response) -> None:
    if request.method not in MUTATING_METHODS:
        return

    # Exclude documentation/static endpoints from platform action audit.
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
        return

    user_id = _user_id_from_request(request)
    resource_type = _resource_type_from_path(request.url.path)
    record_id = _record_id_from_path(request.url.path)

    message = f"{request.method} {request.url.path} -> {response.status_code}"

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_id = request.headers.get("x-device-id")

    async with SessionLocal() as session:
        await save_audit_event(
            db=session,
            operation=request.method,
            resource_type=resource_type,
            user_id=user_id,
            message=message,
            record_id=record_id,
            request_path=request.url.path,
            request_method=request.method,
            response_status_code=response.status_code,
            device_id=device_id,
            ip_address=ip_address,
            browser=user_agent,
            activity_table_name=resource_type,
            new_values={"query": dict(request.query_params)} if request.query_params else None,
        )
