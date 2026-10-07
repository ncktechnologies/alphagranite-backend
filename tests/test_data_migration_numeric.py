import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "data_migration"))

from migrate import parse_duration_sec, parse_float, parse_int


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("4.699999999999", 4.7),
        ("117.100000000001", 117.1),
        ("$1,540.125", 1540.13),
        ("-0.005", -0.01),
        ("NaN", None),
        ("Infinity", None),
        ("N/A", None),
    ],
)
def test_parse_float_rounds_source_figures_to_two_decimal_places(source, expected):
    assert parse_float(source) == expected


def test_parse_int_keeps_truncation_without_float_rounding():
    assert parse_int("1.999") == 1


def test_duration_conversion_keeps_source_precision_before_seconds_conversion():
    assert parse_duration_sec("1.001 hours") == 3603