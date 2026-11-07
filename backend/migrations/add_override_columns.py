"""Add override_vlc, override_nc, override_mtc columns to project_items."""

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

    # Check which columns already exist
    cursor.execute("PRAGMA table_info(project_items)")
    existing = {row[1] for row in cursor.fetchall()}

    new_cols = [
        ("override_vlc", "REAL DEFAULT NULL"),
        ("override_nc", "REAL DEFAULT NULL"),
        ("override_mtc", "REAL DEFAULT NULL"),
    ]

    for col_name, col_def in new_cols:
        if col_name in existing:
            print(f"  Column {col_name} already exists, skipping.")
        else:
            sql = f"ALTER TABLE project_items ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            print(f"  Added column {col_name}.")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
