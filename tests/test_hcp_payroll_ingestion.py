from src.app.hcp_payroll_parser import parse_hcp_payroll_report, parse_hcp_staff_roster


def test_parse_hcp_payroll_report_handles_cost_centers_and_subtotals():
    raw_payload = '''
"","First Name","Last Name","Hourly Pay","Regular Hours","Holiday Hours","PTO Hours","Total REG/PTO/HOL Wages","Overtime Hours","Total OT Wages"

" Cost Center Name (1)","Fabrication"

"","Justin","Calzada","$22.00","40.00","","","$880.00","0.94","$31.02"
"","Jose","Corona","$16.00","40.00","","","$640.00","3.89","$93.36"
"Subtotal"
"","","","","80.00","","","$1,520.00","4.83","$124.38"
'''

    rows = parse_hcp_payroll_report(raw_payload)

    assert len(rows) == 3
    assert rows[0].row_kind == "detail"
    assert rows[0].cost_center_name == "Fabrication"
    assert rows[0].employee_first_name == "Justin"
    assert rows[0].employee_last_name == "Calzada"
    assert rows[0].hourly_pay == 22.0
    assert rows[0].regular_hours == 40.0
    assert rows[0].overtime_hours == 0.94
    assert rows[1].employee_first_name == "Jose"
    assert rows[2].row_kind == "subtotal"
    assert rows[2].cost_center_name == "Fabrication"
    assert rows[2].regular_hours == 80.0
    assert rows[2].total_reg_pto_hol_wages == 1520.0


def test_parse_hcp_payroll_report_handles_unquoted_employee_id_and_thousands_separator():
    """Real HCP exports add an undeclared Employee Id column and leave dollar
    amounts >= $1,000 unquoted, so a naive CSV split shifts every later column.
    """
    raw_payload = '''
"","First Name","Last Name","Hourly Pay","Regular Hours","Holiday Hours","PTO Hours","Total REG/PTO/HOL Wages","Overtime Hours","Total OT Wages"

" Cost Center Name (1)","CAD"

,516,Joshua,McVey,$38.00,39.89,,,$1,515.82,,$0
,44,Erick,Santoyo,$25.50,40.00,,,$1,020.00,0.30,$11.48
"Subtotal"
,,,,,79.89,,,$2,535.82,0.30,$11.48
'''

    rows = parse_hcp_payroll_report(raw_payload)

    assert len(rows) == 3
    assert rows[0].employee_first_name == "Joshua"
    assert rows[0].employee_last_name == "McVey"
    assert rows[0].hourly_pay == 38.0
    assert rows[0].regular_hours == 39.89
    assert rows[0].total_reg_pto_hol_wages == 1515.82
    assert rows[0].overtime_hours is None
    assert rows[0].total_ot_wages == 0.0

    assert rows[1].employee_first_name == "Erick"
    assert rows[1].employee_last_name == "Santoyo"
    assert rows[1].total_reg_pto_hol_wages == 1020.0
    assert rows[1].overtime_hours == 0.30
    assert rows[1].total_ot_wages == 11.48

    assert rows[2].row_kind == "subtotal"
    assert rows[2].regular_hours == 79.89
    assert rows[2].total_reg_pto_hol_wages == 2535.82
    assert rows[2].overtime_hours == 0.30
    assert rows[2].total_ot_wages == 11.48


def test_parse_hcp_staff_roster_flags_active_employees():
    raw_payload = '''
"Employee Id","Username","First Name","Last Name","Employee Status","Employee Type","In Payroll","Locked","Date Terminated"

"247","JHernandez","Jose Luis","Hernandez","Active","Full Time","Yes","No",""

"415","MHernandez","Mary","Hernandez","Terminated","Full Time","No","Yes","2025-01-02"
'''

    rows = parse_hcp_staff_roster(raw_payload)

    assert len(rows) == 2
    assert [row.row_index for row in rows] == [1, 2]
    assert rows[0].employee_id == "247"
    assert rows[0].username == "JHernandez"
    assert rows[0].first_name == "Jose Luis"
    assert rows[0].employee_status == "Active"
    assert rows[0].is_active is True
    assert rows[0].date_terminated is None
    assert rows[1].is_active is False
    assert rows[1].date_terminated == "2025-01-02"
    assert sum(1 for row in rows if row.is_active) == 1