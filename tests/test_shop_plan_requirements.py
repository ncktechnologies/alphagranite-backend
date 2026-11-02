from types import SimpleNamespace

from src.app.routers.fabs import _find_missing_shop_plan_data_points

FIELDS = ("wj_linft", "wj_miter_lnft", "saw_cut_lnft", "saw_miter_lnft", "edging_linft", "cnc_linft", "miter_linft")


def fab(**values):
    return SimpleNamespace(**{name: values.get(name) for name in FIELDS})


def missing(fab_values, planned=(), update=None):
    return [m["required_planning_section"] for m in _find_missing_shop_plan_data_points(fab(**fab_values), update or {}, set(planned))]


def test_nothing_measured_requires_nothing():
    assert missing({}) == []
    assert missing({"cnc_linft": None, "edging_linft": "", "miter_linft": 0}) == []


def test_wj_and_saw_are_required_by_straight_or_miter_footage():
    assert missing({"wj_linft": 12}) == ["CUT - WJ", "HANDWORK"]
    assert missing({"wj_miter_lnft": 3}) == ["CUT - WJ", "HANDWORK"]
    assert missing({"saw_cut_lnft": 8}) == ["CUT - SAW", "HANDWORK"]
    # Saw miter requires CUT - SAW (the spreadsheet's "CUT-WJ" there is a typo).
    assert missing({"saw_miter_lnft": 2}) == ["CUT - SAW", "HANDWORK"]


def test_miter_plan_only_when_miter_lin_ft_is_set():
    assert missing({"miter_linft": 0, "wj_miter_lnft": 5}, planned={"CUT - WJ", "HANDWORK"}) == []
    assert missing({"miter_linft": 4}, planned={"HANDWORK"}) == ["MITER"]


def test_lists_every_missing_activity_in_shop_order():
    fab_values = dict(wj_linft=10, saw_cut_lnft=6, edging_linft=20, cnc_linft=4, miter_linft=2)
    assert missing(fab_values) == ["CUT - WJ", "CUT - SAW", "EDGING", "CNC", "MITER", "HANDWORK"]
    assert missing(fab_values, planned={"CUT - WJ", "CUT - SAW", "CNC", "MITER"}) == ["EDGING", "HANDWORK"]


def test_optional_activities_and_legacy_names_count_as_planned():
    # Planning more than required is fine; legacy "cut"/"wj" sections still satisfy the cut stages.
    assert missing({"wj_linft": 1, "saw_cut_lnft": 1}, planned={"wj", "Cut", "Handwork", "Edging"}) == []


def test_values_being_saved_override_stored_ones():
    assert missing({"cnc_linft": 5}, planned={"HANDWORK"}, update={"cnc_linft": 0}) == []
    assert missing({}, planned={"HANDWORK"}, update={"edging_linft": "7.5"}) == ["EDGING"]
