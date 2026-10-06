"""PDF export for the weekly labor cost reports.

Renders the same `metric_rows` the web page uses (labels, number formats and
row styles), so the PDF matches the on-screen report: one row per metric, one
column per week, and the month's TOTAL column computed by the backend.
"""
import calendar
import io
from datetime import date
from typing import Optional

from src.app.service.labor_cost_report_rows import BOLD, HIGHLIGHT, ROW_HIGHLIGHT_BG, ROW_HIGHLIGHT_TEXT
from src.app.utils.helpers import app_now


def format_metric(value, fmt: str) -> str:
    """Format a report value the way the web report does ("-" for blanks, sign before the $)."""
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if fmt == "currency":
        return f"{'-' if number < 0 else ''}${abs(number):,.2f}"
    if fmt == "percent":
        return f"{number:,.2f}%"
    if fmt == "count":
        return f"{number:,.1f}"
    if fmt == "days":
        return f"{number:,.0f}"
    return f"{number:,.2f}"


def _week_label(week_ending: str) -> str:
    try:
        day = date.fromisoformat(week_ending[:10])
    except ValueError:
        return week_ending
    return f"{calendar.month_abbr[day.month]} {day.day:02d}"


def build_labor_cost_pdf(data: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    monthly = data.get("monthly_report") or {}
    weeks: list[dict] = monthly.get("weekly_breakdown") or []
    totals: dict = monthly.get("totals") or {}
    metric_rows: list[dict] = data.get("metric_rows") or []
    period = data.get("period") or {}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        title=data.get("title") or "Labor Cost Report",
    )
    styles = getSampleStyleSheet()
    grey = colors.HexColor("#6B7280")
    border = colors.HexColor("#D1D5DB")
    header_bg = colors.HexColor("#F3F4F6")
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=15, spaceAfter=2)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=9, textColor=grey, spaceAfter=8)
    section_style = ParagraphStyle("Section", parent=styles["Heading3"], fontSize=11, spaceBefore=10, spaceAfter=4)

    month_label = f"{monthly.get('month', '')} {period.get('start_date', '')[:4]}".strip()
    first_week = weeks[0]["week_ending"] if weeks else None
    last_week = weeks[-1]["week_ending"] if weeks else None
    story = [
        Paragraph(data.get("title") or "Labor Cost Report", title_style),
        Paragraph(
            f"{month_label}  |  Period: {period.get('start_date', '-')} to {period.get('end_date', '-')}"
            + (f"  |  Weeks ending {first_week} to {last_week}" if first_week else "")
            + f"  |  Generated: {app_now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        ),
        Paragraph(f"Weekly Breakdown – {month_label}", section_style),
    ]

    header = ["METRIC", *[_week_label(w["week_ending"]) for w in weeks], "TOTAL"]
    body = [
        [row["label"], *[format_metric(w.get(row["key"]), row["format"]) for w in weeks],
         format_metric(totals.get(row["key"]), row["format"])]
        for row in metric_rows
    ]
    usable_width = landscape(letter)[0] - 0.8 * inch
    label_width = 2.6 * inch
    value_width = (usable_width - label_width) / max(len(header) - 1, 1)
    table = Table([header, *body], colWidths=[label_width, *[value_width] * (len(header) - 1)], repeatRows=1)

    commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, border),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),  # TOTAL column, as on screen
    ]
    for index, row in enumerate(metric_rows, start=1):
        commands.extend(row_style_commands(row.get("style"), index, colors))
    table.setStyle(TableStyle(commands))
    story.append(table)

    summary = data.get("annual_monthly_summary") or []
    if summary:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Annual Monthly Summary – {period.get('start_date', '')[:4]}", section_style))
        summary_columns = _summary_columns(summary[0])
        summary_table = Table(
            [[label for _, label, _ in summary_columns],
             *[[format_metric(item.get(key), fmt) if fmt else str(item.get(key) or "-") for key, _, fmt in summary_columns]
               for item in summary]],
            repeatRows=1,
        )
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, border),
        ]))
        story.append(summary_table)

    doc.build(story)
    return buf.getvalue()


def row_style_commands(style: Optional[str], row_index: int, colors) -> list[tuple]:
    """TableStyle commands for a metric row style, applied across the whole row."""
    if style == HIGHLIGHT:
        return [
            ("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor(ROW_HIGHLIGHT_BG)),
            ("TEXTCOLOR", (0, row_index), (-1, row_index), colors.HexColor(ROW_HIGHLIGHT_TEXT)),
            ("FONTNAME", (0, row_index), (-1, row_index), "Helvetica-Bold"),
        ]
    if style == BOLD:
        return [("FONTNAME", (0, row_index), (-1, row_index), "Helvetica-Bold")]
    return []


_SUMMARY_COLUMNS = [
    ("month", "MONTH", None),
    ("number_of_weeks", "WEEKS", "days"),
    ("completed_sqft", "SQFT", "number"),
    ("gross_revenue", "GROSS REVENUE", "currency"),
    ("gross_profit", "GROSS PROFIT", "currency"),
    ("total_labor_cost", "LABOR COST", "currency"),
    ("total_hours", "TOTAL HRS", "number"),
    ("labor_cost_pct_per_dollar_sold", "LABOR % OF $ SOLD", "percent"),
    ("gross_profit_less_installer_total_cost_psf", "GP LESS COST/SQFT", "currency"),
    ("gross_profit_less_shop_total_cost_psf", "GP LESS COST/SQFT", "currency"),
]


def _summary_columns(sample: dict) -> list[tuple]:
    return [column for column in _SUMMARY_COLUMNS if column[0] in sample]


def pdf_filename(report_key: str, year: int, month: int) -> str:
    return f"{report_key}_{year}-{month:02d}.pdf"
