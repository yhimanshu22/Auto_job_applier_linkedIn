"""One-shot migration: copy all rows from local SQLite (data.db) into the
Postgres database given by DATABASE_URL. Destination tables are created if
missing and overwritten if they contain rows.

Usage: DATABASE_URL=postgresql://... uv run python migrate_to_pg.py
"""

import os
import sys

from sqlalchemy import create_engine, select, text

from models import Base

dst_url = os.environ.get("DATABASE_URL")
if not dst_url or not dst_url.startswith("postgresql"):
    sys.exit("Set DATABASE_URL to a postgresql:// URL before running.")

src = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})
dst = create_engine(dst_url)

Base.metadata.create_all(dst)

SERIAL_TABLES = ["subscriptions", "bot_runs", "applications", "resumes"]

with src.connect() as s, dst.begin() as d:
    for table in Base.metadata.sorted_tables:
        rows = [dict(r._mapping) for r in s.execute(select(table))]
        d.execute(table.delete())
        if rows:
            d.execute(table.insert(), rows)
        print(f"{table.name}: {len(rows)} rows")

    # SQLite rows carry explicit ids; bump Postgres sequences past the max.
    for tname in SERIAL_TABLES:
        d.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{tname}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tname}), 0) + 1, false)"
            )
        )

print("MIGRATION_DONE")
