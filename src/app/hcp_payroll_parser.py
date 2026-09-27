import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from xml.etree import ElementTree as ET


@dataclass
class ParsedHcpPayrollRow:
    row_kind: str
    row_index: int
    cost_center_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_first_name: Optional[str] = None
    employee_last_name: Optional[str] = None
    hourly_pay: Optional[float] = None
    regular_hours: Optional[float] = None
    holiday_hours: Optional[float] = None
    pto_hours: Optional[float] = None
    total_reg_pto_hol_wages: Optional[float] = None
    overtime_hours: Optional[float] = None
    total_ot_wages: Optional[float] = None
    raw_line_text: Optional[str] = None


@dataclass
class ParsedHcpStaffRosterRow:
    row_index: int
    employee_id: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_status: Optional[str] = None
    employee_type: Optional[str] = None
    in_payroll: Optional[str] = None
    locked: Optional[str] = None
    date_terminated: Optional[str] = None
    is_active: bool = False
    raw_line_text: Optional[str] = None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError, InvalidOperation):
        return None


_THOUSANDS_SEPARATOR_DOLLAR = re.compile(r"\$\d{1,3}(?:,\d{3})+\.\d{2}")


def _merge_unquoted_thousands_separators(text: str) -> str:
    """Collapse "$1,515.82" -> "$1515.82" so an unquoted comma inside a dollar
    amount isn't mistaken for a CSV field separator (HCP does not quote these).
    """
    return _THOUSANDS_SEPARATOR_DOLLAR.sub(lambda m: m.group(0).replace(",", ""), text)


def _parse_payload_rows(raw_payload_text: str) -> list[list[str]]:
    lines = [line for line in (raw_payload_text or "").splitlines() if line.strip()]
    parsed_rows: list[list[str]] = []

    for line in lines:
        try:
            parsed_rows.append(next(csv.reader(io.StringIO(line))))
        except Exception:
            parsed_rows.append([line])

    return parsed_rows


_PAYROLL_FIELD_BY_HEADER = {
    "employee id": "employee_id",
    "first name": "employee_first_name",
    "last name": "employee_last_name",
    "hourly pay": "hourly_pay",
    "regular hours": "regular_hours",
    "holiday hours": "holiday_hours",
    "pto hours": "pto_hours",
    "total reg/pto/hol wages": "total_reg_pto_hol_wages",
    "overtime hours": "overtime_hours",
    "total ot wages": "total_ot_wages",
}

# Column order when no header row is present in the payload (legacy fallback).
_PAYROLL_DEFAULT_FIELD_ORDER = [
    None,
    "employee_first_name",
    "employee_last_name",
    "hourly_pay",
    "regular_hours",
    "holiday_hours",
    "pto_hours",
    "total_reg_pto_hol_wages",
    "overtime_hours",
    "total_ot_wages",
]


def parse_hcp_payroll_report(raw_payload_text: str) -> list[ParsedHcpPayrollRow]:
    if not raw_payload_text:
        return []

    stripped = raw_payload_text.lstrip()
    if stripped.startswith("<"):
        try:
            ET.fromstring(raw_payload_text)
        except ET.ParseError:
            pass

    parsed_rows = _parse_payload_rows(_merge_unquoted_thousands_separators(raw_payload_text))
    current_cost_center: Optional[str] = None
    pending_subtotal = False
    field_order = _PAYROLL_DEFAULT_FIELD_ORDER
    results: list[ParsedHcpPayrollRow] = []

    for row_index, row in enumerate(parsed_rows, start=1):
        normalized = [value.strip() for value in row]
        if not any(normalized):
            continue

        first_cell = normalized[0] if len(normalized) > 0 else ""

        if first_cell.lower().startswith("cost center name"):
            current_cost_center = normalized[1] if len(normalized) > 1 else current_cost_center
            pending_subtotal = False
            continue

        if any(cell.lower() in _PAYROLL_FIELD_BY_HEADER for cell in normalized):
            # Column layout (e.g. an extra Employee Id column) varies by export; read it from the header.
            field_order = [_PAYROLL_FIELD_BY_HEADER.get(cell.lower()) for cell in normalized]
            continue

        if first_cell.lower() == "subtotal":
            pending_subtotal = True
            continue

        values: dict[str, str] = {}
        # HCP sometimes emits an extra (undeclared) column, e.g. Employee Id,
        # right after the leading blank cell. Align the header's field order to
        # the row from the position right after that leading cell so every
        # later column still lands correctly regardless of that extra field.
        offset = max(0, len(normalized) - len(field_order))
        for position, field_name in enumerate(field_order):
            if not field_name:
                continue
            source_index = position + offset if position >= 1 else position
            if source_index >= len(normalized):
                continue
            values[field_name] = normalized[source_index]

        if "employee_id" not in values and offset >= 1 and len(normalized) > 1:
            # Header doesn't declare the column, but it's always the extra field
            # right after the leading blank cell when present.
            values["employee_id"] = normalized[1]

        if pending_subtotal:
            pending_subtotal = False
            results.append(
                ParsedHcpPayrollRow(
                    row_kind="subtotal",
                    row_index=row_index,
                    cost_center_name=current_cost_center,
                    regular_hours=_to_float(values.get("regular_hours")),
                    total_reg_pto_hol_wages=_to_float(values.get("total_reg_pto_hol_wages")),
                    overtime_hours=_to_float(values.get("overtime_hours")),
                    total_ot_wages=_to_float(values.get("total_ot_wages")),
                    raw_line_text=",".join(row),
                )
            )
            continue

        if current_cost_center and values.get("employee_first_name") and values.get("employee_last_name"):
            results.append(
                ParsedHcpPayrollRow(
                    row_kind="detail",
                    row_index=row_index,
                    cost_center_name=current_cost_center,
                    employee_id=values.get("employee_id") or None,
                    employee_first_name=values.get("employee_first_name"),
                    employee_last_name=values.get("employee_last_name"),
                    hourly_pay=_to_float(values.get("hourly_pay")),
                    regular_hours=_to_float(values.get("regular_hours")),
                    holiday_hours=_to_float(values.get("holiday_hours")),
                    pto_hours=_to_float(values.get("pto_hours")),
                    total_reg_pto_hol_wages=_to_float(values.get("total_reg_pto_hol_wages")),
                    overtime_hours=_to_float(values.get("overtime_hours")),
                    total_ot_wages=_to_float(values.get("total_ot_wages")),
                    raw_line_text=",".join(row),
                )
            )

    return results


_STAFF_ROSTER_FIELD_BY_HEADER = {
    "employee id": "employee_id",
    "username": "username",
    "first name": "first_name",
    "last name": "last_name",
    "employee status": "employee_status",
    "employee type": "employee_type",
    "in payroll": "in_payroll",
    "locked": "locked",
    "date terminated": "date_terminated",
}

_STAFF_ROSTER_DEFAULT_FIELD_ORDER = [
    "employee_id",
    "username",
    "first_name",
    "last_name",
    "employee_status",
    "employee_type",
    "in_payroll",
    "locked",
    "date_terminated",
]


def parse_hcp_staff_roster(raw_payload_text: str) -> list[ParsedHcpStaffRosterRow]:
    if not raw_payload_text:
        return []

    field_order = _STAFF_ROSTER_DEFAULT_FIELD_ORDER
    results: list[ParsedHcpStaffRosterRow] = []
    row_index = 0

    for row in _parse_payload_rows(raw_payload_text):
        normalized = [value.strip() for value in row]
        if not any(normalized):
            continue

        if normalized[0].lower() in _STAFF_ROSTER_FIELD_BY_HEADER:
            field_order = [_STAFF_ROSTER_FIELD_BY_HEADER.get(value.lower(), "") for value in normalized]
            continue

        values: dict[str, Optional[str]] = {}
        for position, field_name in enumerate(field_order):
            if not field_name or position >= len(normalized):
                continue
            values[field_name] = normalized[position] or None

        row_index += 1
        status = values.get("employee_status")
        results.append(
            ParsedHcpStaffRosterRow(
                row_index=row_index,
                employee_id=values.get("employee_id"),
                username=values.get("username"),
                first_name=values.get("first_name"),
                last_name=values.get("last_name"),
                employee_status=status,
                employee_type=values.get("employee_type"),
                in_payroll=values.get("in_payroll"),
                locked=values.get("locked"),
                date_terminated=values.get("date_terminated"),
                is_active=(status or "").strip().lower() == "active",
                raw_line_text=",".join(row),
            )
        )

    return results