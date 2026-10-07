import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from datetime import date, datetime, timedelta

import pytest

from src.app.routers.reports import _installer_period_totals, _installer_week_metrics
from src.app.service.labor_cost_report_pdf import build_labor_cost_pdf, format_metric, row_style_commands
from src.app.service.labor_cost_report_rows import (
    BOLD,
    FABRICATION_ROW_STYLES,
    FABRICATION_ROWS,
    HIGHLIGHT,
    INSTALLER_ROW_STYLES,
    INSTALLER_ROWS,
    ROW_HIGHLIGHT_BG,
    fabrication_metric_rows,
    installer_metric_rows,
)
from src.app.service.performance_data import (
    breakeven_gross_profit_for_period,
    company_holidays,
    derive_static_data,
    gross_profit_delta,
    working_days_in_year,
)

WEEK = dict(
    number_of_days=5,
    install_sqft=900.0,
    completed_sqft=1000.0,
    gross_revenue=60000.0,
    gross_profit=20000.0,
    ag_head_count=10.0,
    wages_basic_installer=8000.0,
    overtime_installer=2000.0,
    regular_hours=400.0,
    overtime_hours=100.0,
    ag_labor_cost_override=None,
    overtime_pct_override=None,
    sub_labor_cost=5000.0,
    sub_head_count=4.0,
    overhead=3000.0,
)


def week(variant, **changes):
    return _installer_week_metrics(variant=variant, **{**WEEK, **changes})


# ── Combined aggregation ─────────────────────────────────────────────────────

def test_combined_sums_ag_and_sub_labor_and_head_count():
    ag, subs, combined = week("ag"), week("subs"), week("combined")
    assert ag["total_labor_cost"] == 10000.0
    assert subs["total_labor_cost"] == 5000.0
    assert combined["total_labor_cost"] == ag["total_labor_cost"] + subs["total_labor_cost"] == 15000.0
    assert combined["total_head_count"] == 14.0
    assert combined["wages_sub_contractor"] == 5000.0
    assert combined["sub_contractor_head_count"] == 4.0


def test_combined_ratios_are_recalculated_from_totals_not_averaged():
    ag, subs, combined = week("ag"), week("subs"), week("combined")
    # (10000 + 5000) labor / 1000 sqft + 3000 overhead / 1000 sqft
    assert combined["labor_cost_per_sq_ft"] == 15.0
    assert combined["cost_to_install_per_sqft"] == 18.0
    assert combined["cost_to_install_per_sqft"] != round((ag["cost_to_install_per_sqft"] + subs["cost_to_install_per_sqft"]) / 2, 2)
    assert combined["labor_cost_pct_per_dollar_sold"] == 25.0  # 15000 / 60000
    assert combined["hourly_labor_cost_all_installers"] == 30.0  # 15000 / 500 AG hours
    assert combined["gross_profit_per_sf_installed"] == 20.0
    assert combined["gross_profit_less_installer_total_cost_psf"] == 2.0
    assert combined["average_revenue_per_day"] == 12000.0  # 60000 / 5


def test_ag_excludes_subs_and_subs_has_no_payroll_hours_or_overhead():
    ag, subs = week("ag"), week("subs")
    assert ag["wages_sub_contractor"] == 0 and ag["sub_contractor_head_count"] == 0
    assert ag["cost_to_install_per_sqft"] == 13.0  # 10000/1000 + 3000/1000
    assert subs["total_hours"] == 0 and subs["overhead_per_week"] == 0
    assert subs["cost_to_install_per_sqft"] == 5.0  # 5000/1000, no company overhead
    assert subs["total_head_count"] == 4.0
    # Installed volume is the same installs in every variant.
    for row in (ag, subs, week("combined")):
        assert row["completed_sqft_per_week"] == 1000.0 and row["gross_revenue"] == 60000.0


def test_ag_labor_override_applies_to_ag_labor_only():
    combined = week("combined", ag_labor_cost_override=7000.0)
    assert combined["total_labor_cost"] == 12000.0  # 7000 AG override + 5000 subs


def test_combined_month_totals_recalculate_from_summed_weeks():
    rows = [
        {"week_ending": "2026-09-04", "has_data": True, **week("combined")},
        {"week_ending": "2026-09-11", "has_data": True, **week("combined", completed_sqft=500.0, sub_labor_cost=1000.0)},
    ]
    totals = _installer_period_totals(rows)
    assert totals["total_labor_cost"] == 15000.0 + 11000.0
    assert totals["completed_sqft_per_week"] == 1500.0
    # From sums: 26000 / 1500 = 17.33, not the average of the two weekly ratios (15.0 and 22.0).
    assert totals["labor_cost_per_sq_ft"] == round(26000 / 1500, 2)


# ── Gross Profit Delta and static data ───────────────────────────────────────

def test_static_data_derivations():
    derived = derive_static_data(total_expenses=7_800_000, total_wages=3_120_000, breakeven_gross_revenue=1_100_000, year=2026)
    assert derived["difference_overhead"] == 4_680_000
    assert derived["overhead_monthly"] == 390_000
    assert derived["overhead_weekly"] == 90_000
    assert derived["breakeven_gross_profit"] == 650_000
    assert derived["working_days_per_year"] == 257
    assert derived["breakeven_avg_revenue_per_day"] == round(1_100_000 * 12 / 257, 2)


def test_static_data_missing_inputs_give_none():
    derived = derive_static_data(None, 100.0, None, 2026)
    assert derived["difference_overhead"] is None
    assert derived["overhead_weekly"] is None
    assert derived["breakeven_gross_profit"] is None
    assert derived["breakeven_avg_revenue_per_day"] is None


def test_gross_profit_delta_is_signed_gross_profit_minus_breakeven():
    assert gross_profit_delta(5_000, 650_000) == -645_000
    assert gross_profit_delta(700_000, 650_000) == 50_000
    assert gross_profit_delta(650_000, 650_000) == 0
    assert gross_profit_delta(5_000, None) is None


def test_breakeven_scales_to_dashboard_period():
    assert breakeven_gross_profit_for_period(7_800_000, "this_month", 2026) == 650_000
    assert breakeven_gross_profit_for_period(7_800_000, "this_week", 2026) == 150_000
    assert breakeven_gross_profit_for_period(7_800_000, "today", 2026) == pytest.approx(7_800_000 / 257)
    assert breakeven_gross_profit_for_period(None, "this_month", 2026) is None
    assert breakeven_gross_profit_for_period(7_800_000, "all", 2026) is None


# ── Working days per year ────────────────────────────────────────────────────

def test_working_days_are_weekdays_less_company_holidays():
    # 2026: 261 weekdays less New Year's Day (Thu), Good Friday (Apr 3), Christmas Eve (Thu) and Day (Fri).
    assert company_holidays(2026) == {date(2026, 1, 1), date(2026, 4, 3), date(2026, 12, 24), date(2026, 12, 25)}
    assert working_days_in_year(2026) == 257
    # Good Friday follows Easter: 2024-03-29, 2025-04-18, 2027-03-26.
    assert date(2024, 3, 29) in company_holidays(2024)
    assert date(2025, 4, 18) in company_holidays(2025)
    assert date(2027, 3, 26) in company_holidays(2027)


def test_weekend_holidays_are_observed_on_a_working_day():
    # 2022: Jan 1 is a Saturday (taken Fri Dec 31, 2021); Christmas is a Sunday (taken Mon Dec 26), Eve Fri Dec 23.
    assert company_holidays(2022) == {date(2022, 4, 15), date(2022, 12, 23), date(2022, 12, 26)}
    assert date(2021, 12, 31) in company_holidays(2021)
    # 2021: Christmas Saturday -> taken Fri Dec 24, so Eve moves to Thu Dec 23.
    assert {date(2021, 12, 23), date(2021, 12, 24)} <= company_holidays(2021)
    # 2023: Jan 1 Sunday -> Mon Jan 2; Christmas Monday -> Eve taken Fri Dec 22.
    assert {date(2023, 1, 2), date(2023, 12, 22), date(2023, 12, 25)} <= company_holidays(2023)
    # Leap year 2024: 262 weekdays less 4.
    assert working_days_in_year(2024) == 258


# ── Week days and HCP pay-week split ─────────────────────────────────────────

def test_report_weeks_count_weekdays_only():
    from src.app.routers.reports import _week_windows_for_month

    september = _week_windows_for_month(2026, 9)
    assert [w["number_of_weekdays"] for w in september] == [4, 5, 5, 5, 3]  # Tue 1st - Fri 4th ... Mon 28 - Wed 30
    october = _week_windows_for_month(2026, 10)
    assert october[0]["week_end"] == date(2026, 10, 2) and october[0]["number_of_weekdays"] == 2


def test_weekend_month_end_joins_the_last_friday_week():
    from src.app.routers.reports import _week_windows_for_month

    # October 2026 ends on Saturday the 31st: no Saturday-only week, the 31st belongs to the week ending Fri 30th.
    october = _week_windows_for_month(2026, 10)
    assert [w["week_end"].day for w in october] == [2, 9, 16, 23, 30]
    assert october[-1]["overlap_end"] == date(2026, 10, 31) and october[-1]["number_of_weekdays"] == 5
    # May 2026 ends on Sunday the 31st: same, both weekend days join the week ending Fri 29th.
    may = _week_windows_for_month(2026, 5)
    assert may[-1]["week_end"] == date(2026, 5, 29) and may[-1]["overlap_end"] == date(2026, 5, 31)
    # Every working day in the month is still covered exactly once.
    assert sum(w["number_of_weekdays"] for w in october) == 22


def test_pay_week_cut_by_month_end_is_shared_by_weekdays():
    from src.app.routers.reports import _pay_week_report_shares

    shares = _pay_week_report_shares(date(2026, 9, 28), date(2026, 10, 4), 2026, 4)
    assert shares == {"2026-09-30": 3 / 5, "2026-10-02": 2 / 5}
    # A pay week inside one report week goes to it whole.
    assert _pay_week_report_shares(date(2026, 9, 14), date(2026, 9, 20), 2026, 4) == {"2026-09-18": 1.0}
    # Only the weekdays in the requested year are kept.
    assert _pay_week_report_shares(date(2026, 12, 28), date(2027, 1, 3), 2027, 4) == {"2027-01-01": 1 / 5}


def test_hcp_pay_weeks_are_allocated_proportionally():
    from src.app.routers.reports import _allocate_hcp_pay_weeks

    def pay_week(snapshot_id, start, shares, wages, hours, head_count):
        return {
            "snapshot_id": snapshot_id, "period_start": start, "period_end": start + timedelta(days=6),
            "pulled_at": datetime(2026, 10, 5), "shares": shares,
            "totals": {"wages_basic": wages, "overtime_wages": wages / 10, "total_labor_cost": wages * 1.1,
                       "regular_hours": hours, "overtime_hours": hours / 10, "total_hours": hours * 1.1,
                       "head_count": head_count},
        }

    by_week = _allocate_hcp_pay_weeks([
        pay_week(1, date(2026, 9, 21), {"2026-09-25": 1.0}, 5000.0, 400.0, 10),
        pay_week(2, date(2026, 9, 28), {"2026-09-30": 0.6, "2026-10-02": 0.4}, 10000.0, 500.0, 12),
    ])
    assert by_week["2026-09-25"]["wages_basic"] == 5000.0
    assert by_week["2026-09-30"]["wages_basic"] == 6000.0  # 3/5 x 10000
    assert by_week["2026-10-02"]["wages_basic"] == 4000.0  # 2/5 x 10000
    assert by_week["2026-09-30"]["overtime_wages"] == 600.0
    assert by_week["2026-10-02"]["regular_hours"] == 200.0
    assert by_week["2026-10-02"]["overtime_hours"] == 20.0
    # Head count is people, not prorated.
    assert by_week["2026-09-30"]["head_count"] == by_week["2026-10-02"]["head_count"] == 12
    assert by_week["2026-10-02"]["snapshot_id"] == 2 and by_week["2026-10-02"]["pay_week_share"] == 0.4


# ── Row formatting map ───────────────────────────────────────────────────────

def test_row_styles_match_the_spec():
    assert FABRICATION_ROW_STYLES["shop_total_cost_per_sqft"] == HIGHLIGHT
    for key in ("shop_labor_overhead_per_hour", "gross_profit_per_sf_completed", "gross_revenue_per_sqft_fabricated"):
        assert FABRICATION_ROW_STYLES[key] == BOLD
    assert INSTALLER_ROW_STYLES["cost_to_install_per_sqft"] == HIGHLIGHT
    for key in ("gross_profit_per_sf_installed", "gross_revenue_per_sq_ft"):
        assert INSTALLER_ROW_STYLES[key] == BOLD
    for key in ("gross_revenue", "gross_profit", "average_revenue_per_day", "total_labor_cost"):
        assert FABRICATION_ROW_STYLES[key] == BOLD and INSTALLER_ROW_STYLES[key] == BOLD


def test_every_styled_key_is_a_real_report_row():
    assert set(FABRICATION_ROW_STYLES) <= {key for key, _, _ in FABRICATION_ROWS}
    assert set(INSTALLER_ROW_STYLES) <= {key for key, _, _ in INSTALLER_ROWS}


def test_metric_rows_carry_style_and_variant_rows():
    rows = {row["key"]: row for row in fabrication_metric_rows()}
    assert rows["shop_total_cost_per_sqft"]["style"] == HIGHLIGHT
    assert rows["regular_hours"]["style"] is None

    ag = {row["key"] for row in installer_metric_rows("ag")}
    subs = {row["key"] for row in installer_metric_rows("subs")}
    combined = {row["key"] for row in installer_metric_rows("combined")}
    assert "wages_sub_contractor" not in ag and "wages_sub_contractor" in combined
    assert "total_hours" not in subs and "cost_to_install_per_sqft" in subs
    assert ag < combined and subs < combined
    for variant in ("ag", "subs", "combined"):
        styled = {row["key"]: row["style"] for row in installer_metric_rows(variant)}
        assert styled["cost_to_install_per_sqft"] == HIGHLIGHT


# ── PDF ──────────────────────────────────────────────────────────────────────

def test_pdf_row_styles_span_the_whole_row():
    from reportlab.lib import colors

    highlight = row_style_commands(HIGHLIGHT, 3, colors)
    assert ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor(ROW_HIGHLIGHT_BG)) in highlight
    assert ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold") in highlight
    assert row_style_commands(BOLD, 2, colors) == [("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold")]
    assert row_style_commands(None, 1, colors) == []


def test_pdf_value_formatting_matches_web():
    assert format_metric(-645000, "currency") == "-$645,000.00"
    assert format_metric(1234.5, "currency") == "$1,234.50"
    assert format_metric(12.345, "percent") == "12.35%"
    assert format_metric(None, "currency") == "-"


def test_pdf_builds_from_report_data():
    data = {
        "title": "Installer Labor Costs - Weekly - Combined",
        "period": {"start_date": "2026-09-01", "end_date": "2026-09-30"},
        "metric_rows": installer_metric_rows("combined"),
        "monthly_report": {
            "month": "September",
            "weekly_breakdown": [{"week_ending": "2026-09-04", "has_data": True, **week("combined")}],
            "totals": {"has_data": True, **week("combined")},
        },
        "annual_report": {
            "year": 2026,
            "monthly_breakdown": [{"month": "September", "month_number": 9, **week("combined")}],
            "totals": {"has_data": True, **week("combined")},
        },
    }
    pdf = build_labor_cost_pdf(data)
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500


# ── Annual summary (fabrication) ─────────────────────────────────────────────

def _fab_week(completed_sqft, labor, revenue, overhead=1000.0):
    return {
        "number_of_days": 5, "cut_sqft_saw": completed_sqft, "completed_sqft": completed_sqft,
        "gross_revenue": revenue, "gross_profit": revenue / 2, "wages_basic_shop_yard": labor,
        "overtime_shop_yard": 0.0, "total_labor_cost": labor, "regular_hours": 100.0, "overtime_hours": 0.0,
        "total_hours": 100.0, "total_head_count_inc_yard": 5.0, "total_employees": 10.0, "overhead_per_week": overhead,
    }


def test_fabrication_year_totals_recalculate_from_all_weeks():
    from src.app.routers.reports import _fabrication_period_totals

    january = [_fab_week(100.0, 1000.0, 10000.0), _fab_week(300.0, 2000.0, 30000.0)]
    february = [_fab_week(600.0, 3000.0, 60000.0)]
    jan, feb = _fabrication_period_totals(january), _fabrication_period_totals(february)
    year = _fabrication_period_totals(january + february)

    assert year["completed_sqft"] == jan["completed_sqft"] + feb["completed_sqft"] == 1000.0
    assert year["total_labor_cost"] == 6000.0 and year["overhead_per_week"] == 3000.0
    assert year["number_of_weeks"] == 3
    # 6000 / 1000, not the average of January (7.5) and February (5.0).
    assert year["labor_cost_per_sq_ft"] == 6.0
    assert jan["labor_cost_per_sq_ft"] == 7.5 and feb["labor_cost_per_sq_ft"] == 5.0


# ── Report widgets ───────────────────────────────────────────────────────────

STATIC = derive_static_data(total_expenses=7_800_000, total_wages=3_120_000, breakeven_gross_revenue=1_100_000, year=2026)


def _widgets(groups, totals, **kwargs):
    from src.app.service.labor_cost_report_widgets import build_labor_cost_widgets

    args = dict(groups=groups, totals=totals, static_data=STATIC, overhead_per_week=90_000.0, total_employees=40,
                wages_regular_key="wages_basic_shop_yard", wages_overtime_key="overtime_shop_yard")
    return {w["key"]: w for w in build_labor_cost_widgets(**{**args, **kwargs})}


def test_revenue_widgets_are_actual_minus_monthly_breakeven():
    widgets = _widgets(("revenue",), {"gross_revenue": 1_000_000.0, "gross_profit": 700_000.0, "average_revenue_per_day": 60_000.0})
    assert widgets["gross_revenue_delta"]["value"] == -100_000.0
    assert widgets["gross_revenue_delta"]["breakeven"] == 1_100_000
    assert widgets["gross_profit_delta"]["value"] == 50_000.0  # 700,000 - 7,800,000 / 12
    assert widgets["average_revenue_per_day_delta"]["value"] == round(60_000 - STATIC["breakeven_avg_revenue_per_day"], 2)
    assert {w["good_when"] for w in widgets.values()} == {"positive"}


def test_wage_widgets_use_the_monthly_wages_budget():
    # Budget 3,120,000 / 12 = 260,000; regular 200,000 leaves 60,000 for overtime.
    widgets = _widgets(("wages",), {"wages_basic_shop_yard": 200_000.0, "overtime_shop_yard": 80_000.0})
    assert widgets["wages_regular_delta"]["breakeven"] == 260_000.0
    assert widgets["wages_regular_delta"]["value"] == -60_000.0
    assert widgets["wages_overtime_delta"]["breakeven"] == 60_000.0
    assert widgets["wages_overtime_delta"]["value"] == 20_000.0
    # 80,000 / 200,000 = 40% vs 60,000 / 200,000 = 30%: 10 points over.
    assert widgets["overtime_regular_pct_delta"]["breakeven"] == 30.0
    assert widgets["overtime_regular_pct_delta"]["value"] == 10.0
    assert widgets["overtime_regular_pct_delta"]["format"] == "percent"
    assert {w["good_when"] for w in widgets.values()} == {"negative"}


def test_overhead_widgets_per_employee():
    widgets = _widgets(("overhead",), {})
    assert widgets["overhead_per_week"]["value"] == 90_000.0
    assert widgets["overhead_per_employee_week"]["value"] == 2_250.0
    assert widgets["overhead_per_employee_day"]["value"] == 450.0


def test_widgets_without_static_data_or_payroll_are_blank():
    from src.app.service.labor_cost_report_widgets import build_labor_cost_widgets

    widgets = build_labor_cost_widgets(
        groups=("revenue", "wages"), totals={"gross_revenue": 5.0, "wages_basic_shop_yard": 0.0, "overtime_shop_yard": 0.0},
        static_data=derive_static_data(None, None, None, 2026), overhead_per_week=None, total_employees=None,
        wages_regular_key="wages_basic_shop_yard", wages_overtime_key="overtime_shop_yard",
    )
    assert all(w["value"] is None for w in widgets)
    assert {w["note"] for w in widgets} == {"Break even not set - enter it on Static Data"}


def test_overtime_pct_without_regular_wages_says_why():
    widgets = _widgets(("wages",), {"wages_basic_shop_yard": 0.0, "overtime_shop_yard": 0.0})
    assert widgets["overtime_regular_pct_delta"]["value"] is None
    assert widgets["overtime_regular_pct_delta"]["note"] == "No regular wages this month"
    assert widgets["wages_regular_delta"]["note"] is None


def test_each_report_shows_its_widget_groups():
    from src.app.service.labor_cost_report_widgets import FABRICATION_WIDGET_GROUPS, INSTALLER_WIDGET_GROUPS

    assert FABRICATION_WIDGET_GROUPS == ("revenue", "wages", "overhead")
    assert INSTALLER_WIDGET_GROUPS == {"ag": ("revenue", "wages", "overhead"), "subs": (), "combined": ("revenue", "overhead")}
