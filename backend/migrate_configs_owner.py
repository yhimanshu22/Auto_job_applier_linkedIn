"""One-shot: copy legacy template config rows to the owner's account.

Before multi-tenancy, all config rows were global. The schema migration in
db_manager assigns them to the legacy ``local-user`` namespace. Run this once
after signing in with Google to copy those rows into your email namespace.

Usage:
    uv run python migrate_configs_owner.py you@gmail.com
    (set DATABASE_URL first to run against Postgres)
"""

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_BACKEND_DIR, "config")
for _path in (_CONFIG_DIR, _BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

from db_manager import db
from models import Config

_LEGACY_TEMPLATE_OWNER = "local-user"


def main(owner: str) -> None:
    owner = owner.strip()
    if not owner or owner == _LEGACY_TEMPLATE_OWNER:
        raise SystemExit("Pass the owner's login email as the first argument.")

    copied = 0
    skipped = 0
    with db.get_session() as session:
        template_rows = (
            session.query(Config).filter(Config.user_id == _LEGACY_TEMPLATE_OWNER).all()
        )
        existing_keys = {
            row.key
            for row in session.query(Config).filter(Config.user_id == owner).all()
        }
        for row in template_rows:
            if row.key in existing_keys:
                skipped += 1
                continue
            session.add(
                Config(
                    user_id=owner,
                    key=row.key,
                    value=row.value,
                    category=row.category,
                    is_encrypted=row.is_encrypted,
                )
            )
            copied += 1
        session.commit()

    print(f"DB: {db.db_url.split('@')[-1] if '@' in db.db_url else db.db_url}")
    print(f"Copied {copied} config rows to {owner!r} ({skipped} already existed).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
