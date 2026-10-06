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
    ("number_of_days", "Number of days", "days"),
    ("cut_sqft_saw", "Cut sq. ft (saw)", "number"),
    ("completed_sqft", "Completed sq. ft", "number"),
    ("average_sqft_per_day", "Average sq. ft per day", "number"),
    ("gross_revenue", "Gross revenue", "currency"),
    ("gross_profit", "Gross profit", "currency"),
    ("average_revenue_per_day", "Average revenue per day", "currency"),
    ("total_head_count_inc_yard", "Total head count (inc yard)", "count"),
    ("total_employees", "Total employees", "count"),
    ("wages_basic_shop_yard", "Wages basic shop & yard", "currency"),
    ("overtime_shop_yard", "Overtime shop & yard", "currency"),
    ("cost_of_overtime_pct", "Cost of overtime as a % of basic wages", "percent"),
    ("total_labor_cost", "Total labor cost", "currency"),
    ("regular_hours", "Regular hours", "number"),
    ("overtime_hours", "Overtime hours", "number"),
    ("overtime_hours_pct", "Overtime hours as % of total hours", "percent"),
    ("total_hours", "Total hours", "number"),
    ("shop_labor_per_hour", "Shop labor per hour", "currency"),
    ("shop_overhead_per_hour", "Shop overhead per hour", "currency"),
    ("shop_labor_overhead_per_hour", "Shop labor & overhead per hour", "currency"),
    ("manpower_cost_per_hour", "Manpower cost per hour", "currency"),
    ("sqft_per_labor_hour", "Sq. ft per labor hour", "number"),
    ("shop_productivity_sqft_per_hour", "Shop productivity - sq. ft per hour", "number"),
    ("labor_cost_per_sq_ft", "Labor cost per sq. ft", "currency"),
    ("labor_cost_pct_per_dollar_sold", "Labor cost as % per dollar sold", "percent"),
    ("shop_overhead_cost_per_sqft", "Shop overhead cost per sq. ft fabricated", "currency"),
    ("shop_total_cost_per_sqft", "Shop total cost per sq. ft fabricated", "currency"),
    ("gross_profit_per_sf_completed", "Gross profit per sq. ft completed", "currency"),
    ("gross_profit_less_shop_total_cost_psf", "Gross profit less shop total cost per sq. ft", "currency"),
    ("gross_revenue_per_sqft_fabricated", "Gross revenue per sq. ft fabricated", "currency"),
]

INSTALLER_ROWS = [
    ("number_of_days_per_week", "Number of days per week", "days"),
    ("install_sqft_per_week", "Install sq. ft per week", "number"),
    ("completed_sqft_per_week", "Completed sq. ft per week", "number"),
    ("average_sqft_per_day", "Average sq. ft per day", "number"),
    ("gross_revenue", "Gross revenue", "currency"),
    ("gross_profit", "Gross profit", "currency"),
    ("average_revenue_per_day", "Average revenue per day", "currency"),
    ("sub_contractor_head_count", "Sub contractor head count", "count"),
    ("wages_sub_contractor", "Total labor cost - sub contractor", "currency"),
    ("total_head_count", "Total head count", "count"),
    ("wages_basic_installer", "Wages basic installer", "currency"),
    ("overtime_installer", "Overtime installer", "currency"),
    ("overtime_pct", "% overtime", "percent"),
    ("total_labor_cost", "Total labor cost", "currency"),
    ("regular_hours", "Regular hours", "number"),
    ("overtime_hours", "Overtime hours", "number"),
    ("overtime_total_hours_pct", "% overtime of total hours", "percent"),
    ("total_hours", "Total hours", "number"),
    ("hourly_labor_cost_all_installers", "Hourly labor cost for all installers", "currency"),
    ("hourly_overhead_cost_all_installers", "Hourly overhead cost for all installers", "currency"),
    ("hourly_cost_all_installers_inc_overhead", "Hourly cost of all installers inc overhead", "currency"),
    ("hourly_cost_per_installer_inc_overhead", "Hourly cost per installer inc overhead", "currency"),
    ("sqft_per_labor_hour", "Sq. ft per labor hour", "number"),
    ("installer_productivity_sqft_per_hour", "Installer productivity - sq. ft per hour", "number"),
    ("labor_cost_per_sq_ft", "Labor cost per sq. ft", "currency"),
    ("labor_cost_pct_per_dollar_sold", "Labor cost as % per dollar sold", "percent"),
    ("overhead_cost_per_sqft_installed", "Overhead cost per sq. ft installed", "currency"),
    ("overhead_per_week", "Overhead per week", "currency"),
    ("cost_to_install_per_sqft", "Cost to install per sq. ft", "currency"),
    ("gross_profit_per_sf_installed", "Gross profit per sq. ft installed", "currency"),
    ("gross_profit_less_installer_total_cost_psf", "Gross profit less installer total cost per sq. ft", "currency"),
    ("gross_revenue_per_sq_ft", "Gross revenue per sq. ft", "currency"),
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
