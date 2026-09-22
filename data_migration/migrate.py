"""Caspio -> Odyssey Tracker migration (idempotent).

Usage:
    python3 migrate.py --input sample_data --db odyssey_migration_test
    python3 migrate.py --input Caspio_Tables --db odyssey_migration_test --dry-run

Implements mapping_matrix.csv / Caspio_to_Odyssey_mapping.md:
  Phase 1 refs -> Phase 2 core+stages -> Phase 3 history, with reject table,
  unresolved-reference backlog, and reconciliation report. Safe to re-run:
  every entity resolves by natural key and updates in place (zero growth).
Requires target DB cloned from staging (schema + seeds). Never run against
production without a backup.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import psycopg2
import psycopg2.extras

SRC_TZ = ZoneInfo("America/Chicago")
ACTIVE, COMPLETED = 1, 8  # status.value_id
MIG_USER = "migration_bot"

BOOL_TRUE = {"yes", "y", "true", "t", "1", "complete", "completed", "done"}
BOOL_FALSE = {"no", "n", "false", "f", "0"}


def parse_bool(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if not s:
        return None
    if s in BOOL_TRUE:
        return True
    if s in BOOL_FALSE:
        return False
    return None


def needed(not_needed_val, default=True):
    """fab 'X_not_needed' -> 'x_needed' (inverted). Blank means needed."""
    b = parse_bool(not_needed_val)
    return (not b) if b is not None else default


def parse_float(v):
    if v is None:
        return None
    s = str(v).strip().lower().replace(",", "").replace("$", "")
    s = re.sub(r"(sq\s*ft|sqft|lin\s*ft|linft|ln\s*ft|lnft|ft|%|hrs?|hours?|mins?|minutes?|secs?|seconds?)+$", "", s).strip()
    if s in ("", "n/a", "na", "none", "-", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_int(v):
    f = parse_float(v)
    return int(f) if f is not None else None


def parse_dt(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    for fmt in (
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%m/%d/%y %I:%M:%S %p",
        "%m/%d/%y %I:%M %p",
        "%m/%d/%y %H:%M",
        "%m/%d/%y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=SRC_TZ).astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def parse_duration_sec(v):
    """Bare numbers are minutes (Caspio clock convention); hours/secs by suffix."""
    if v is None:
        return None
    s = str(v).strip().lower()
    if not s:
        return None
    num = parse_float(s)
    if num is None:
        return None
    if "hour" in s or s.endswith("h"):
        return int(num * 3600)
    if "sec" in s:
        return int(num)
    return int(num * 60)


def parse_thickness_mm(v):
    f = parse_float(v)
    if f is None:
        return None
    s = str(v).lower()
    if "mm" in s:
        return f
    if "cm" in s:
        return f * 10
    return None


class Ctx:
    def __init__(self, conn, dry_run=False):
        self.conn = conn
        self.cur = conn.cursor()
        self.dry_run = dry_run
        self.now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.counts = defaultdict(lambda: defaultdict(int))  # entity -> op -> n
        self.mig_user = None
        self.accounts = {}      # lower name -> id
        self.jobs = {}          # job_number -> id
        self.fabs = {}          # fab_id -> job_id
        self.stations = {}      # lower name -> id
        self.plan_sections = {}  # UPPER name -> id

    # -- infra ----------------------------------------------------------
    def ensure_helper_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS migration_rejects(
                id serial PRIMARY KEY, source_table varchar NOT NULL,
                source_key varchar, reason varchar NOT NULL,
                payload jsonb, created_at timestamp DEFAULT now())""")
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS unresolved_references(
                id serial PRIMARY KEY, kind varchar NOT NULL,
                raw_value varchar, context varchar,
                created_at timestamp DEFAULT now())""")
        self.cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_unresolved
            ON unresolved_references(kind, raw_value, context)""")

    def ensure_mig_user(self):
        self.cur.execute("SELECT id FROM users WHERE username=%s", (MIG_USER,))
        row = self.cur.fetchone()
        if row:
            self.mig_user = row[0]
            return
        import uuid
        self.cur.execute("""
            INSERT INTO users(username, employee_id, email, first_name, last_name,
                department, status, is_super_admin, password,
                failed_login_attempts, is_locked, is_first_login,
                email_notifications_enabled, created_at, updated_at)
            VALUES(%s, %s, %s, %s, %s, 4, 1, false, 'NOT-A-REAL-PASSWORD',
                0, false, false, false, %s, %s) RETURNING id""",
            (MIG_USER, str(uuid.uuid4()), "migration@localhost",
             "Migration", "Bot", self.now, self.now))
        self.mig_user = self.cur.fetchone()[0]

    def load_caches(self):
        for tbl, key in (("accounts", "name"), ("work_stations", "name")):
            self.cur.execute(f"SELECT id, {key} FROM {tbl}")
            cache = self.accounts if tbl == "accounts" else self.stations
            for _id, name in self.cur.fetchall():
                cache[(name or "").strip().lower()] = _id
        self.cur.execute("SELECT id, job_number FROM business_jobs")
        for _id, jn in self.cur.fetchall():
            self.jobs[(jn or "").strip()] = _id
        self.cur.execute("SELECT id, job_id FROM fabs")
        for _id, job_id in self.cur.fetchall():
            self.fabs[_id] = job_id
        self.cur.execute("SELECT id, plan_name FROM planning_sections")
        for _id, name in self.cur.fetchall():
            self.plan_sections[(name or "").strip().upper()] = _id

    def reject(self, table, key, reason, payload=None):
        self.counts[table]["errored"] += 1
        if self.dry_run:
            if self.counts[table]["errored"] <= 5:
                print(f"REJECT {table} {key}: {reason}")
            return
        try:
            self.cur.execute(
                "INSERT INTO migration_rejects(source_table, source_key, reason, payload)"
                " SELECT %s,%s,%s,%s WHERE NOT EXISTS ("
                " SELECT 1 FROM migration_rejects"
                " WHERE source_table=%s AND source_key=%s AND reason=%s)",
                (table, str(key), reason,
                 json.dumps(payload or {}, default=str),
                 table, str(key), reason))
        except Exception:
            self.conn.rollback()

    def backlog(self, kind, raw, context):
        if not raw:
            return
        if self.dry_run:
            return
        self.cur.execute(
            "INSERT INTO unresolved_references(kind, raw_value, context)"
            " VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
            (kind, str(raw)[:255], str(context)[:255]))

    def upsert_by_key(self, entity, table, key_cols, data):
        """SELECT by natural key; UPDATE if present else INSERT. Returns id."""
        where = " AND ".join(f"{c}=%s" for c in key_cols)
        self.cur.execute(f"SELECT id FROM {table} WHERE {where}",
                         tuple(data[c] for c in key_cols))
        row = self.cur.fetchone()
        if row:
            _id = row[0]
            others = {k: v for k, v in data.items() if k not in key_cols}
            if others:
                sets = ", ".join(f"{c}=%s" for c in others)
                self.cur.execute(f"UPDATE {table} SET {sets} WHERE id=%s",
                                 tuple(others.values()) + (_id,))
            self.counts[entity]["updated"] += 1
            return _id
        cols = ", ".join(data)
        ph = ", ".join(["%s"] * len(data))
        self.cur.execute(
            f"INSERT INTO {table}({cols}) VALUES({ph}) RETURNING id",
            tuple(data.values()))
        self.counts[entity]["inserted"] += 1
        return self.cur.fetchone()[0]

    # -- reference resolvers --------------------------------------------
    def ref_upsert(self, table, name_col, name, extra=None):
        name = (name or "").strip()
        if not name:
            return None
        cache_attr = {"stone_types": "stone_types", "stone_colors": "stone_colors",
                      "stone_thickness": "stone_thickness", "edges": "edges"}.get(table)
        if not hasattr(self, cache_attr or "_none"):
            setattr(self, "_refcaches", getattr(self, "_refcaches", {}))
        caches = getattr(self, "_refcaches")
        cache = caches.setdefault(table, {})
        key = name.lower()
        if key in cache:
            return cache[key]
        self.cur.execute(f"SELECT id FROM {table} WHERE lower({name_col})=%s", (key,))
        row = self.cur.fetchone()
        if row:
            cache[key] = row[0]
            return row[0]
        data = {name_col: name, "status_id": ACTIVE, "created_by": self.mig_user,
                "created_at": self.now}
        data.update(extra or {})
        cols = ", ".join(data)
        self.cur.execute(f"INSERT INTO {table}({cols}) VALUES({', '.join(['%s']*len(data))}) RETURNING id",
                         tuple(data.values()))
        _id = self.cur.fetchone()[0]
        cache[key] = _id
        self.counts[table]["inserted"] += 1
        return _id

    def stone_type(self, v):
        return self.ref_upsert("stone_types", "name", v)

    def stone_color(self, v, type_id=None):
        extra = {"stone_type_id": type_id} if type_id else {}
        return self.ref_upsert("stone_colors", "name", v, extra)

    def stone_thickness(self, v):
        return self.ref_upsert("stone_thickness", "thickness", v,
                               {"thickness_mm": parse_thickness_mm(v)})

    def edge(self, v):
        return self.ref_upsert("edges", "name", v, {"edge_type": "Standard"})

    def fab_type(self, v):
        v = (v or "").strip()
        if not v:
            return "STANDARD"
        self.cur.execute("SELECT id FROM fab_type WHERE lower(name)=%s", (v.lower(),))
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO fab_type(name) VALUES(%s)", (v,))
            self.counts["fab_type"]["inserted"] += 1
        else:
            self.counts["fab_type"]["updated"] += 1
        return v

    def workstation(self, name, context=""):
        name = (name or "").strip()
        if not name:
            return None
        key = name.lower()
        if key in self.stations:
            return self.stations[key]
        self.cur.execute("SELECT id FROM work_stations WHERE lower(name)=%s", (key,))
        row = self.cur.fetchone()
        if row:
            self.stations[key] = row[0]
            return row[0]
        self.cur.execute(
            "INSERT INTO work_stations(name, is_active, status_id, created_at, created_by)"
            " VALUES(%s, true, %s, %s, %s) RETURNING id",
            (name, ACTIVE, self.now, self.mig_user))
        _id = self.cur.fetchone()[0]
        self.stations[key] = _id
        self.counts["work_stations"]["inserted"] += 1
        self.backlog("workstation", name, context)
        return _id

    def account(self, raw, job_number=""):
        name = (raw or "").strip()
        if not name:
            name = "UNASSIGNED"
            self.backlog("account", "(blank)", f"job {job_number}")
        key = name.lower()
        if key in self.accounts:
            return self.accounts[key]
        _id = self.upsert_by_key("accounts", "accounts", ["name"],
                                 {"name": name, "status_id": ACTIVE,
                                  "created_by": self.mig_user,
                                  "created_at": self.now})
        self.accounts[key] = _id
        return _id

    def person(self, raw_name, context):
        """Deferred employee linkage: always mig-user fallback + backlog, or None."""
        if raw_name and str(raw_name).strip():
            self.backlog("user", raw_name, context)
        return None


def read_csvs(input_dir):
    out = {}
    import glob as _glob
    for path in sorted(_glob.glob(f"{input_dir}/*.csv")):
        base = path.split("/")[-1].split("_2026")[0]
        with open(path, encoding="utf-8-sig") as fh:
            out[base] = list(csv.DictReader(fh))
    return out


WS_BY_ACTIVITY = {"CUT": "SAW 1", "WJ": "WATERJET", "MITER": "MITER 1"}
PLAN_BY_WS = {"CUT": "CUT", "EDGING": "EDGING", "MITER": "MITER",
              "CNC": "CNC", "QC": "HANDWORK", "WJ": "WJ",
              "RESURFACE": "RESURFACING", "POLISH": "HANDWORK"}


def resolve_station(ctx, activity, machine, context):
    for cand in (machine, WS_BY_ACTIVITY.get((activity or "").upper()), activity):
        if cand and str(cand).strip():
            if cand == machine:
                ctx.backlog("machine", cand, context)
            sid = ctx.workstation(str(cand).strip(), context)
            if sid:
                return sid
    return ctx.workstation("UNKNOWN", context)


def migrate(ctx, data):
    tables = data
    fab_rows = tables.get("Fab_Status", [])

    # ---- lookups -> work_stations / fab_type ---------------------------
    for prefix, col in (("Machines_CNC", "cnc_machine_name"),
                        ("Machines_Cut", "cut_machine_name"),
                        ("Machines_Edging", "edging_machine_name")):
        for r in tables.get(prefix, []):
            if r.get(col, "").strip():
                ctx.workstation(r[col].strip(), f"lookup {prefix}")
    for act, emp in ((r.get("Activity", ""), r.get("Employee", ""))
                     for r in tables.get("Default_Shop_Employees", [])):
        if act.strip():
            ctx.workstation(act.strip(), "default shop employee seed")
        if emp.strip():
            ctx.backlog("user", emp, f"default for {act}")
    for r in tables.get("Fab_Types", []):
        if r.get("fab_type", "").strip():
            ctx.fab_type(r["fab_type"])
    for emp_file, cols in (
            ("Active_Sales_Employees", ("sales_employee_name",)),
            ("Employees_Shop", ("Name",)),
            ("Employees_Template", ("template_employee_name",)),
            ("Alpha_Employees", ("FirstName", "LastName"))):
        for r in tables.get(emp_file, []):
            label = " ".join(r.get(c, "") for c in cols).strip()
            if label:
                ctx.backlog("user", label, f"employee file {emp_file} (deferred)")

    # ---- jobs + fabs ----------------------------------------------------
    jobs_agg = defaultdict(list)
    for r in fab_rows:
        jn = (r.get("job_number") or "").strip()
        if not jn:
            ctx.reject("Fab_Status", r.get("fab_id"), "missing job_number", r)
            continue
        jobs_agg[jn].append(r)

    for jn, rows in jobs_agg.items():
        first = rows[0]
        acct_id = ctx.account(first.get("account"), jn)
        sqft = sum(parse_float(r.get("total_sqft")) or 0 for r in rows)
        rev = sum(parse_float(r.get("revenue")) or 0 for r in rows)
        starts = [parse_dt(r.get("creation_date")) for r in rows]
        starts = [d for d in starts if d]
        name = next((r.get("job_name", "").strip() for r in rows
                     if r.get("job_name", "").strip()), f"JOB-{jn}")
        sales_raw = next((r.get("installer", "") for r in rows), "")
        ctx.person(sales_raw, f"job {jn} sales")
        job_id = ctx.upsert_by_key("business_jobs", "business_jobs", ["job_number"], {
            "job_number": jn, "name": name[:255], "account_id": acct_id,
            "description": first.get("areas", "").strip() or None,
            "sq_ft": sqft or None, "project_value": rev or None,
            "start_date": min(starts).date() if starts else None,
            "status_id": ACTIVE, "created_by": ctx.mig_user,
            "created_at": min(starts) if starts else ctx.now,
            "need_to_invoice": False})
        ctx.jobs[jn] = job_id

    STAGES = ["template", "draft", "slabsmith", "sct", "final", "shop", "install"]
    for r in fab_rows:
        try:
            fab_id = parse_int(r.get("fab_id"))
            if not fab_id:
                ctx.reject("Fab_Status", r.get("fab_id"), "bad fab_id", r)
                continue
            jn = (r.get("job_number") or "").strip()
            if jn not in ctx.jobs:
                ctx.reject("Fab_Status", r.get("fab_id"),
                           "no job (missing job_number)", r)
                continue
            total = parse_float(r.get("total_sqft"))
            if total is None:
                ctx.backlog("total_sqft", r.get("total_sqft"), f"fab {fab_id} -> 0")
                total = 0.0
            stone_t = ctx.stone_type(r.get("stone_type") or "UNKNOWN")
            stone_c = ctx.stone_color(r.get("stone_color") or "UNKNOWN", stone_t)
            stone_th = ctx.stone_thickness(r.get("stone_thickness") or "UNKNOWN")
            edge_id = ctx.edge(r.get("edge") or "UNKNOWN")
            for missing, val in (("stone_type", r.get("stone_type")),
                                 ("stone_color", r.get("stone_color")),
                                 ("stone_thickness", r.get("stone_thickness")),
                                 ("edge", r.get("edge"))):
                if not (val or "").strip():
                    ctx.backlog(missing, "(blank)", f"fab {fab_id}")
            complete = parse_bool(r.get("complete")) or False
            revised = bool(parse_bool(r.get("been_revised"))
                           or parse_bool(r.get("being_revised"))
                           or r.get("revision_completion_date", "").strip())
            created = parse_dt(r.get("creation_date")) or ctx.now
            ctx.person(r.get("installer"), f"fab {fab_id} sales_person")
            notes = {}
            for col in ("template_date_completed_2", "draft_date_completed_2",
                        "estimated_completion_date2", "first_est_completion_date",
                        "fab_percent", "install_date2"):
                if r.get(col, "").strip():
                    notes[col] = r[col].strip()
            for col in ("program_clock_complete", "draft_clock_complete",
                        "slabsmith_clock_complete"):
                if parse_bool(r.get(col)) is not None:
                    notes[col] = parse_bool(r.get(col))
            # current/next stage derivation
            done_flags = {
                "template": parse_bool(r.get("template_completed")),
                "draft": parse_bool(r.get("draft_completed")),
                "slabsmith": parse_bool(r.get("slabsmith_complete")),
                "sct": parse_bool(r.get("sct_completed")),
                "final": parse_bool(r.get("final_completed")),
                "shop": bool(r.get("cut_date_completed", "").strip()),
                "install": bool(r.get("completion_date", "").strip()
                                or r.get("install_date", "").strip())}
            if complete:
                cur_stage, nxt = "completed", None
            else:
                last = next((s for s in reversed(STAGES) if done_flags.get(s)), None)
                cur_stage = last or "template"
                nxt = STAGES[STAGES.index(cur_stage) + 1] if cur_stage in STAGES[:-1] else None
            fab_data = {
                "id": fab_id, "job_id": ctx.jobs[jn],
                "fab_type": ctx.fab_type(r.get("fab_type") or "STANDARD"),
                "sales_person_id": ctx.mig_user,
                "stone_type_id": stone_t, "stone_color_id": stone_c,
                "stone_thickness_id": stone_th, "edge_id": edge_id,
                "input_area": r.get("areas", "").strip() or None,
                "total_sqft": total, "notes": json.dumps(notes) if notes else None,
                "cost_of_stone": parse_float(r.get("cost_of_stone")),
                "redo_department": None, "cost_per_sqft": None,
                "redo_requested_by": None,
                "template_needed": needed(r.get("template_not_needed")),
                "drafting_needed": needed(r.get("draft_not_needed")),
                "slab_smith_cust_needed": needed(r.get("slabsmith_cust_not_needed")),
                "slab_smith_ag_needed": needed(r.get("slabsmith_ag_not_needed")),
                "sct_needed": needed(r.get("sct_not_needed")),
                "final_programming_needed": needed(r.get("final_not_needed")),
                "template_received": bool(parse_bool(r.get("template_completed"))
                                          or r.get("template_date_completed", "").strip()),
                "template_review_complete": bool(parse_bool(r.get("template_completed"))),
                "draft_completed": bool(parse_bool(r.get("draft_completed"))),
                "cad_review_complete": bool(parse_bool(r.get("draft_completed"))),
                "no_of_pieces": parse_int(r.get("number_pieces")),
                "revenue": parse_float(r.get("revenue")),
                "gp": parse_float(r.get("gp")),
                "sct_completed": bool(parse_bool(r.get("sct_completed"))),
                "revised": revised,
                "shop_date_schedule": parse_dt(r.get("shop_date_scheduled")),
                "final_programming_complete": bool(parse_bool(r.get("final_completed"))),
                "cutlist_complete": bool(parse_bool(r.get("complete"))),
                "final_programming_completed_date": parse_dt(r.get("final_date_completed")),
                "slab_smith_used": bool(parse_bool(r.get("slabsmith_complete"))
                                        or r.get("slabsmith_completion_date", "").strip()),
                "fp_not_needed": bool(parse_bool(r.get("final_not_needed"))),
                "wj_time_minutes": parse_int(r.get("wj_time")),
                "wj_linft": parse_float(r.get("wj_linft")),
                "edging_linft": parse_float(r.get("edging_linft")),
                "cnc_linft": parse_float(r.get("cnc_linft")),
                "miter_linft": parse_float(r.get("miter_linft")),
                "installation_date": parse_dt(r.get("completion_date"))
                                     or parse_dt(r.get("install_date")),
                "current_stage": cur_stage, "next_stage": nxt,
                "status_id": COMPLETED if complete else ACTIVE,
                "created_at": created, "created_by": ctx.mig_user,
                "slabsmith_completed_date": parse_dt(r.get("slabsmith_completion_date")),
                "sales_ct_completed_date": parse_dt(r.get("sct_date_completed")),
                "template_completed_date": parse_dt(r.get("template_date_completed")),
                "predraft_completed_date": (parse_dt(r.get("draft_date_completed"))
                    if parse_bool(r.get("pre_draft_review_completed")) else None),
                "draft_completed_date": parse_dt(r.get("draft_date_completed")),
                "revision_completed_date": parse_dt(r.get("revision_completion_date")),
                "sct_completed_date": parse_dt(r.get("sct_date_completed")),
                "shop_est_completion_date": parse_dt(r.get("shop_date_scheduled2"))
                    or parse_dt(r.get("estimated_completion_date")),
            }
            if (r.get("redo_dept", "").strip()):
                ctx.backlog("department", r["redo_dept"], f"fab {fab_id} redo")
            if (r.get("redo_person", "").strip()):
                ctx.backlog("user", r["redo_person"], f"fab {fab_id} redo")
            if (r.get("redo_cost", "").strip()):
                ctx.backlog("redo_cost", r["redo_cost"],
                            f"fab {fab_id} archived in revision notes")
            ctx.cur.execute("""
                INSERT INTO fabs(id, job_id, fab_type, sales_person_id, stone_type_id,
                    stone_color_id, stone_thickness_id, edge_id, input_area, total_sqft,
                    notes, cost_of_stone, redo_department, cost_per_sqft, redo_requested_by,
                    template_needed, drafting_needed, slab_smith_cust_needed,
                    slab_smith_ag_needed, sct_needed, final_programming_needed,
                    template_received, template_review_complete, draft_completed,
                    cad_review_complete, no_of_pieces, revenue, gp, sct_completed, revised,
                    shop_date_schedule, final_programming_complete, cutlist_complete,
                    final_programming_completed_date, slab_smith_used, fp_not_needed,
                    wj_time_minutes, wj_linft, edging_linft, cnc_linft, miter_linft,
                    installation_date, current_stage, next_stage, status_id, created_at,
                    created_by, slabsmith_completed_date, sales_ct_completed_date,
                    template_completed_date, predraft_completed_date, draft_completed_date,
                    revision_completed_date, sct_completed_date, shop_est_completion_date)
                VALUES(%(id)s, %(job_id)s, %(fab_type)s, %(sales_person_id)s,
                    %(stone_type_id)s, %(stone_color_id)s, %(stone_thickness_id)s,
                    %(edge_id)s, %(input_area)s, %(total_sqft)s,
                    %(notes)s::jsonb, %(cost_of_stone)s, %(redo_department)s,
                    %(cost_per_sqft)s, %(redo_requested_by)s,
                    %(template_needed)s, %(drafting_needed)s, %(slab_smith_cust_needed)s,
                    %(slab_smith_ag_needed)s, %(sct_needed)s, %(final_programming_needed)s,
                    %(template_received)s, %(template_review_complete)s, %(draft_completed)s,
                    %(cad_review_complete)s, %(no_of_pieces)s, %(revenue)s, %(gp)s,
                    %(sct_completed)s, %(revised)s, %(shop_date_schedule)s,
                    %(final_programming_complete)s, %(cutlist_complete)s,
                    %(final_programming_completed_date)s, %(slab_smith_used)s,
                    %(fp_not_needed)s, %(wj_time_minutes)s, %(wj_linft)s,
                    %(edging_linft)s, %(cnc_linft)s, %(miter_linft)s,
                    %(installation_date)s, %(current_stage)s, %(next_stage)s,
                    %(status_id)s, %(created_at)s, %(created_by)s,
                    %(slabsmith_completed_date)s, %(sales_ct_completed_date)s,
                    %(template_completed_date)s, %(predraft_completed_date)s,
                    %(draft_completed_date)s, %(revision_completed_date)s,
                    %(sct_completed_date)s, %(shop_est_completion_date)s)
                ON CONFLICT (id) DO UPDATE SET
                    job_id=EXCLUDED.job_id, total_sqft=EXCLUDED.total_sqft,
                    updated_at=%(now)s, updated_by=%(mig)s
                RETURNING (xmax = 0) AS was_inserted""",
                {**fab_data, "now": ctx.now, "mig": ctx.mig_user})
            was_inserted = ctx.cur.fetchone()[0]
            if was_inserted:
                ctx.counts["fabs"]["inserted"] += 1
            else:
                ctx.counts["fabs"]["updated"] += 1
            ctx.fabs[fab_id] = ctx.jobs[jn]
            if parse_int(r.get("number_pieces")) is None and r.get("number_pieces", "").strip():
                ctx.backlog("number_pieces", r["number_pieces"], f"fab {fab_id}")
            make_stage_rows(ctx, r, fab_id, created)
        except Exception as e:
            ctx.conn.rollback()
            ctx.reject("Fab_Status", r.get("fab_id"), f"{type(e).__name__}: {e}", r)


def one_per_fab(ctx, entity, table, fab_id, data, extra_keys=()):
    keys = ["fab_id"] + list(extra_keys)
    return ctx.upsert_by_key(entity, table, keys, {"fab_id": fab_id, **data})


def make_stage_rows(ctx, r, fab_id, created):
    M, now = ctx.mig_user, ctx.now
    sched = parse_dt(r.get("shop_date_scheduled")) or created
    # templatings / draftings / slab_smiths / sales_cts / final_programmings
    one_per_fab(ctx, "templatings", "templatings", fab_id, {
        "schedule_start_date": parse_dt(r.get("template_date_scheduled")) or created,
        "schedule_due_date": parse_dt(r.get("template_date_scheduled")) or created,
        "technician_id": M, "actual_start_date": None,
        "actual_end_date": parse_dt(r.get("template_date_completed")),
        "is_templating_schedule": True, "rescheduled": False,
        "is_completed": bool(parse_bool(r.get("template_completed"))),
        "status_id": ACTIVE, "created_at": created, "updated_at": now,
        "updated_by": M})
    ctx.person(r.get("template_by"), f"fab {fab_id} template_by")
    one_per_fab(ctx, "draftings", "draftings", fab_id, {
        "drafter_id": M, "scheduled_start_date": created,
        "scheduled_end_date": created,
        "drafter_end_date": parse_dt(r.get("draft_date_completed")),
        "status_id": ACTIVE, "created_at": created, "updated_at": now,
        "updated_by": M, "total_sqft_required_to_draft": r.get("total_sqft") or "0",
        "draft_note": r.get("draft_notes", "").strip() or None,
        "is_redrafting": False,
        "is_completed": bool(parse_bool(r.get("draft_completed")))})
    ctx.person(r.get("draft_by"), f"fab {fab_id} draft_by")
    if any((r.get(c, "").strip() for c in ("pre_draft_review", "pre_draft_review_2"))
           ) or parse_bool(r.get("pre_draft_review_completed")) is not None:
        one_per_fab(ctx, "pre_draft_reviews", "pre_draft_reviews", fab_id, {
            "draft_notes": " | ".join(x for x in
                (r.get("pre_draft_review", "").strip(),
                 r.get("pre_draft_review_2", "").strip()) if x) or "migrated",
            "is_redrafting_needed": 0,
            "is_completed": bool(parse_bool(r.get("pre_draft_review_completed"))),
            "created_at": created, "updated_by": M, "updated_at": now,
            "status_id": ACTIVE})
    one_per_fab(ctx, "slab_smiths", "slab_smiths", fab_id, {
        "slab_smith_type": "CUST", "drafter_id": M, "status_id": ACTIVE,
        "start_date": created,
        "end_date": parse_dt(r.get("slabsmith_completion_date")),
        "total_sqft_completed": r.get("total_sqft") or None,
        "is_completed": bool(parse_bool(r.get("slabsmith_complete"))),
        "slabsmith_completed_date": parse_dt(r.get("slabsmith_completion_date")),
        "created_at": created, "updated_at": now, "updated_by": M})
    one_per_fab(ctx, "sales_cts", "sales_cts", fab_id, {
        "is_revision_needed": False,
        "is_completed": bool(parse_bool(r.get("sct_completed"))),
        "status_id": ACTIVE, "created_at": created, "updated_at": now,
        "updated_by": M, "slab_smith_type": "SCT", "drafter_id": M,
        "start_date": created,
        "end_date": parse_dt(r.get("sct_date_completed")) or created})
    ctx.person(r.get("sct_by"), f"fab {fab_id} sct_by")
    one_per_fab(ctx, "final_programmings", "final_programmings", fab_id, {
        "drafter_id": M, "scheduled_start_date": created,
        "scheduled_end_date": created,
        "drafter_end_date": parse_dt(r.get("final_date_completed")),
        "is_completed": bool(parse_bool(r.get("final_completed"))),
        "status_id": ACTIVE, "created_at": created, "updated_at": now,
        "updated_by": M, "total_sqft_required_to_draft": r.get("total_sqft") or "0",
        "notes": json.dumps({"migrated_final_notes": r["final_notes"].strip()})
                 if r.get("final_notes", "").strip() else None})
    ctx.person(r.get("final_by"), f"fab {fab_id} final_by")
    # notes
    for col, stage in (("draft_notes", "draft"), ("slabsmith_notes", "slabsmith"),
                       ("sct_notes", "sct"), ("final_notes", "final_programming"),
                       ("pre_shop_review", "shop"), ("install_notes", "install")):
        txt = r.get(col, "").strip()
        if txt:
            ctx.cur.execute(
                "SELECT id FROM fab_notes WHERE fab_id=%s AND stage=%s AND note=%s",
                (fab_id, stage, txt))
            if not ctx.cur.fetchone():
                ctx.cur.execute(
                    "INSERT INTO fab_notes(fab_id, stage, note, created_by, created_at)"
                    " VALUES(%s,%s,%s,%s,%s)",
                    (fab_id, stage, txt, M, now))
                ctx.counts["fab_notes"]["inserted"] += 1
            else:
                ctx.counts["fab_notes"]["updated"] += 1
    if r.get("shop_notes", "").strip():
        txt = r["shop_notes"].strip()
        ctx.cur.execute(
            "SELECT id FROM shop_notes WHERE fab_id=%s AND note=%s", (fab_id, txt))
        if not ctx.cur.fetchone():
            ctx.cur.execute(
                "INSERT INTO shop_notes(fab_id, note, created_at, created_by)"
                " VALUES(%s,%s,%s,%s)", (fab_id, txt, now, M))
            ctx.counts["shop_notes"]["inserted"] += 1
        else:
            ctx.counts["shop_notes"]["updated"] += 1
    # cut_list / cost / shop_plannings
    one_per_fab(ctx, "cut_list", "cut_list", fab_id, {
        "is_final_progreamming_completed": bool(parse_bool(r.get("final_completed"))),
        "is_completed": bool(parse_bool(r.get("complete"))),
        "shop_schedule_date": parse_dt(r.get("cut_date_scheduled")),
        "status_id": ACTIVE, "created_at": created, "updated_at": now,
        "updated_by": M, "total_sqft": r.get("cut_sqft") or r.get("total_sqft"),
        "installation_date": parse_dt(r.get("install_date"))})
    ctx.person(r.get("cut_by"), f"fab {fab_id} cut_by")
    if (r.get("cost_of_stone", "").strip() or
            parse_bool(r.get("cost_entered")) is not None):
        one_per_fab(ctx, "cost_of_stones", "cost_of_stones", fab_id, {
            "total_sqft": r.get("total_sqft"),
            "total_cost": r.get("cost_of_stone"),
            "is_completed": bool(parse_bool(r.get("cost_entered"))),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M})
    one_per_fab(ctx, "shop_plannings", "shop_plannings", fab_id, {
        "start_date": sched, "no_of_steps_needed": 5, "status_id": ACTIVE,
        "completed_steps": (5 if parse_bool(r.get("pre_shop_review_completed")) else 0),
        "current_steps": 0, "created_at": created, "created_by": M,
        "updated_at": now, "updated_by": M})
    # shop_cut_plans per workstation with data
    ws_groups = [
        ("CUT", ("cut_date_scheduled", "cut_hours_scheduled", "cut_percent",
                 "cut_date_completed", "cut_by", "cut_machine_scheduled",
                 "cut_employee_scheduled")),
        ("EDGING", ("edging_date_scheduled", "edging_hours_scheduled", "edging_percent",
                    "edging_date_completed", "edging_by", "edging_machine_scheduled",
                    "edging_employee_scheduled")),
        ("MITER", ("miter_date_scheduled", "miter_hours_scheduled", "miter_percent",
                   "miter_date_completed", "miter_by", "miter_machine_scheduled",
                   "miter_employee_scheduled")),
        ("CNC", ("cnc_date_scheduled", "cnc_hours_scheduled", "cnc_percent",
                 "cnc_date_completed", "cnc_by", "cnc_machine_scheduled",
                 "cnc_employee_scheduled")),
        ("QC", ("qc_date_scheduled", "qc_hours_scheduled", "qc_percent",
                "qc_date_completed", "qc_by", "qc_machine_scheduled",
                "qc_employee_scheduled"))]
    seq = {"CUT": 1, "EDGING": 2, "MITER": 3, "CNC": 4, "QC": 5}
    for ws, cols in ws_groups:
        vals = [r.get(c, "").strip() for c in cols]
        if not any(vals):
            continue
        sched_s, hours, pct, done_d, by, mach, emp = vals
        pct_i = parse_int(pct)
        ws_id = resolve_station(ctx, ws, mach, f"fab {fab_id} {ws}")
        plan_id = ctx.plan_sections.get(PLAN_BY_WS[ws], 7)
        for person in (by, emp):
            ctx.person(person, f"fab {fab_id} {ws}")
        ctx.cur.execute(
            "SELECT id FROM shop_cut_plans WHERE fab_id=%s AND workstation_id=%s",
            (fab_id, ws_id))
        row = ctx.cur.fetchone()
        payload = {"fab_id": fab_id, "workstation_id": ws_id,
                   "planning_section_id": plan_id, "user_id": M,
                   "sequence": seq[ws],
                   "estimated_hours": parse_float(hours) or 0,
                   "scheduled_start_date": parse_dt(sched_s),
                   "scheduled_end_date": parse_dt(sched_s),
                   "actual_start_date": parse_dt(sched_s),
                   "actual_end_date": parse_dt(done_d),
                   "work_percentage": max(0, min(100, pct_i)) if pct_i is not None else 0,
                   "notes": f"migrated {ws} by={by} emp={emp}".strip(),
                   "created_at": created, "created_by": M,
                   "updated_at": now, "updated_by": M}
        if row:
            sets = ", ".join(f"{c}=%s" for c in payload if c != "fab_id")
            ctx.cur.execute(f"UPDATE shop_cut_plans SET {sets} WHERE id=%s",
                            tuple(v for k, v in payload.items() if k != "fab_id")
                            + (row[0],))
            ctx.counts["shop_cut_plans"]["updated"] += 1
        else:
            cols_s = ", ".join(payload)
            ctx.cur.execute(
                f"INSERT INTO shop_cut_plans({cols_s}) VALUES({', '.join(['%s']*len(payload))})",
                tuple(payload.values()))
            ctx.counts["shop_cut_plans"]["inserted"] += 1
    # WJ
    if any((r.get(c, "").strip() for c in ("wj_time", "wj_linft", "wj_date_scheduled",
                                           "wj_percent", "wj_date_completed"))):
        done_d = parse_dt(r.get("wj_date_completed"))
        one_per_fab(ctx, "wj_schedulings", "wj_schedulings", fab_id, {
            "technician_id": None,
            "scheduled_start_date": parse_dt(r.get("wj_date_scheduled")),
            "scheduled_end_date": parse_dt(r.get("wj_date_scheduled")),
            "actual_start_date": parse_dt(r.get("wj_date_scheduled")),
            "actual_end_date": done_d, "total_ln_ft": r.get("wj_linft"),
            "completed_ln_ft": None,
            "is_completed": bool(done_d),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M,
            "notes": json.dumps({"wj_percent": r["wj_percent"]})
                     if r.get("wj_percent", "").strip() else None})
        one_per_fab(ctx, "wj_programmings", "wj_programmings", fab_id, {
            "drafter_id": M, "scheduled_start_date": created,
            "scheduled_end_date": created,
            "is_completed": bool(done_d),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M,
            "total_ln_ft": r.get("wj_linft")})
        for person in (r.get("wj_by"), r.get("wj_employee_scheduled")):
            ctx.person(person, f"fab {fab_id} wj")
    # resurface
    if any((r.get(c, "").strip() for c in ("resurface_sqft", "resurface_percent",
                                           "resurface_date_completed"))):
        done_d = parse_dt(r.get("resurface_date_completed"))
        one_per_fab(ctx, "resurface_schedulings", "resurface_schedulings", fab_id, {
            "technician_id": None,
            "scheduled_start_date": sched, "scheduled_end_date": sched,
            "actual_start_date": sched, "actual_end_date": done_d,
            "total_sqft": r.get("resurface_sqft"),
            "completed_sqft": r.get("resurface_sqft") if done_d else None,
            "is_completed": bool(done_d),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M,
            "notes": json.dumps({"resurface_percent": r["resurface_percent"]})
                     if r.get("resurface_percent", "").strip() else None})
        ctx.person(r.get("resurface_by"), f"fab {fab_id} resurface")
    # install
    if any((r.get(c, "").strip() for c in ("install_date", "install_date2",
                                           "installer", "install_confirmed",
                                           "completion_date"))):
        inst_d = parse_dt(r.get("install_date")) or parse_dt(r.get("completion_date"))
        comp_d = parse_dt(r.get("completion_date")) or inst_d or now
        one_per_fab(ctx, "install_schedulings", "install_schedulings", fab_id, {
            "installer_id": None,
            "scheduled_install_date": inst_d, "scheduled_end_date": inst_d,
            "actual_install_date": comp_d,
            "total_sqft": r.get("total_sqft"),
            "is_completed": bool(comp_d and parse_bool(r.get("complete"))),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M,
            "notes": json.dumps({"migrated_install_notes":
                                  r["install_notes"].strip()})
                 if r.get("install_notes", "").strip() else None})
        one_per_fab(ctx, "install_completions", "install_completions", fab_id, {
            "installer_id": M, "install_date": inst_d or created,
            "completion_date": comp_d,
            "is_completed": bool(parse_bool(r.get("complete"))),
            "is_confirmed": bool(parse_bool(r.get("install_confirmed"))),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M})
        ctx.person(r.get("installer"), f"fab {fab_id} installer")
    # redo -> revisions
    if any((r.get(c, "").strip() for c in ("redo_reason", "redo_dept",
                                           "redo_person", "redo_cost"))
           ) or parse_bool(r.get("being_revised")):
        notes = " | ".join(x for x in (
            f"REDO COST={r['redo_cost'].strip()}" if r.get("redo_cost", "").strip() else "",
            r.get("redo_reason", "").strip()) if x)
        one_per_fab(ctx, "revisions", "revisions", fab_id, {
            "revision_type": "SHOP", "requested_by": M, "assigned_to": None,
            "revision_reason": r.get("redo_reason", "").strip() or None,
            "revision_notes": notes or None,
            "department": r.get("redo_dept", "").strip() or None,
            "person_name": r.get("redo_person", "").strip() or None,
            "is_completed": bool(parse_dt(r.get("revision_completion_date"))
                                 and not parse_bool(r.get("being_revised"))),
            "actual_end_date": parse_dt(r.get("revision_completion_date")),
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M})


def migrate_history(ctx, data):
    M, now = ctx.mig_user, ctx.now
    # Draft_Data
    for i, s in enumerate(data.get("Draft_Data", [])):
        fab_id = parse_int(s.get("fab_id"))
        if not fab_id or fab_id not in ctx.fabs:
            ctx.reject("Draft_Data", s.get("fab_id"), "orphan fab_id", s)
            continue
        start = (parse_dt(s.get("session_start_time")) or parse_dt(s.get("new_start_time"))
                 or parse_dt(s.get("start_time")))
        if not start:
            ctx.reject("Draft_Data", s.get("fab_id"), "no start_time", s)
            continue
        end = parse_dt(s.get("new_end_time")) or parse_dt(s.get("end_time")) \
            or parse_dt(s.get("display_end_time"))
        dur = parse_duration_sec(s.get("session_duration")) \
            or parse_duration_sec(s.get("draft_duration"))
        if start and end and dur is None:
            dur = int((end - start).total_seconds())
        active = parse_bool(s.get("active_session"))
        status = ("IN_PROGRESS" if active else
                  ("COMPLETED" if end else "IN_PROGRESS"))
        ctx.cur.execute(
            "SELECT id FROM drafting_sessions WHERE fab_id=%s AND session_start_time=%s",
            (fab_id, start))
        row = ctx.cur.fetchone()
        payload = {"fab_id": fab_id, "drafter_id": M, "status": status,
                   "session_start_time": start, "session_end_time": end,
                   "total_pause_duration": 0, "total_time_spent": dur or 0,
                   "work_percentage_done": 100 if end else 0,
                   "created_at": now, "updated_at": now}
        if row:
            sid = row[0]
            ctx.cur.execute(
                "UPDATE drafting_sessions SET status=%s, session_end_time=%s,"
                " total_time_spent=%s, updated_at=%s WHERE id=%s",
                (status, end, dur or 0, now, sid))
            ctx.counts["drafting_sessions"]["updated"] += 1
        else:
            ctx.cur.execute(
                "INSERT INTO drafting_sessions(fab_id, drafter_id, status,"
                " session_start_time, session_end_time, total_pause_duration,"
                " total_time_spent, work_percentage_done, created_at, updated_at)"
                " VALUES(%s,%s,%s,%s,%s,0,%s,%s,%s,%s) RETURNING id",
                (fab_id, M, status, start, end, dur or 0,
                 100 if end else 0, now, now))
            sid = ctx.cur.fetchone()[0]
            ctx.counts["drafting_sessions"]["inserted"] += 1
        ctx.person(s.get("drafter"), f"draft session fab {fab_id}")
        for col, act in (("old_duration", "DURATION_ADJUST"), ("new_duration", "DURATION_ADJUST"),
                         ("session_start_temp", "SESSION_TEMP"),
                         ("intermediary", "INTERMEDIARY"), ("test", "DEBUG")):
            if s.get(col, "").strip():
                note = f"{act}: {s[col].strip()}"
                ctx.cur.execute(
                    "SELECT id FROM drafting_session_notes WHERE session_id=%s AND note=%s",
                    (sid, note))
                if not ctx.cur.fetchone():
                    ctx.cur.execute(
                        "INSERT INTO drafting_session_notes(session_id, fab_id, action,"
                        " timestamp, note, created_at) VALUES(%s,%s,%s,%s,%s,%s)",
                        (sid, fab_id, act, start, note, now))
                    ctx.counts["drafting_session_notes"]["inserted"] += 1
    # FP_Data
    for s in data.get("FP_Data", []):
        fab_id = parse_int(s.get("fab_id"))
        if not fab_id or fab_id not in ctx.fabs:
            ctx.reject("FP_Data", s.get("fab_id"), "orphan fab_id", s)
            continue
        start = (parse_dt(s.get("session_start_time")) or parse_dt(s.get("new_start_time"))
                 or parse_dt(s.get("start_time")))
        if not start:
            ctx.reject("FP_Data", s.get("fab_id"), "no start_time", s)
            continue
        end = parse_dt(s.get("new_end_time")) or parse_dt(s.get("end_time")) \
            or parse_dt(s.get("display_end_date"))
        dur = parse_duration_sec(s.get("session_duration")) \
            or parse_duration_sec(s.get("programming_duration"))
        if start and end and dur is None:
            dur = int((end - start).total_seconds())
        active = parse_bool(s.get("active_session"))
        status = "IN_PROGRESS" if (active or not end) else "COMPLETED"
        ctx.cur.execute(
            "SELECT id FROM final_programming_sessions WHERE fab_id=%s AND session_start_time=%s",
            (fab_id, start))
        row = ctx.cur.fetchone()
        if row:
            sid = row[0]
            ctx.cur.execute(
                "UPDATE final_programming_sessions SET status=%s, session_end_time=%s,"
                " total_time_spent=%s, updated_at=%s WHERE id=%s",
                (status, end, dur or 0, now, sid))
            ctx.counts["final_programming_sessions"]["updated"] += 1
        else:
            ctx.cur.execute(
                "INSERT INTO final_programming_sessions(fab_id, user_id, status,"
                " session_start_time, session_end_time, total_pause_duration,"
                " total_time_spent, created_at, updated_at)"
                " VALUES(%s,%s,%s,%s,%s,0,%s,%s,%s) RETURNING id",
                (fab_id, M, status, start, end, dur or 0, now, now))
            sid = ctx.cur.fetchone()[0]
            ctx.counts["final_programming_sessions"]["inserted"] += 1
        ctx.person(s.get("programmer"), f"fp session fab {fab_id}")
        for col in ("old_duration", "session_start_temp", "intermediary"):
            if s.get(col, "").strip():
                note = f"{col}: {s[col].strip()}"
                ctx.cur.execute(
                    "SELECT id FROM final_programming_session_notes"
                    " WHERE session_id=%s AND note=%s", (sid, note))
                if not ctx.cur.fetchone():
                    ctx.cur.execute(
                        "INSERT INTO final_programming_session_notes(session_id, fab_id,"
                        " user_id, action, timestamp, note, created_at)"
                        " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                        (sid, fab_id, M, "MIGRATED", start, note, now))
                    ctx.counts["final_programming_session_notes"]["inserted"] += 1
    # Shop_Data
    for s in data.get("Shop_Data", []):
        fab_id = parse_int(s.get("fab_id"))
        if not fab_id or fab_id not in ctx.fabs:
            ctx.reject("Shop_Data", s.get("fab_id"), "orphan fab_id", s)
            continue
        start = parse_dt(s.get("start_time"))
        if not start:
            ctx.reject("Shop_Data", s.get("fab_id"), "no start_time", s)
            continue
        stop = parse_dt(s.get("stop_time"))
        dur = parse_duration_sec(s.get("duration"))
        if start and stop and dur is None:
            dur = int((stop - start).total_seconds())
        activity = (s.get("activity") or "").strip().upper()
        ws_id = resolve_station(ctx, activity, s.get("cut_machine") or s.get("edging_machine"),
                                f"shop session fab {fab_id}")
        if s.get("cut_machine", "").strip():
            ctx.backlog("machine", s["cut_machine"], f"shop session fab {fab_id}")
        if s.get("edging_machine", "").strip():
            ctx.backlog("machine", s["edging_machine"], f"shop session fab {fab_id}")
        ctx.person(s.get("shop_employee"), f"shop session fab {fab_id}")
        job_id = ctx.fabs[fab_id]
        status = "IN_PROGRESS" if not stop else "COMPLETED"
        ctx.cur.execute(
            "SELECT id FROM operator_job_timer_sessions"
            " WHERE fab_id=%s AND session_start_at=%s", (fab_id, start))
        row = ctx.cur.fetchone()
        if row:
            sid = row[0]
            ctx.cur.execute(
                "UPDATE operator_job_timer_sessions SET stopped_at=%s, total_work_seconds=%s,"
                " status=%s, updated_at=%s WHERE id=%s",
                (stop, dur or 0, status, now, sid))
            ctx.counts["operator_job_timer_sessions"]["updated"] += 1
        else:
            ctx.cur.execute(
                "INSERT INTO operator_job_timer_sessions(job_id, fab_id, operator_id,"
                " workstation_id, status, session_start_at, stopped_at,"
                " total_work_seconds, total_pause_seconds, created_at, created_by,"
                " updated_at, updated_by)"
                " VALUES(%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s) RETURNING id",
                (job_id, fab_id, M, ws_id, status, start, stop, dur or 0,
                 now, M, now, M))
            sid = ctx.cur.fetchone()[0]
            ctx.counts["operator_job_timer_sessions"]["inserted"] += 1
        note = " | ".join(x for x in (
            f"activity={s.get('activity','').strip()}",
            f"measure={s['measure'].strip()} {s['units'].strip()}" if s.get("measure","").strip() else "",
            f"percent={s['percent_complete'].strip()}" if s.get("percent_complete","").strip() else "") if x)
        ctx.cur.execute(
            "SELECT id FROM operator_job_timer_events WHERE session_id=%s AND action=%s AND event_at=%s",
            (sid, "MIGRATED", start))
        if not ctx.cur.fetchone():
            ctx.cur.execute(
                "INSERT INTO operator_job_timer_events(session_id, job_id, fab_id,"
                " operator_id, action, event_at, note)"
                " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (sid, job_id, fab_id, M, "MIGRATED", start, note or None))
            ctx.counts["operator_job_timer_events"]["inserted"] += 1
        pct_i = parse_int(s.get("percent_complete"))
        if pct_i is not None and ws_id:
            ctx.cur.execute(
                "UPDATE shop_cut_plans SET work_percentage=%s, updated_at=%s"
                " WHERE fab_id=%s AND workstation_id=%s",
                (max(0, min(100, pct_i)), now, fab_id, ws_id))
    # revision_info
    for rev in data.get("revision_info", []):
        fab_id = parse_int(rev.get("FabID"))
        if not fab_id or fab_id not in ctx.fabs:
            ctx.reject("revision_info", rev.get("FabID"), "orphan fab_id", rev)
            continue
        rtype = (rev.get("RevisionType") or "SHOP").strip().upper()
        if rtype not in ("SHOP", "DRAFT", "SCT", "FINAL"):
            rtype = "SHOP"
        created = parse_dt(rev.get("creation_date")) or now
        done_d = parse_dt(rev.get("revision_date_completed"))
        ctx.person(rev.get("SalesPerson"), f"revision fab {fab_id} sales")
        ctx.person(rev.get("Revisor"), f"revision fab {fab_id} revisor")
        one_per_fab(ctx, "revisions", "revisions", fab_id, {
            "revision_type": rtype, "requested_by": M, "assigned_to": None,
            "revision_reason": rev.get("RevisionReason", "").strip() or None,
            "revision_notes": rev.get("DraftNotes", "").strip() or None,
            "is_completed": bool(done_d),
            "scheduled_start_date": created, "scheduled_end_date": created,
            "actual_start_date": created, "actual_end_date": done_d,
            "status_id": ACTIVE, "created_at": created,
            "updated_at": now, "updated_by": M},
            extra_keys=("revision_type",))
        if rev.get("FileData", "").strip():
            ctx.cur.execute(
                "SELECT id FROM files WHERE fab_id=%s AND file_path=%s",
                (fab_id, rev["FileData"].strip()))
            if not ctx.cur.fetchone():
                ctx.cur.execute(
                    "INSERT INTO files(name, file_path, file_type, created_at, updated_at,"
                    " file_size, fab_id, job_id, stage)"
                    " VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (rev["FileData"].strip()[:255], rev["FileData"].strip(),
                     "migration", now, now, "0", fab_id, ctx.fabs[fab_id], "revision"))
                ctx.counts["files"]["inserted"] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--db", default="odyssey_migration_test")
    ap.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL URL; defaults to DATABASE_URL when set",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.database_url:
        database_url = args.database_url
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
        if os.path.exists("/.dockerenv"):
            database_url = database_url.replace("@localhost:", "@host.docker.internal:", 1)
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(dbname=args.db)
    conn.autocommit = False
    ctx = Ctx(conn, dry_run=args.dry_run)
    ctx.ensure_helper_tables()
    ctx.ensure_mig_user()
    ctx.load_caches()
    data = read_csvs(args.input)

    migrate(ctx, data)
    migrate_history(ctx, data)

    if args.dry_run:
        conn.rollback()
        print("DRY RUN - no writes committed")
    else:
        conn.commit()
        for seq, tbl, col in (("fabs_id_seq", "fabs", "id"),
                              ("business_jobs_id_seq", "business_jobs", "id"),
                              ("accounts_id_seq", "accounts", "id")):
            ctx.cur.execute(
                f"SELECT setval('{seq}', COALESCE((SELECT max({col}) FROM {tbl}), 1))")
        conn.commit()
    print("\n=== RECONCILIATION ===")
    total_i = total_u = total_e = 0
    for entity in sorted(ctx.counts):
        ops = ctx.counts[entity]
        i, u, e = ops.get("inserted", 0), ops.get("updated", 0), ops.get("errored", 0)
        total_i += i
        total_u += u
        total_e += e
        print(f"{entity:38s} inserted={i:4d} updated={u:4d} errored={e:4d}")
    print(f"{'TOTAL':38s} inserted={total_i:4d} updated={total_u:4d} errored={total_e:4d}")
    if not args.dry_run:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM migration_rejects")
        print(f"migration_rejects rows: {cur.fetchone()[0]}")
        cur.execute("SELECT kind, count(*) FROM unresolved_references GROUP BY 1 ORDER BY 2 DESC")
        print("unresolved_references:")
        for kind, n in cur.fetchall():
            print(f"  {kind:20s} {n}")
        print("\n=== TARGET COUNTS ===")
        for t in ("accounts", "business_jobs", "fabs", "templatings", "draftings",
                  "slab_smiths", "sales_cts", "final_programmings", "shop_cut_plans",
                  "revisions", "fab_notes", "shop_notes", "drafting_sessions",
                  "final_programming_sessions", "operator_job_timer_sessions"):
            cur.execute(f"SELECT count(*) FROM {t}")
            print(f"{t:38s} {cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
