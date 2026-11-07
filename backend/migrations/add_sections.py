# -*- coding: utf-8 -*-
"""Add project_sections table and section_id column to project_items.

Migrates existing items into auto-created sections based on mhdg prefix.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dutoan.db"

SECTION_NAMES = {
    "XD": "Xây dựng",
    "LD": "Lắp đặt",
    "SC": "Sửa chữa",
    "KS": "Khảo sát",
}

DEFAULT_SECTION_RATES = {
    "XD": {"chi_phi_chung_pct": 6.5, "thu_nhap_tt_pct": 5.5},
    "LD": {"chi_phi_chung_pct": 5.5, "thu_nhap_tt_pct": 5.5},
    "SC": {"chi_phi_chung_pct": 5.5, "thu_nhap_tt_pct": 5.5},
    "KS": {"chi_phi_chung_pct": 4.0, "thu_nhap_tt_pct": 5.5},
}

SORT_MAP = {"XD": 0, "LD": 1, "SC": 2, "KS": 3}


def detect_cost_type(mhdg: str) -> str:
    prefix = mhdg[:2].upper() if len(mhdg) >= 2 else ""
    if prefix in ("SA", "SB", "SC", "SD", "SE", "SF"):
        return "SC"
    if prefix in ("BA", "BB", "BC", "BD"):
        return "LD"
    if prefix in ("CA", "CB", "CC", "CD", "CE", "CF", "CG", "CH", "CI", "CK"):
        return "KS"
    return "XD"


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Create project_sections table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            cost_type TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            chi_phi_chung_pct REAL,
            thu_nhap_tt_pct REAL
        )
    """)
    # Index on project_id
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_project_sections_project_id
        ON project_sections(project_id)
    """)
    print("  Created project_sections table (if not exists).")

    # 2. Add section_id column to project_items if not present
    cursor.execute("PRAGMA table_info(project_items)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if "section_id" not in existing_cols:
        cursor.execute(
            "ALTER TABLE project_items ADD COLUMN section_id INTEGER "
            "REFERENCES project_sections(id) ON DELETE SET NULL"
        )
        print("  Added section_id column to project_items.")
        # Index on section_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_project_items_section_id
            ON project_items(section_id)
        """)
    else:
        print("  Column section_id already exists, skipping.")

    # 3. Migrate existing items: create sections and assign items
    cursor.execute("SELECT DISTINCT project_id FROM project_items WHERE section_id IS NULL")
    project_ids = [row[0] for row in cursor.fetchall()]

    if not project_ids:
        print("  No unassigned items to migrate.")
    else:
        print(f"  Migrating items for {len(project_ids)} project(s)...")

    for pid in project_ids:
        # Get all items for this project that have no section
        cursor.execute(
            "SELECT id, mhdg FROM project_items WHERE project_id = ? AND section_id IS NULL",
            (pid,),
        )
        items = cursor.fetchall()

        # Group items by cost_type
        groups: dict[str, list[int]] = {}
        for item_id, mhdg in items:
            ct = detect_cost_type(mhdg)
            groups.setdefault(ct, []).append(item_id)

        for cost_type, item_ids in groups.items():
            # Check if section already exists for this project + cost_type
            cursor.execute(
                "SELECT id FROM project_sections WHERE project_id = ? AND cost_type = ?",
                (pid, cost_type),
            )
            row = cursor.fetchone()
            if row:
                section_id = row[0]
            else:
                defaults = DEFAULT_SECTION_RATES.get(cost_type, DEFAULT_SECTION_RATES["XD"])
                name = f"Phần {cost_type} - {SECTION_NAMES.get(cost_type, cost_type)}"
                cursor.execute(
                    "INSERT INTO project_sections (project_id, name, cost_type, sort_order, chi_phi_chung_pct, thu_nhap_tt_pct) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (pid, name, cost_type, SORT_MAP.get(cost_type, 99),
                     defaults["chi_phi_chung_pct"], defaults["thu_nhap_tt_pct"]),
                )
                section_id = cursor.lastrowid
                print(f"    Project {pid}: created section '{name}' (id={section_id})")

            # Assign items to section
            placeholders = ",".join("?" for _ in item_ids)
            cursor.execute(
                f"UPDATE project_items SET section_id = ? WHERE id IN ({placeholders})",
                [section_id] + item_ids,
            )
            print(f"    Project {pid}: assigned {len(item_ids)} items to section {cost_type}")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
