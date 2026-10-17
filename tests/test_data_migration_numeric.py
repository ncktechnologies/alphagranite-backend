import sys
import sqlite3
from pathlib import Path
from unittest.mock import Mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "data_migration"))

from migrate import Ctx, parse_duration_sec, parse_float, parse_int


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


@pytest.mark.parametrize(
    ("max_id", "last_value", "is_called", "expected_next_id"),
    [(1, 1, False, 2), (8, 1, True, 9), (1, 20, True, 21),
     (1, 20, False, 20), (1, 1, True, 2), (None, 1, False, 1)],
)
def test_sequence_sync_handles_uncalled_sequence_without_moving_backwards(
    max_id, last_value, is_called, expected_next_id,
):
    with sqlite3.connect(":memory:") as database:
        database.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
        if max_id is not None:
            database.execute("INSERT INTO users VALUES (?)", (max_id,))
        database.execute("CREATE TABLE users_id_seq (last_value INTEGER)")
        database.execute("INSERT INTO users_id_seq VALUES (?)", (last_value,))
        sequence_updates = []

        def setval(sequence_name, value):
            assert sequence_name == "users_id_seq"
            sequence_updates.append(value)
            return value

        database.create_function("setval", 2, setval)
        cursor = Mock()
        cursor.fetchall.return_value = [("users", "id", "users_id_seq")]

        def execute(query, parameters=()):
            if query.startswith("SELECT table_name"):
                return
            database.execute(query.replace("%s", "?"), parameters).fetchall()

        cursor.execute.side_effect = execute
        connection = Mock()
        connection.cursor.return_value = cursor

        Ctx(connection).sync_id_sequences()

        next_id = sequence_updates[-1] + 1 if sequence_updates else last_value + int(is_called)
        assert next_id == expected_next_id