#!/usr/bin/env python3
"""
Test/execute Caspio XML migration for three legacy tables:
- Fab_Status
- revision_info
- Shop_Data

Default mode is DRY RUN (no DB writes committed).
Use --apply to execute actual writes.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# Make script runnable from either project root or scripts/ directory.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from src.app.utils.config import SessionLocal


def as_bool(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "t"}


def as_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def as_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(str(value).strip())
    except Exception:
        return default


def as_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def stable_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def row_to_dict(row_elem: ET.Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    if row_elem.attrib:
        out.update(row_elem.attrib)

    for child in list(row_elem):
        if len(list(child)) == 0:
            tag = child.tag.split("}")[-1]
            out[tag] = (child.text or "").strip()

    return out


def extract_table_rows(xml_path: str) -> Dict[str, List[Dict[str, Any]]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for table in root.findall(".//Table"):
        name_elem = table.find("Name")
        if name_elem is None:
            continue
        table_name = (name_elem.text or "").strip()
        if not table_name:
            continue

        candidates = []
        candidates.extend(table.findall("./Data/Row"))
        candidates.extend(table.findall("./Rows/Row"))
        candidates.extend(table.findall(".//Record"))
        candidates.extend(table.findall(".//Row"))

        for row in candidates:
            if str(row.attrib.get("NoData", "")).lower() == "true":
                continue

            d = row_to_dict(row)
            if not d:
                continue

            # Skip schema-only row blocks.
            if len(list(row)) > 0:
                schema_like = all(
                    ("DataType" in c.attrib or "DisplayOrder" in c.attrib)
                    for c in list(row)
                )
                if schema_like:
                    continue

            result[table_name].append(d)

    return result


async def ensure_key_map_table(db) -> None:
    await db.execute(text("""
    CREATE TABLE IF NOT EXISTS migration_key_map (
      id BIGSERIAL PRIMARY KEY,
      run_id UUID NOT NULL,
      source_system VARCHAR(50) NOT NULL DEFAULT 'CASPIO',
      source_table VARCHAR(128) NOT NULL,
      source_pk TEXT NOT NULL,
      source_natural_key VARCHAR(512),
      target_table VARCHAR(128) NOT NULL,
      target_pk BIGINT,
      target_uuid UUID,
      match_method VARCHAR(50) NOT NULL,
      mapping_status VARCHAR(20) NOT NULL DEFAULT 'mapped',
      field_hash VARCHAR(128),
      attempt_count INT NOT NULL DEFAULT 1,
      last_error TEXT,
      mapped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_migration_key_map UNIQUE (source_system, source_table, source_pk, target_table)
    );
    """))

    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_migration_key_map_run_id ON migration_key_map (run_id);"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_migration_key_map_source ON migration_key_map (source_table, source_pk);"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_migration_key_map_target ON migration_key_map (target_table, target_pk);"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_migration_key_map_status ON migration_key_map (mapping_status);"))


async def upsert_key_map(
    db,
    run_id: uuid.UUID,
    source_table: str,
    source_pk: str,
    source_natural_key: Optional[str],
    target_table: str,
    target_pk: Optional[int],
    match_method: str,
    mapping_status: str,
    field_hash: Optional[str],
    last_error: Optional[str] = None,
) -> None:
    await db.execute(text("""
    INSERT INTO migration_key_map (
      run_id, source_system, source_table, source_pk, source_natural_key,
      target_table, target_pk, match_method, mapping_status, field_hash, last_error
    )
    VALUES (
      :run_id, 'CASPIO', :source_table, :source_pk, :source_natural_key,
      :target_table, :target_pk, :match_method, :mapping_status, :field_hash, :last_error
    )
    ON CONFLICT (source_system, source_table, source_pk, target_table)
    DO UPDATE SET
      run_id = EXCLUDED.run_id,
      source_natural_key = EXCLUDED.source_natural_key,
      target_pk = EXCLUDED.target_pk,
      match_method = EXCLUDED.match_method,
      mapping_status = EXCLUDED.mapping_status,
      field_hash = EXCLUDED.field_hash,
      last_error = EXCLUDED.last_error,
      attempt_count = migration_key_map.attempt_count + 1,
      mapped_at = NOW(),
      updated_at = NOW();
    """), {
        "run_id": str(run_id),
        "source_table": source_table,
        "source_pk": source_pk,
        "source_natural_key": source_natural_key,
        "target_table": target_table,
        "target_pk": target_pk,
        "match_method": match_method,
        "mapping_status": mapping_status,
        "field_hash": field_hash,
        "last_error": last_error,
    })


async def _exists(db, query: str, params: Dict[str, Any]) -> bool:
    rs = await db.execute(text(query), params)
    return rs.first() is not None


async def _table_exists(db, table_name: str) -> bool:
    rs = await db.execute(
        text("SELECT to_regclass(:table_name)"),
        {"table_name": table_name},
    )
    return rs.scalar_one_or_none() is not None


async def run_preflight_checks(db, cfg: Dict[str, int]) -> List[str]:
    errors: List[str] = []

    required_tables = [
        "users",
        "status",
        "stone_types",
        "stone_colors",
        "stone_thickness",
        "edges",
        "work_stations",
        "planning_sections",
    ]

    missing_tables: List[str] = []
    for table_name in required_tables:
        if not await _table_exists(db, table_name):
            missing_tables.append(table_name)

    if missing_tables:
        errors.append(
            "Database schema is incomplete. Missing table(s): "
            + ", ".join(missing_tables)
        )
        errors.append(
            "Run schema setup/migrations first (e.g., scripts/auto_migrate.py or your deployment migration step), "
            "and verify DATABASE_URL points to the intended app database."
        )
        return errors

    if not await _exists(db, "SELECT 1 FROM users WHERE id=:id", {"id": cfg["user_id"]}):
        errors.append(f"default-user-id {cfg['user_id']} not found in users")

    if not await _exists(db, "SELECT 1 FROM status WHERE value_id=:id", {"id": cfg["status_id"]}):
        errors.append(f"default-status-id {cfg['status_id']} not found in status.value_id")

    if not await _exists(db, "SELECT 1 FROM stone_types WHERE id=:id", {"id": cfg["stone_type_id"]}):
        errors.append(f"default-stone-type-id {cfg['stone_type_id']} not found in stone_types")

    if not await _exists(db, "SELECT 1 FROM stone_colors WHERE id=:id", {"id": cfg["stone_color_id"]}):
        errors.append(f"default-stone-color-id {cfg['stone_color_id']} not found in stone_colors")

    if not await _exists(db, "SELECT 1 FROM stone_thickness WHERE id=:id", {"id": cfg["stone_thickness_id"]}):
        errors.append(f"default-stone-thickness-id {cfg['stone_thickness_id']} not found in stone_thickness")

    if not await _exists(db, "SELECT 1 FROM edges WHERE id=:id", {"id": cfg["edge_id"]}):
        errors.append(f"default-edge-id {cfg['edge_id']} not found in edges")

    if not await _exists(db, "SELECT 1 FROM work_stations WHERE id=:id", {"id": cfg["workstation_id"]}):
        errors.append(f"default-workstation-id {cfg['workstation_id']} not found in work_stations")

    if not await _exists(db, "SELECT 1 FROM planning_sections WHERE id=:id", {"id": cfg["planning_section_id"]}):
        errors.append(f"default-planning-section-id {cfg['planning_section_id']} not found in planning_sections")

    return errors


async def get_or_create_account(db, account_name: str, status_id: int, user_id: int, dry_run: bool) -> Optional[int]:
    if not account_name:
        return None

    rs = await db.execute(text("SELECT id FROM accounts WHERE lower(name)=lower(:name)"), {"name": account_name})
    row = rs.first()
    if row:
        return row[0]

    if dry_run:
        return None

    rs = await db.execute(text("""
    INSERT INTO accounts (name, status_id, created_by, created_at)
    VALUES (:name, :status_id, :created_by, NOW())
    RETURNING id
    """), {
        "name": account_name,
        "status_id": status_id,
        "created_by": user_id,
    })
    return rs.scalar_one()


async def get_or_create_business_job(
    db,
    job_number: str,
    job_name: str,
    account_id: Optional[int],
    status_id: int,
    user_id: int,
    sq_ft: Optional[float],
    dry_run: bool,
) -> Optional[int]:
    if not job_number:
        return None

    rs = await db.execute(text("SELECT id FROM business_jobs WHERE job_number=:job_number"), {"job_number": job_number})
    row = rs.first()
    if row:
        return row[0]

    if dry_run:
        return None

    rs = await db.execute(text("""
    INSERT INTO business_jobs (
      name, job_number, account_id, status_id, created_by, created_at, sq_ft, need_to_invoice
    ) VALUES (
      :name, :job_number, :account_id, :status_id, :created_by, NOW(), :sq_ft, false
    )
    RETURNING id
    """), {
        "name": (job_name or f"Job {job_number}")[:255],
        "job_number": str(job_number),
        "account_id": account_id,
        "status_id": status_id,
        "created_by": user_id,
        "sq_ft": sq_ft,
    })
    return rs.scalar_one()


async def migrate_fab_status(db, run_id, rows, cfg, dry_run, stats):
    for row in rows:
        source_fab_id = str(row.get("fab_id") or "").strip()
        if not source_fab_id:
            stats["fab_status_skipped_missing_fab_id"] += 1
            continue

        account_name = (row.get("account") or "").strip()
        job_number = str(row.get("job_number") or "").strip()
        job_name = (row.get("job_name") or "").strip()
        total_sqft = as_float(row.get("total_sqft"), 0.0)

        account_id = await get_or_create_account(db, account_name, cfg["status_id"], cfg["user_id"], dry_run)
        job_id = await get_or_create_business_job(
            db,
            job_number,
            job_name,
            account_id,
            cfg["status_id"],
            cfg["user_id"],
            total_sqft,
            dry_run,
        )

        existing_map = await db.execute(text("""
            SELECT target_pk FROM migration_key_map
            WHERE source_system='CASPIO'
              AND source_table='Fab_Status'
              AND source_pk=:source_pk
              AND target_table='fabs'
        """), {"source_pk": source_fab_id})

        if existing_map.first():
            stats["fab_status_already_mapped"] += 1
            continue

        payload = {
            "source_fab_id": source_fab_id,
            "job_number": job_number,
            "account": account_name,
            "fab_type": row.get("fab_type"),
        }

        if dry_run:
            await upsert_key_map(
                db,
                run_id,
                "Fab_Status",
                source_fab_id,
                f"job={job_number}|account={account_name}",
                "fabs",
                None,
                "direct_pk",
                "mapped",
                stable_hash(payload),
            )
            stats["fab_status_dry_run"] += 1
            continue

        if not job_id:
            await upsert_key_map(
                db,
                run_id,
                "Fab_Status",
                source_fab_id,
                f"job={job_number}|account={account_name}",
                "fabs",
                None,
                "direct_pk",
                "failed",
                stable_hash(payload),
                "job_id unresolved",
            )
            stats["fab_status_failed"] += 1
            continue

        rs = await db.execute(text("""
        INSERT INTO fabs (
          job_id, fab_type, sales_person_id, stone_type_id, stone_color_id,
          stone_thickness_id, edge_id, total_sqft, no_of_pieces,
          status_id, created_by, created_at,
          revised, shop_date_schedule, installation_date,
          draft_completed, sct_completed, final_programming_complete, template_needed
        ) VALUES (
          :job_id, :fab_type, :sales_person_id, :stone_type_id, :stone_color_id,
          :stone_thickness_id, :edge_id, :total_sqft, :no_of_pieces,
          :status_id, :created_by, NOW(),
          :revised, :shop_date_schedule, :installation_date,
          :draft_completed, :sct_completed, :final_programming_complete, false
        )
        RETURNING id
        """), {
            "job_id": job_id,
            "fab_type": str(row.get("fab_type") or "Unknown")[:255],
            "sales_person_id": cfg["user_id"],
            "stone_type_id": cfg["stone_type_id"],
            "stone_color_id": cfg["stone_color_id"],
            "stone_thickness_id": cfg["stone_thickness_id"],
            "edge_id": cfg["edge_id"],
            "total_sqft": float(total_sqft or 0.0),
            "no_of_pieces": as_int(row.get("number_pieces")),
            "status_id": cfg["status_id"],
            "created_by": cfg["user_id"],
            "revised": as_bool(row.get("been_revised")),
            "shop_date_schedule": as_dt(row.get("shop_date_scheduled")),
            "installation_date": as_dt(row.get("install_date")),
            "draft_completed": as_bool(row.get("draft_completed")),
            "sct_completed": as_bool(row.get("sct_completed")),
            "final_programming_complete": as_bool(row.get("final_completed")),
        })

        new_fab_id = rs.scalar_one()

        await upsert_key_map(
            db,
            run_id,
            "Fab_Status",
            source_fab_id,
            f"job={job_number}|account={account_name}",
            "fabs",
            new_fab_id,
            "direct_pk",
            "mapped",
            stable_hash(payload),
        )
        stats["fab_status_inserted"] += 1


async def migrate_revision_info(db, run_id, rows, cfg, dry_run, stats):
    for row in rows:
        source_fab_id = str(row.get("fab_id") or row.get("FabID") or "").strip()
        if not source_fab_id:
            stats["revision_skipped_missing_fab_id"] += 1
            continue

        fab_map = await db.execute(text("""
            SELECT target_pk FROM migration_key_map
            WHERE source_system='CASPIO'
              AND source_table='Fab_Status'
              AND source_pk=:source_pk
              AND target_table='fabs'
        """), {"source_pk": source_fab_id})
        m = fab_map.first()
        target_fab_id = m[0] if m else None

        revision_type = str(row.get("RevisionType") or row.get("revision_type") or "Unknown")
        revision_reason = row.get("RevisionReason") or row.get("revision_reason")
        revision_notes = row.get("RevisionNotes") or row.get("revision_notes")
        source_pk = str(row.get("revision_id") or f"{source_fab_id}:{revision_type}:{revision_reason or ''}")

        payload = {
            "source_fab_id": source_fab_id,
            "revision_type": revision_type,
            "revision_reason": revision_reason,
        }

        if dry_run:
            await upsert_key_map(
                db,
                run_id,
                "revision_info",
                source_pk,
                f"fab={source_fab_id}",
                "revisions",
                None,
                "composite_key",
                "mapped",
                stable_hash(payload),
            )
            stats["revision_dry_run"] += 1
            continue

        if not target_fab_id:
            await upsert_key_map(
                db,
                run_id,
                "revision_info",
                source_pk,
                f"fab={source_fab_id}",
                "revisions",
                None,
                "composite_key",
                "failed",
                stable_hash(payload),
                "target fab not found in migration_key_map",
            )
            stats["revision_failed"] += 1
            continue

        rs = await db.execute(text("""
        INSERT INTO revisions (
          fab_id, revision_type, requested_by, assigned_to,
          revision_reason, revision_notes, is_completed,
          status_id, created_at, updated_at, updated_by
        ) VALUES (
          :fab_id, :revision_type, :requested_by, NULL,
          :revision_reason, :revision_notes, :is_completed,
          :status_id, NOW(), NULL, NULL
        )
        ON CONFLICT (fab_id)
        DO UPDATE SET
          revision_type = EXCLUDED.revision_type,
          revision_reason = EXCLUDED.revision_reason,
          revision_notes = EXCLUDED.revision_notes,
          is_completed = EXCLUDED.is_completed,
          updated_at = NOW()
        RETURNING id
        """), {
            "fab_id": target_fab_id,
            "revision_type": revision_type,
            "requested_by": cfg["user_id"],
            "revision_reason": revision_reason,
            "revision_notes": revision_notes,
            "is_completed": as_bool(row.get("is_completed")),
            "status_id": cfg["status_id"],
        })

        revision_id = rs.scalar_one()

        await upsert_key_map(
            db,
            run_id,
            "revision_info",
            source_pk,
            f"fab={source_fab_id}",
            "revisions",
            revision_id,
            "composite_key",
            "mapped",
            stable_hash(payload),
        )
        stats["revision_upserted"] += 1


async def migrate_shop_data(db, run_id, rows, cfg, dry_run, stats):
    seq_by_fab: Dict[int, int] = defaultdict(int)

    for row in rows:
        source_fab_id = str(row.get("fab_id") or "").strip()
        if not source_fab_id:
            stats["shop_data_skipped_missing_fab_id"] += 1
            continue

        fab_map = await db.execute(text("""
            SELECT target_pk FROM migration_key_map
            WHERE source_system='CASPIO'
              AND source_table='Fab_Status'
              AND source_pk=:source_pk
              AND target_table='fabs'
        """), {"source_pk": source_fab_id})
        m = fab_map.first()
        target_fab_id = m[0] if m else None

        source_pk = str(
            row.get("shop_data_id")
            or row.get("id")
            or f"{source_fab_id}:{row.get('activity','')}:{row.get('start_time','')}"
        )

        payload = {
            "source_fab_id": source_fab_id,
            "activity": row.get("activity"),
            "machine": row.get("machine"),
        }

        if dry_run:
            await upsert_key_map(
                db,
                run_id,
                "Shop_Data",
                source_pk,
                f"fab={source_fab_id}",
                "shop_cut_plans",
                None,
                "composite_key",
                "mapped",
                stable_hash(payload),
            )
            stats["shop_data_dry_run"] += 1
            continue

        if not target_fab_id:
            await upsert_key_map(
                db,
                run_id,
                "Shop_Data",
                source_pk,
                f"fab={source_fab_id}",
                "shop_cut_plans",
                None,
                "composite_key",
                "failed",
                stable_hash(payload),
                "target fab not found in migration_key_map",
            )
            stats["shop_data_failed"] += 1
            continue

        seq_by_fab[target_fab_id] += 1

        notes_parts = [
            f"legacy_activity={row.get('activity')}" if row.get("activity") else None,
            f"legacy_machine={row.get('machine')}" if row.get("machine") else None,
            f"legacy_employee={row.get('shop_employee')}" if row.get("shop_employee") else None,
            f"legacy_notes={row.get('notes')}" if row.get("notes") else None,
        ]
        notes = " | ".join([p for p in notes_parts if p])

        rs = await db.execute(text("""
        INSERT INTO shop_cut_plans (
          fab_id, workstation_id, planning_section_id, user_id,
          sequence, estimated_hours, scheduled_start_date,
          actual_start_date, actual_end_date, work_percentage,
          notes, created_at, created_by
        ) VALUES (
          :fab_id, :workstation_id, :planning_section_id, :user_id,
          :sequence, :estimated_hours, :scheduled_start_date,
          :actual_start_date, :actual_end_date, :work_percentage,
          :notes, NOW(), :created_by
        )
        RETURNING id
        """), {
            "fab_id": target_fab_id,
            "workstation_id": cfg["workstation_id"],
            "planning_section_id": cfg["planning_section_id"],
            "user_id": cfg["user_id"],
            "sequence": seq_by_fab[target_fab_id],
            "estimated_hours": as_float(row.get("hours_scheduled"), 1.0) or 1.0,
            "scheduled_start_date": as_dt(row.get("date_scheduled")),
            "actual_start_date": as_dt(row.get("start_time")),
            "actual_end_date": as_dt(row.get("end_time")),
            "work_percentage": max(0, min(100, as_int(row.get("percent_complete"), 0) or 0)),
            "notes": notes[:2000] if notes else None,
            "created_by": cfg["user_id"],
        })
        shop_cut_plan_id = rs.scalar_one()

        await upsert_key_map(
            db,
            run_id,
            "Shop_Data",
            source_pk,
            f"fab={source_fab_id}",
            "shop_cut_plans",
            shop_cut_plan_id,
            "composite_key",
            "mapped",
            stable_hash(payload),
        )
        stats["shop_data_inserted"] += 1


async def run_migration(args):
    dry_run = not args.apply
    run_id = uuid.UUID(args.run_id)

    if not os.path.exists(args.xml):
        raise FileNotFoundError(f"XML file not found: {args.xml}")

    tables = extract_table_rows(args.xml)
    fab_status_rows = tables.get("Fab_Status", [])
    revision_rows = tables.get("revision_info", [])
    shop_data_rows = tables.get("Shop_Data", [])

    print(
        "Parsed source rows: "
        f"Fab_Status={len(fab_status_rows)}, "
        f"revision_info={len(revision_rows)}, "
        f"Shop_Data={len(shop_data_rows)}"
    )

    if not fab_status_rows and not revision_rows and not shop_data_rows:
        print("No data rows found for target tables. Ensure XML contains records (not only schema metadata).")
        return

    cfg = {
        "user_id": args.default_user_id,
        "status_id": args.default_status_id,
        "stone_type_id": args.default_stone_type_id,
        "stone_color_id": args.default_stone_color_id,
        "stone_thickness_id": args.default_stone_thickness_id,
        "edge_id": args.default_edge_id,
        "workstation_id": args.default_workstation_id,
        "planning_section_id": args.default_planning_section_id,
    }

    stats: Dict[str, int] = defaultdict(int)

    async with SessionLocal() as db:
        try:
            preflight_errors = await run_preflight_checks(db, cfg)
        except Exception as exc:
            print("Preflight check could not query the database.")
            print(f"Reason: {exc}")
            print("Verify DATABASE_URL and ensure schema migrations have been applied.")
            await db.rollback()
            return

        if preflight_errors:
            print("Preflight check failed:")
            for err in preflight_errors:
                print(f"  - {err}")
            await db.rollback()
            return

        print("Preflight check passed.")

        if args.preflight_only:
            await db.rollback()
            print("Preflight-only mode complete. No migration executed.")
            return

        await ensure_key_map_table(db)
        await migrate_fab_status(db, run_id, fab_status_rows, cfg, dry_run, stats)
        await migrate_revision_info(db, run_id, revision_rows, cfg, dry_run, stats)
        await migrate_shop_data(db, run_id, shop_data_rows, cfg, dry_run, stats)

        if dry_run:
            await db.rollback()
            print("Dry-run finished. Transaction rolled back (no changes applied).")
        else:
            await db.commit()
            print("Apply mode finished. Transaction committed.")

    print("\nMigration stats:")
    for key in sorted(stats.keys()):
        print(f"  {key}: {stats[key]}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test/execute Caspio XML migration for Fab_Status, revision_info, Shop_Data"
    )
    parser.add_argument(
        "--xml",
        default="Tables_2026-Jun-29_1712.xml",
        help="Path to XML file (default: Tables_2026-Jun-29_1712.xml)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply writes. Default is dry-run.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run FK/default-ID validation only and exit.",
    )
    parser.add_argument(
        "--run-id",
        default=str(uuid.uuid4()),
        help="UUID for this migration run.",
    )

    # Safe required defaults for target FK and audit fields.
    parser.add_argument("--default-user-id", type=int, required=True)
    parser.add_argument("--default-status-id", type=int, required=True)
    parser.add_argument("--default-stone-type-id", type=int, required=True)
    parser.add_argument("--default-stone-color-id", type=int, required=True)
    parser.add_argument("--default-stone-thickness-id", type=int, required=True)
    parser.add_argument("--default-edge-id", type=int, required=True)
    parser.add_argument("--default-workstation-id", type=int, required=False)
    parser.add_argument("--default-planning-section-id", type=int, required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(run_migration(args))


if __name__ == "__main__":
    main()
