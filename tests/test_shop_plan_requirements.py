from types import SimpleNamespace

from src.app.routers.fabs import _find_missing_shop_plan_data_points


def fab(**values):
    fields = ("wj_linft", "edging_linft", "cnc_linft", "miter_linft", "saw_cut_lnft", "saw_miter_lnft", "wj_miter_lnft")
    return SimpleNamespace(**{name: values.get(name) for name in fields})


def test_miter_plan_not_required_when_wj_miter_is_zero():
    missing = _find_missing_shop_plan_data_points(fab(miter_linft=12, saw_miter_lnft=4, wj_miter_lnft=0), {}, set())
    assert missing == []


def test_miter_plan_required_when_wj_miter_has_footage():
    missing = _find_missing_shop_plan_data_points(fab(wj_miter_lnft=3.5), {}, {"CUT - SAW"})
    assert missing == [{"field": "wj_miter_lnft", "value": 3.5, "required_planning_section": "MITER"}]
    assert _find_missing_shop_plan_data_points(fab(wj_miter_lnft=3.5), {}, {"Miter"}) == []
