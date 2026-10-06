"""Row layout for the weekly labor cost reports.

Each report response carries `metric_rows` built from these definitions, and
the PDF export renders from the same list, so the web table and the PDF always
show the same rows, labels, number formats and row styles. Rows are identified
by the metric key used in the report data, never by the display label.

Styles:
  "highlight" - row background ROW_HIGHLIGHT_BG with bold ROW_HIGHLIGHT_TEXT
  "bold"      - bold text, no background change
"""
from typing import Optional

# Same value as the web design token --color-info-strong (white text on it is 5.93:1, WCAG AA).
ROW_HIGHLIGHT_BG = "#0369A1"
ROW_HIGHLIGHT_TEXT = "#FFFFFF"

HIGHLIGHT, BOLD = "highlight", "bold"

# Rows bold in both the installer and the fabrication reports.
_SHARED_BOLD = {"gross_revenue", "gross_profit", "average_revenue_per_day", "total_labor_cost"}

FABRICATION_ROW_STYLES: dict[str, str] = {
    "shop_total_cost_per_sqft": HIGHLIGHT,
    "shop_labor_overhead_per_hour": BOLD,
    "gross_profit_per_sf_completed": BOLD,
    "gross_revenue_per_sqft_fabricated": BOLD,
    **{key: BOLD for key in _SHARED_BOLD},
}

INSTALLER_ROW_STYLES: dict[str, str] = {
    "cost_to_install_per_sqft": HIGHLIGHT,
    "gross_profit_per_sf_installed": BOLD,
    "gross_revenue_per_sq_ft": BOLD,
    **{key: BOLD for key in _SHARED_BOLD},
}

# (key, label, format) in display order. Formats: currency | percent | number | count | days.
FABRICATION_ROWS = [
    ("number_of_days", "Number of Days", "days"),
    ("cut_sqft_saw", "Cut Sq. Ft (saw)", "number"),
    ("completed_sqft", "Completed Sq. Ft", "number"),
    ("average_sqft_per_day", "Average Sq. Ft. per Day", "number"),
    ("gross_revenue", "Gross Revenue", "currency"),
    ("gross_profit", "Gross Profit", "currency"),
    ("average_revenue_per_day", "Average Revenue per Day", "currency"),
    ("total_head_count_inc_yard", "Total Head Count (Inc yard)", "count"),
    ("total_employees", "Total Employees", "count"),
    ("wages_basic_shop_yard", "Wages Basic Shop & Yard", "currency"),
    ("overtime_shop_yard", "Overtime Shop & Yard", "currency"),
    ("cost_of_overtime_pct", "Cost Of Overtime as a % of Basic Wages", "percent"),
    ("total_labor_cost", "Total Labor Cost", "currency"),
    ("regular_hours", "Regular Hours", "number"),
    ("overtime_hours", "Overtime Hours", "number"),
    ("overtime_hours_pct", "Overtime Hours as % of Total Hours", "percent"),
    ("total_hours", "Total Hours", "number"),
    ("shop_labor_per_hour", "Shop Labor Per hour", "currency"),
    ("shop_overhead_per_hour", "Shop Overhead per hour", "currency"),
    ("shop_labor_overhead_per_hour", "Shop labor & overhead per hour", "currency"),
    ("manpower_cost_per_hour", "Manpower cost per hour", "currency"),
    ("sqft_per_labor_hour", "Sq. Ft. Per Labor Hour", "number"),
    ("shop_productivity_sqft_per_hour", "Shop Productivity - Sq. Ft per Hour", "number"),
    ("labor_cost_per_sq_ft", "Labor Cost Per sq. Ft.", "currency"),
    ("labor_cost_pct_per_dollar_sold", "Labor Cost as % per Dollar Sold", "percent"),
    ("shop_overhead_cost_per_sqft", "Shop overhead cost per sq.ft fabricated", "currency"),
    ("shop_total_cost_per_sqft", "Shop total cost per sq.ft fabricated", "currency"),
    ("gross_profit_per_sf_completed", "Gross Profit per s.f. completed", "currency"),
    ("gross_profit_less_shop_total_cost_psf", "Gross Profit less Shop total cost psf", "currency"),
    ("gross_revenue_per_sqft_fabricated", "Gross Revenue per sq.ft fabricated", "currency"),
]

INSTALLER_ROWS = [
    ("number_of_days_per_week", "Number of Days Per Week", "days"),
    ("install_sqft_per_week", "Install Sq. Ft per week", "number"),
    ("completed_sqft_per_week", "Completed Sq. Ft per week", "number"),
    ("average_sqft_per_day", "Average Sq. Ft. per Day", "number"),
    ("gross_revenue", "Gross Revenue", "currency"),
    ("gross_profit", "Gross Profit", "currency"),
    ("average_revenue_per_day", "Average Revenue per Day", "currency"),
    ("sub_contractor_head_count", "Sub Contractor Head Count", "count"),
    ("wages_sub_contractor", "Total Labor Cost - Sub Contractor", "currency"),
    ("total_head_count", "Total Head Count", "count"),
    ("wages_basic_installer", "Wages Basic Installer", "currency"),
    ("overtime_installer", "Overtime Installer", "currency"),
    ("overtime_pct", "% Overtime", "percent"),
    ("total_labor_cost", "Total Labor Cost", "currency"),
    ("regular_hours", "Regular Hours", "number"),
    ("overtime_hours", "Overtime Hours", "number"),
    ("overtime_total_hours_pct", "% Overtime Of Total Hours", "percent"),
    ("total_hours", "Total Hours", "number"),
    ("hourly_labor_cost_all_installers", "Hourly Labor Cost for All Installers", "currency"),
    ("hourly_overhead_cost_all_installers", "Hourly Overhead Cost for All Installers", "currency"),
    ("hourly_cost_all_installers_inc_overhead", "Hourly Cost Of all Installers inc Overhead", "currency"),
    ("hourly_cost_per_installer_inc_overhead", "Hourly Cost Per Installer inc Overhead", "currency"),
    ("sqft_per_labor_hour", "Sq. Ft. Per Labor Hour", "number"),
    ("installer_productivity_sqft_per_hour", "Installer Productivity Sq.Ft per Hour", "number"),
    ("labor_cost_per_sq_ft", "Labor Cost Per sq Ft.", "currency"),
    ("labor_cost_pct_per_dollar_sold", "Labor Cost as % per Dollar Sold", "percent"),
    ("overhead_cost_per_sqft_installed", "Overhead cost per sq.ft installed", "currency"),
    ("overhead_per_week", "Overhead per Week", "currency"),
    ("cost_to_install_per_sqft", "Cost To Install Per Sq. ft.", "currency"),
    ("gross_profit_per_sf_installed", "Gross Profit per s.f. Installed", "currency"),
    ("gross_profit_less_installer_total_cost_psf", "Gross Profit less Installer total cost psf", "currency"),
    ("gross_revenue_per_sq_ft", "Gross Revenue Per Sq. ft", "currency"),
]

# Installer report variants: which rows each one shows.
INSTALLER_VARIANT_AG, INSTALLER_VARIANT_SUBS, INSTALLER_VARIANT_COMBINED = "ag", "subs", "combined"
INSTALLER_VARIANTS = (INSTALLER_VARIANT_AG, INSTALLER_VARIANT_SUBS, INSTALLER_VARIANT_COMBINED)

_SUB_ONLY_ROWS = {"sub_contractor_head_count", "wages_sub_contractor"}
# Subs have no HCP payroll, hours or company overhead, and their head count/labor
# are the "Total" rows, so the payroll breakdown rows are left out.
_SUBS_HIDDEN_ROWS = {
    "wages_sub_contractor",
    "total_head_count",
    "wages_basic_installer",
    "overtime_installer",
    "overtime_pct",
    "regular_hours",
    "overtime_hours",
    "overtime_total_hours_pct",
    "total_hours",
    "hourly_labor_cost_all_installers",
    "hourly_overhead_cost_all_installers",
    "hourly_cost_all_installers_inc_overhead",
    "hourly_cost_per_installer_inc_overhead",
    "sqft_per_labor_hour",
    "installer_productivity_sqft_per_hour",
    "overhead_cost_per_sqft_installed",
    "overhead_per_week",
}

INSTALLER_TITLES = {
    INSTALLER_VARIANT_AG: "Installer Labor Costs - Weekly - Alpha Granite",
    INSTALLER_VARIANT_SUBS: "Installer Labor Costs - Weekly - Subs",
    INSTALLER_VARIANT_COMBINED: "Installer Labor Costs - Weekly - Combined",
}
FABRICATION_TITLE = "Shop Labor Costs - Weekly"


def _metric_rows(rows: list[tuple[str, str, str]], styles: dict[str, str], hidden: Optional[set] = None) -> list[dict]:
    hidden = hidden or set()
    return [
        {"key": key, "label": label, "format": fmt, "style": styles.get(key)}
        for key, label, fmt in rows
        if key not in hidden
    ]


def fabrication_metric_rows() -> list[dict]:
    return _metric_rows(FABRICATION_ROWS, FABRICATION_ROW_STYLES)


def installer_metric_rows(variant: str) -> list[dict]:
    if variant == INSTALLER_VARIANT_AG:
        hidden = _SUB_ONLY_ROWS
    elif variant == INSTALLER_VARIANT_SUBS:
        hidden = _SUBS_HIDDEN_ROWS
    else:
        hidden = set()
    return _metric_rows(INSTALLER_ROWS, INSTALLER_ROW_STYLES, hidden)
