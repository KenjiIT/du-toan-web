# -*- coding: utf-8 -*-
"""Add project_other_costs table for TMDT calculation."""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dutoan.db"


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_other_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            calc_type TEXT DEFAULT 'percent',
            percent_value REAL,
            fixed_value REAL,
            notes TEXT,
            sort_order INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_project_other_costs_project_id
        ON project_other_costs(project_id)
    """)
    print("Created project_other_costs table.")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
