import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.database import get_db
from src.app.middleware.jwt_auth import get_current_user
from src.app.routers import cnc


def test_every_selected_file_is_uploaded_and_attached():
    app = FastAPI()
    app.include_router(cnc.router)
    record = SimpleNamespace(id=5, fab_id=9, file_ids="1", updated_at=None, updated_by=None)
    result = MagicMock()
    result.scalar_one_or_none.return_value = record
    app.dependency_overrides[get_db] = lambda: SimpleNamespace(execute=AsyncMock(return_value=result), commit=AsyncMock())
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=3)
    new_ids = iter(range(100, 200))

    with patch.object(cnc.FileService, "upload_file", AsyncMock(side_effect=lambda **kw: {"id": next(new_ids)})) as upload:
        response = TestClient(app).post(
            "/CNC/5/add-file",
            data={"stage_name": "cnc", "file_design": "CNC EST"},
            # The web app sends all selected files under the same "file" field.
            files=[("file", (f"f{i}.jpg", io.BytesIO(b"x"), "image/jpeg")) for i in range(4)],
        )

    assert response.status_code == 200
    assert upload.await_count == 4
    assert response.json()["data"]["file_ids"] == [100, 101, 102, 103]
    assert record.file_ids == "1,100,101,102,103"
