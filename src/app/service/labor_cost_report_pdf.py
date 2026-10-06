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
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle

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

    usable_width = landscape(letter)[0] - 0.8 * inch

    def pivot_table(column_labels: list[str], column_values: list[dict], period_totals: dict,
                    label_width: float, font_size: float):
        """Metric rows x period columns + TOTAL, styled like the web table."""
        header = ["METRIC", *column_labels, "TOTAL"]
        body = [
            [row["label"], *[format_metric(values.get(row["key"]), row["format"]) for values in column_values],
             format_metric(period_totals.get(row["key"]), row["format"])]
            for row in metric_rows
        ]
        value_width = (usable_width - label_width) / max(len(header) - 1, 1)
        table = Table([header, *body], colWidths=[label_width, *[value_width] * (len(header) - 1)], repeatRows=1)
        commands = [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
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
        return table

    story.append(pivot_table([_week_label(w["week_ending"]) for w in weeks], weeks, totals, 2.6 * inch, 7.5))

    # Annual summary: the same rows month by month with the year's total, as on screen.
    annual = data.get("annual_report") or {}
    months: list[dict] = annual.get("monthly_breakdown") or []
    if months:
        year = annual.get("year") or period.get("start_date", "")[:4]
        story.append(PageBreak())
        story.append(Paragraph(f"Annual Monthly Summary – {year}", section_style))
        story.append(pivot_table([str(m.get("month", ""))[:3].upper() for m in months], months,
                                 annual.get("totals") or {}, 2.1 * inch, 6.3))

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



def pdf_filename(report_key: str, year: int, month: int) -> str:
    return f"{report_key}_{year}-{month:02d}.pdf"
