"""Generate synthetic Caspio-style sample CSVs for migration testing.

Reads real headers from Caspio_Tables/ (schema-only exports) so columns match
exactly, then writes sample_data/ CSVs with deterministic rows covering:
  normal full-lifecycle fab, *_not_needed flags, blank account, bad sqft,
  redo/revision, resurface, open + closed timer sessions, orphan session row,
  unknown activity/machine/employee (fallback paths), revision_info rows,
  lookups, production rollups.
Deterministic: no randomness; reruns produce identical files.
"""
import csv
import os

SRC = "/Users/cugwuh/Downloads/data_migration/Caspio_Tables"
DST = "/Users/cugwuh/Downloads/data_migration/sample_data"
os.makedirs(DST, exist_ok=True)

FILES = sorted(f for f in os.listdir(SRC) if f.endswith(".csv"))
HEADERS = {}
for fn in FILES:
    with open(os.path.join(SRC, fn), encoding="utf-8-sig") as fh:
        HEADERS[fn] = next(csv.reader(fh))

SHORT = {fn: fn.split("_2026")[0] for fn in FILES}


def blank_row(fn):
    return {h: "" for h in HEADERS[fn]}


def write(fn, rows):
    hdr = HEADERS[fn]
    with open(os.path.join(DST, fn), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"{SHORT[fn]}: {len(rows)} rows")


def F(fn, **kw):
    r = blank_row(fn)
    r.update(kw)
    return r


def fab_status_file():
    return [f for f in FILES if SHORT[f] == "Fab_Status"][0]


FS = fab_status_file()

# --- 10 fabs, 3 accounts, 4 jobs -------------------------------------------
fabs = [
    # 9001: golden full-lifecycle fab, everything complete
    dict(fab_id="9001", fab_type="STANDARD", account="Acme Builders",
         job_name="Kitchen Remodel", job_number="JOB-100",
         areas="Kitchen", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="120.5",
         number_pieces="4", creation_date="09/01/2026 09:00",
         template_completed="Yes", template_date_completed="09/02/2026 10:00",
         template_by="tpl.smith", draft_completed="Yes",
         draft_date_completed="09/04/2026 15:00", draft_by="draft.jones",
         draft_notes="Verify sink cutout",
         pre_draft_review_completed="Yes", pre_draft_review="Check measurements",
         slabsmith_complete="Yes", slabsmith_completion_date="09/05/2026 12:00",
         slabsmith_notes="Slab approved by customer",
         sct_completed="Yes", sct_date_completed="09/06/2026 11:00",
         sct_by="sct.lee", sct_notes="Sales CT ok",
         final_completed="Yes", final_date_completed="09/08/2026 16:00",
         final_by="fp.kim", final_notes="Final program verified",
         shop_date_scheduled="09/09/2026 08:00",
         cut_sqft="120.5", cut_date_scheduled="09/09/2026 08:00",
         cut_hours_scheduled="3", cut_machine_scheduled="SAW 1",
         cut_employee_scheduled="shop.cortez", cut_percent="100",
         cut_date_completed="09/09/2026 11:00", cut_by="shop.cortez",
         wj_time="45", wj_linft="30.5", wj_date_scheduled="09/09/2026 12:00",
         wj_hours_scheduled="1", wj_machine_scheduled="WATERJET",
         wj_employee_scheduled="shop.cortez", wj_percent="100",
         wj_date_completed="09/09/2026 13:00", wj_by="shop.cortez",
         edging_linft="28.0", edging_date_scheduled="09/10/2026 08:00",
         edging_hours_scheduled="2", edging_machine_scheduled="EDGER 1",
         edging_employee_scheduled="shop.diaz", edging_percent="100",
         edging_date_completed="09/10/2026 10:00", edging_by="shop.diaz",
         miter_linft="12.0", miter_date_scheduled="09/10/2026 11:00",
         miter_hours_scheduled="1", miter_machine_scheduled="MITER 1",
         miter_employee_scheduled="shop.diaz", miter_percent="100",
         miter_date_completed="09/10/2026 12:00", miter_by="shop.diaz",
         cnc_linft="15.0", cnc_date_scheduled="09/10/2026 13:00",
         cnc_hours_scheduled="2", cnc_machine_scheduled="CNC 1",
         cnc_employee_scheduled="shop.park", cnc_percent="100",
         cnc_date_completed="09/10/2026 15:00", cnc_by="shop.park",
         qc_sqft="120.5", qc_date_scheduled="09/11/2026 08:00",
         qc_hours_scheduled="1", qc_percent="100",
         qc_date_completed="09/11/2026 09:00", qc_by="qc.nguyen",
         completion_date="09/12/2026 10:00", fab_percent="100",
         shop_notes="Ready to ship", install_notes="Call before arrival",
         install_date="09/13/2026 09:00", installer="inst.rivera",
         install_confirmed="Yes", complete="Yes",
         revenue="4500.00", cost_of_stone="1200.00", cost_entered="Yes",
         gp="1800.00"),
    # 9002: same job, template/draft not needed
    dict(fab_id="9002", fab_type="FAB ONLY", account="Acme Builders",
         job_name="Kitchen Remodel", job_number="JOB-100",
         areas="Bath", stone_type="MS", stone_color="Agger Grey",
         stone_thickness="2cm", edge="DEMI BULLNOSE", total_sqft="45.0",
         number_pieces="2", creation_date="09/01/2026 09:30",
         template_not_needed="Yes", draft_not_needed="Yes",
         slabsmith_complete="Yes", slabsmith_completion_date="09/05/2026 14:00",
         sct_not_needed="Yes", final_not_needed="Yes",
         shop_date_scheduled="09/09/2026 08:00",
         cut_sqft="45.0", cut_date_scheduled="09/09/2026 08:00",
         cut_hours_scheduled="1.5", cut_machine_scheduled="SAW 2",
         cut_employee_scheduled="shop.cortez", cut_percent="50",
         complete="No", revenue="1500.00", cost_of_stone="400.00",
         cost_entered="Yes", gp="500.00"),
    # 9003: blank account + novel stone/edge (upsert path), in-progress
    dict(fab_id="9003", fab_type="SYNTHETIC NEW TYPE", account="",
         job_name="", job_number="JOB-101",
         areas="Outdoor Kitchen", stone_type="SYNTH STONE",
         stone_color="Synth White", stone_thickness="9cm", edge="SYNTH EDGE",
         total_sqft="80", number_pieces="3", creation_date="09/03/2026 10:00",
         template_completed="No", draft_completed="No",
         complete="No", revenue="2200.00"),
    # 9004: bad numeric sqft (fallback path) + redo fields
    dict(fab_id="9004", fab_type="CUST REDO", account="Beta Homes",
         job_name="Redo Island", job_number="JOB-102",
         areas="Island", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="N/A",
         number_pieces="two", creation_date="09/04/2026 11:00",
         been_revised="Yes", revision_completion_date="09/07/2026 12:00",
         redo_reason="Chip on edge", redo_dept="FABRICATION",
         redo_person="shop.cortez", redo_cost="250.00",
         revenue="900.00", cost_of_stone="300.00", cost_entered="No",
         gp="150.00", complete="No"),
    # 9005: resurface fab
    dict(fab_id="9005", fab_type="RESURFACE", account="Beta Homes",
         job_name="Resurface Vanity", job_number="JOB-102",
         areas="Vanity", stone_type="GS", stone_color="Airy Concrete",
         stone_thickness="2cm", edge="BEVEL", total_sqft="25.5",
         number_pieces="1", creation_date="09/05/2026 08:00",
         resurface_sqft="25.5", resurface_percent="100",
         resurface_date_completed="09/06/2026 16:00", resurface_by="shop.park",
         shop_date_scheduled="09/06/2026 08:00", complete="Yes",
         completion_date="09/06/2026 16:30",
         revenue="600.00", cost_of_stone="100.00", cost_entered="Yes",
         gp="200.00"),
    # 9006-9010: small fabs for second account, mixed states
    dict(fab_id="9006", fab_type="STANDARD", account="Gamma Condos",
         job_name="Tower A", job_number="JOB-103",
         areas="Unit 101", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="60",
         number_pieces="2", creation_date="09/06/2026 09:00",
         template_completed="Yes", template_date_completed="09/07/2026 10:00",
         template_by="tpl.smith", complete="No", revenue="2000.00",
         cost_of_stone="500.00", cost_entered="Yes", gp="700.00"),
    dict(fab_id="9007", fab_type="STANDARD", account="Gamma Condos",
         job_name="Tower A", job_number="JOB-103",
         areas="Unit 102", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="62",
         number_pieces="2", creation_date="09/06/2026 09:15",
         complete="No", revenue="2050.00"),
    dict(fab_id="9008", fab_type="FAST TRACK", account="Gamma Condos",
         job_name="Tower B", job_number="JOB-104",
         areas="Lobby", stone_type="DK", stone_color="Arabetto",
         stone_thickness="2cm", edge="COVE", total_sqft="200",
         number_pieces="6", creation_date="09/07/2026 09:00",
         slabsmith_ag_not_needed="Yes", slabsmith_cust_not_needed="No",
         complete="No", revenue="8000.00", cost_of_stone="2500.00",
         cost_entered="Yes", gp="3000.00"),
    dict(fab_id="9009", fab_type="STANDARD", account="acme builders",
         job_name="Kitchen Remodel", job_number="JOB-100",
         areas="Pantry", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="30",
         number_pieces="1", creation_date="09/08/2026 09:00",
         complete="No", revenue="800.00"),
    dict(fab_id="9010", fab_type="STANDARD", account="Acme Builders",
         job_name="Kitchen Remodel", job_number="JOB-100",
         areas="Laundry", stone_type="MS", stone_color="Adamina",
         stone_thickness="3cm", edge="BEVEL", total_sqft="28",
         number_pieces="1", creation_date="09/08/2026 09:30",
         being_revised="Yes", complete="No", revenue="750.00"),
]

write(FS, [F(FS, **kw) for kw in fabs])

# --- Draft_Data: closed + open sessions for 9001, one for 9006 ---------------
DD = [f for f in FILES if SHORT[f] == "Draft_Data"][0]
write(DD, [
    F(DD, fab_id="9001", draft_duration="90", start_time="09/03/2026 09:00",
      end_time="09/03/2026 10:30", drafter="draft.jones", state="completed",
      active_session="No", session_duration="90"),
    F(DD, fab_id="9001", draft_duration="", start_time="09/04/2026 13:00",
      end_time="", drafter="draft.jones", state="in progress",
      active_session="Yes", session_start_time="09/04/2026 13:00",
      intermediary="paused for review", new_duration="30"),
    F(DD, fab_id="9006", draft_duration="2 hours", start_time="09/07/2026 09:00",
      end_time="09/07/2026 11:00", drafter="draft.unknown.person",
      state="completed", active_session="No", session_duration="120"),
])

# --- FP_Data ------------------------------------------------------------------
FP = [f for f in FILES if SHORT[f] == "FP_Data"][0]
write(FP, [
    F(FP, fab_id="9001", programming_duration="60",
      start_time="09/08/2026 14:00", end_time="09/08/2026 15:00",
      programmer="fp.kim", state="completed", active_session="No",
      session_duration="60"),
    F(FP, fab_id="9002", programming_duration="",
      start_time="09/09/2026 10:00", end_time="", programmer="fp.kim",
      state="in progress", active_session="Yes",
      session_start_time="09/09/2026 10:00"),
])

# --- Shop_Data: CUT/WJ/EDGING + unknown activity + orphan --------------------
SD = [f for f in FILES if SHORT[f] == "Shop_Data"][0]
write(SD, [
    F(SD, fab_id="9001", activity="CUT", cut_machine="SAW 1",
      shop_employee="shop.cortez", start_time="09/09/2026 08:00",
      stop_time="09/09/2026 11:00", duration="180", measure="120.5",
      units="sqft", percent_complete="100"),
    F(SD, fab_id="9001", activity="WJ", shop_employee="shop.cortez",
      start_time="09/09/2026 12:00", stop_time="09/09/2026 13:00",
      duration="60", measure="30.5", units="linft", percent_complete="100"),
    F(SD, fab_id="9002", activity="POLISH", cut_machine="",
      edging_machine="", shop_employee="shop.diaz",
      start_time="09/09/2026 09:00", stop_time="09/09/2026 10:00",
      duration="60", measure="45", units="sqft", percent_complete="50"),
    F(SD, fab_id="9999", activity="CUT", cut_machine="SAW 1",
      shop_employee="shop.cortez", start_time="09/09/2026 08:00",
      stop_time="09/09/2026 09:00", duration="60", measure="10",
      units="sqft", percent_complete="100"),
])

# --- revision_info -------------------------------------------------------------
RI = [f for f in FILES if SHORT[f] == "revision_info"][0]
write(RI, [
    F(RI, revision_date_completed="09/07/2026 12:00", Account="Beta Homes",
      Edge="BEVEL", StoneThickness="3cm", StoneColor="Adamina",
      StoneType="MS", Areas="Island", JobName="Redo Island",
      RevisionReason="Chip on edge", FabID="9004", FabType="CUST REDO",
      JobNumber="JOB-102", NumPieces="1", creation_date="09/06/2026 10:00",
      TotalSqft="40", SalesPerson="sales.adams", Revisor="shop.cortez",
      RevisionType="SHOP"),
    F(RI, revision_date_completed="", Account="Acme Builders",
      Edge="BEVEL", StoneThickness="3cm", StoneColor="Adamina",
      StoneType="MS", Areas="Laundry", JobName="Kitchen Remodel",
      RevisionReason="Customer moved sink", FabID="9010", FabType="STANDARD",
      JobNumber="JOB-100", NumPieces="1", DraftNotes="Move sink 2in left",
      DraftCompleted="No", creation_date="09/09/2026 10:00",
      TotalSqft="28", SalesPerson="sales.adams", Revisor="draft.jones",
      FileData="/files/rev9010.pdf", RevisionType="DRAFT"),
])

# --- lookups -------------------------------------------------------------------
def simple(short, col, values):
    fn = [f for f in FILES if SHORT[f] == short][0]
    hdr = HEADERS[fn]
    rows = []
    for v in values:
        r = {h: "" for h in hdr}
        if len(hdr) == 2:
            r[hdr[0]] = v[0]
            r[hdr[1]] = v[1]
        else:
            for h, val in zip(hdr, v):
                r[h] = val
        rows.append(r)
    write(fn, rows)


simple("Fab_Types", None, [("1", "STANDARD"), ("2", "FAB ONLY"),
                            ("3", "CUST REDO"), ("4", "SYNTHETIC NEW TYPE")])
simple("Machines_CNC", None, [("1", "CNC 1")])
simple("Machines_Cut", None, [("1", "SAW 1"), ("2", "SAW 2")])
simple("Machines_Edging", None, [("1", "EDGER 1")])
simple("Active_Sales_Employees", None, [("101", "sales.adams")])
simple("Alpha_Employees", None,
       [("1001", "Cortez", "Shop"), ("1002", "Diaz", "Shop")])
simple("Employees_Shop", None,
       [("1001", "Cortez", "Shop", "shop.cortez", "Yes"),
        ("1002", "Diaz", "Shop", "shop.diaz", "Yes"),
        ("1003", "Park", "Shop", "shop.park", "No")])
simple("Employees_Template", None,
       [("201", "tpl.smith"), ("202", "draft.jones")])
simple("Default_Shop_Employees", None,
       [("CUT", "shop.cortez"), ("WJ", "shop.cortez")])

CAL = [f for f in FILES if SHORT[f] == "Calendar"][0]
write(CAL, [F(CAL, date=d) for d in
            ["09/01/2026", "09/02/2026", "09/03/2026"]])

PPP = [f for f in FILES if SHORT[f] == "ProductionPerPerson"][0]
write(PPP, [
    F(PPP, Tmestamp="09/09/2026 17:00", Name="shop.cortez", ClockNum="1001",
      Dept="CUT", SqFt="165.5", LinFt="30.5"),
    F(PPP, Tmestamp="09/10/2026 17:00", Name="shop.diaz", ClockNum="1002",
      Dept="EDGING", SqFt="28", LinFt="28"),
])

PT = [f for f in FILES if SHORT[f] == "Production_Table_1"][0]
write(PT, [
    F(PT, DateActual="09/09/2026", SawSqFt="165.5", WJLinFt="30.5",
      TotalSqFt="196", Notes="day shift"),
])

print("done:", DST)
