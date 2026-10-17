import sys
import sqlite3
import csv
from pathlib import Path
from unittest.mock import Mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "data_migration"))

from migrate import Ctx, parse_duration_sec, parse_float, parse_int
from split_fab_status import split_csv


@pytest.mark.parametrize("apply", [False, True])
def test_split_fab_status_preserves_records_and_backs_up_original(tmp_path, apply):
    source = tmp_path / "input" / "Fab_Status.csv"
    output = tmp_path / "excluded" / "Fab_Status.csv"
    source.parent.mkdir()
    records = [
        ["fab_id", "fab_percent", "complete", "notes"],
        ["1", "50", "0", 'A, quoted "note"\nwith a newline'],
        ["2", "100.00", "true", "keep complete"],
        ["3", "0", "-1", "keep complete"],
        ["4", "", "FALSE", "move blank percentage"],
        ["5", "100", "0", "move hundred"],
    ]
    with source.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream).writerows(records)
    original = source.read_bytes()

    assert split_csv(source, output, apply=apply) == (2, 3)

    backup = source.with_suffix(".csv.bak")
    if not apply:
        assert source.read_bytes() == original
        assert not output.exists()
        assert not backup.exists()
    else:
        assert backup.read_bytes() == original
        with source.open(encoding="utf-8-sig", newline="") as stream:
            assert list(csv.reader(stream)) == [records[index] for index in (0, 2, 3)]
        with output.open(encoding="utf-8-sig", newline="") as stream:
            assert list(csv.reader(stream)) == [records[index] for index in (0, 1, 4, 5)]


@pytest.mark.parametrize("existing", ["backup", "output"])
def test_split_fab_status_refuses_to_overwrite_files(tmp_path, existing):
    source = tmp_path / "input" / "Fab_Status.csv"
    output = tmp_path / "excluded" / "Fab_Status.csv"
    source.parent.mkdir()
    source.write_text("fab_percent,complete\n50,0\n")
    original = source.read_bytes()
    target = source.with_suffix(".csv.bak") if existing == "backup" else output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing data")

    with pytest.raises(FileExistsError):
        split_csv(source, output, apply=True)

    assert source.read_bytes() == original
    assert target.read_text() == "existing data"


@pytest.mark.parametrize("contents", [
    "fab_percent,complete\nunknown,0\n",
    "complete\n0\n",
])
def test_split_fab_status_does_not_require_or_parse_percentages(tmp_path, contents):
    source = tmp_path / "Fab_Status.csv"
    output = tmp_path / "excluded" / "Fab_Status.csv"
    source.write_text(contents)

    assert split_csv(source, output) == (0, 1)

    assert not source.with_suffix(".csv.bak").exists()
    assert not output.exists()


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