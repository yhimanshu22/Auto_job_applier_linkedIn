"""One-shot: copy existing template config rows to the owner's account.

Before multi-tenancy, all config rows were global. The schema migration in
db_manager assigns them to the "local-user" template namespace. Identity
categories (personals, secrets, linkedin_automation, form defaults) are NOT
inherited by real users, so the original owner would see empty forms after
logging in. This script copies every template row the owner doesn't already
have into their namespace.

Usage:
    uv run python migrate_configs_owner.py you@gmail.com
    (set DATABASE_URL first to run against Postgres)
"""

import sys

from db_manager import DEFAULT_USER, db
from models import Config


def main(owner: str) -> None:
    owner = owner.strip()
    if not owner or owner == DEFAULT_USER:
        raise SystemExit("Pass the owner's login email as the first argument.")

    copied = 0
    skipped = 0
    with db.get_session() as session:
        template_rows = (
            session.query(Config).filter(Config.user_id == DEFAULT_USER).all()
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
