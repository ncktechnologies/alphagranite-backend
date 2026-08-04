from src.app.hcp_payroll_parser import parse_hcp_payroll_report


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
    assert rows[2].total_ot_wages == 124.38