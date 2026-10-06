import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

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
    derive_static_data,
    gross_profit_delta,
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
    derived = derive_static_data(total_expenses=7_800_000, total_wages=3_120_000, breakeven_gross_revenue=1_100_000)
    assert derived["difference_overhead"] == 4_680_000
    assert derived["overhead_monthly"] == 390_000
    assert derived["overhead_weekly"] == 90_000
    assert derived["breakeven_gross_profit"] == 650_000
    assert derived["breakeven_avg_revenue_per_day"] == round(1_100_000 / 253 * 12, 2)


def test_static_data_missing_inputs_give_none():
    derived = derive_static_data(None, 100.0, None)
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
    assert breakeven_gross_profit_for_period(7_800_000, "this_month") == 650_000
    assert breakeven_gross_profit_for_period(7_800_000, "this_week") == 150_000
    assert breakeven_gross_profit_for_period(7_800_000, "today") == pytest.approx(7_800_000 / 253)
    assert breakeven_gross_profit_for_period(None, "this_month") is None
    assert breakeven_gross_profit_for_period(7_800_000, "all") is None


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
        "annual_monthly_summary": [{"month": "September", "number_of_weeks": 5, "gross_revenue": 60000}],
    }
    pdf = build_labor_cost_pdf(data)
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500
