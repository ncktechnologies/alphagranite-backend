import os
from datetime import datetime

import pytest

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")
pytest.importorskip("jwt")

from src.app.routers.shop_cut_plan import _compute_business_rollover_end


def test_compute_business_rollover_end_spills_to_next_day():
    start = datetime(2026, 4, 1, 14, 0)

    result = _compute_business_rollover_end(start, 6)

    assert result == datetime(2026, 4, 2, 11, 0)


def test_compute_business_rollover_end_skips_lunch_and_next_day():
    start = datetime(2026, 4, 1, 11, 0)

    result = _compute_business_rollover_end(start, 8)

    assert result == datetime(2026, 4, 2, 11, 0)