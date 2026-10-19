import sys
import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "data_migration"))

from migrate import Ctx, parse_duration_sec, parse_float, parse_int
from split_fab_status import split_csv
from clear_unreviewed_shop_plans import cleanup, read_target_fab_ids
from backfill_predraft_completed_dates import read_review_dates
from data_migration.backfill_completed_cnc_draftings import backfill, read_csv_fab_ids


@pytest.mark.parametrize("apply", [False, True])
def test_completed_cnc_backfill_ignores_explicit_fabs(apply):
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,)], [(1,)], [], [(1,)]]
    cursor.fetchone.side_effect = [(7,), (3,)]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    assert backfill(connection, [1, 15376, 15484], apply=apply) == [1]

    fab_queries = [call.args for call in cursor.execute.call_args_list
                   if "WHERE id = ANY(%s)" in call.args[0] or "WHERE f.id = ANY(%s)" in call.args[0]]
    assert fab_queries
    for query, parameters in fab_queries:
        assert parameters[-1] == [1]


def test_completed_cnc_backfill_skips_database_when_only_ignored_fabs():
    connection = Mock()

    assert backfill(connection, [15376, 15484], apply=True) == []

    connection.cursor.assert_not_called()


def test_completed_cnc_backfill_reads_unique_csv_ids(tmp_path):
    source = tmp_path / "active.csv"
    source.write_text("fab_id,complete\n3,0\n1,-1\n3,0\n")

    assert read_csv_fab_ids(source) == [1, 3]


@pytest.mark.parametrize("contents", ["complete\n0\n", "fab_id\n0\n", "fab_id\ninvalid\n"])
def test_completed_cnc_backfill_rejects_invalid_csv(tmp_path, contents):
    source = tmp_path / "active.csv"
    source.write_text(contents)
    with pytest.raises(ValueError):
        read_csv_fab_ids(source)


@pytest.mark.parametrize("apply", [False, True])
def test_completed_cnc_backfill_skips_existing_and_other_sections(apply):
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,), (2,), (3,)], [(1,), (2,)], [(2,)], [(1,)]]
    cursor.fetchone.side_effect = [(7,), (3,)]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    assert backfill(connection, [1, 2, 3], apply=apply) == [1]

    statements = [call.args for call in cursor.execute.call_args_list]
    assert any("p.planning_section_id = 1" in query for query, *rest in statements)
    writes = [arguments for arguments in statements if arguments[0].startswith(("INSERT", "UPDATE", "DELETE"))]
    if apply:
        assert len(writes) == 1
        query, parameters = writes[0]
        assert query.startswith("INSERT INTO public.cnc_draftings")
        assert "NOT EXISTS" in query
        assert "true, 3, false, true" in query
        assert parameters[0] == 7
        assert parameters[-1] == [1]
    else:
        assert writes == []


def test_completed_cnc_backfill_rerun_does_not_insert():
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,)], [(1,)], [(1,)]]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    assert backfill(connection, [1], apply=True) == []
    assert not any(call.args[0].startswith(("INSERT", "UPDATE", "DELETE"))
                   for call in cursor.execute.call_args_list)


def test_unreviewed_shop_cleanup_reads_explicit_false_ids_only(tmp_path):
    source = tmp_path / "active.csv"
    source.write_text(
        "fab_id,pre_shop_review_completed\n1,0\n2,false\n3,-1\n4,true\n5,\n1,0\n"
    )

    assert read_target_fab_ids(source) == [1, 2]


@pytest.mark.parametrize("contents", [
    "fab_id,pre_shop_review_completed\n1,0\n1,-1\n",
    "fab_id,pre_shop_review_completed\ninvalid,0\n",
    "fab_id,complete\n1,0\n",
])
def test_unreviewed_shop_cleanup_refuses_ambiguous_csv(tmp_path, contents):
    source = tmp_path / "active.csv"
    source.write_text(contents)
    with pytest.raises(ValueError):
        read_target_fab_ids(source)


def test_predraft_backfill_reads_review_dates_for_requested_ids_only(tmp_path):
    source = tmp_path / "active.csv"
    source.write_text(
        "fab_id,pre_draft_review\n1,9/18/2026 1:03:33 PM\n2,\n3,10/15/2026 7:12:12 PM\n"
    )

    assert read_review_dates(source, [1, 3]) == {
        1: datetime(2026, 9, 18, 13, 3, 33),
        3: datetime(2026, 10, 15, 19, 12, 12),
    }


@pytest.mark.parametrize("contents, fab_ids", [
    ("fab_id,pre_draft_review\n1,9/18/2026 1:03:33 PM\n", [1, 2]),
    ("fab_id,pre_draft_review\n1,\n", [1]),
    ("fab_id,pre_draft_review\n1,not a date\n", [1]),
    ("fab_id,pre_draft_review\n1,9/18/2026\n1,9/19/2026\n", [1]),
    ("fab_id,draft_date_completed\n1,9/18/2026\n", [1]),
])
def test_predraft_backfill_refuses_missing_or_ambiguous_dates(tmp_path, contents, fab_ids):
    source = tmp_path / "active.csv"
    source.write_text(contents)
    with pytest.raises(ValueError):
        read_review_dates(source, fab_ids)


@pytest.mark.parametrize("apply", [False, True])
def test_unreviewed_shop_cleanup_limits_changes_to_csv_ids(apply):
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,), (2,)], [(10,)], []]
    cursor.fetchone.side_effect = [(0,), (0,), (2,)]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    cleanup(connection, [1, 2], apply=apply)

    writes = [call.args for call in cursor.execute.call_args_list
              if call.args[0].startswith(("UPDATE", "DELETE"))]
    if apply:
        assert len(writes) == 2
        assert writes[0] == ("DELETE FROM public.shop_cut_plans WHERE id = ANY(%s)", ([10],))
        assert "SET shop_est_completion_date = NULL" in writes[1][0]
        assert writes[1][1] == ([1, 2],)
    else:
        assert writes == []


@pytest.mark.parametrize("sessions, events, files, message", [
    ([(20,)], 1, 0, "Timer history exists"),
    ([], 0, 1, "Linked files exist"),
])
def test_unreviewed_shop_cleanup_blocks_dependencies_without_consent(sessions, events, files, message):
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,)], [(10,)], sessions]
    cursor.fetchone.side_effect = [(events,), (files,), (1,)]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    with pytest.raises(ValueError, match=message):
        cleanup(connection, [1], apply=True)

    assert not any(call.args[0].startswith(("DELETE", "UPDATE"))
                   for call in cursor.execute.call_args_list)


def test_unreviewed_shop_cleanup_removes_only_approved_dependencies():
    cursor = Mock()
    cursor.fetchall.side_effect = [[(1,)], [(10,)], [(20,)]]
    cursor.fetchone.side_effect = [(1,), (1,), (1,)]
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    cleanup(connection, [1], apply=True, delete_timer_history=True, detach_files=True)

    writes = [call.args for call in cursor.execute.call_args_list
              if call.args[0].startswith(("UPDATE", "DELETE"))]
    assert len(writes) == 5
    assert writes[0][0].startswith("DELETE FROM public.shop_cut_plan_timer_events")
    assert writes[0][1] == ([10], [20])
    assert writes[1][1] == ([20],)
    assert writes[2] == ("UPDATE public.files SET task_id = NULL WHERE task_id = ANY(%s)", ([10],))
    assert writes[3][1] == ([10],)
    assert writes[4][1] == ([1],)


def test_unreviewed_shop_cleanup_refuses_missing_fabs():
    cursor = Mock()
    cursor.fetchall.return_value = []
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)

    with pytest.raises(ValueError, match="missing from database"):
        cleanup(connection, [1], apply=True)

    assert not any(call.args[0].startswith(("DELETE", "UPDATE"))
                   for call in cursor.execute.call_args_list)


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