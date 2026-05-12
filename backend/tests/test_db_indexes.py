"""Regression tests for DB indexes on hot read paths.

Two layers of assertion per index:

1. **Schema check** — ``sqlite_master`` lists the index after ``create_all`` runs.
2. **Plan check** — ``EXPLAIN QUERY PLAN`` on the exact ORM-emitted SQL must
   reference the index (i.e. SQLite picked it). This guards against future
   schema changes that silently break the optimizer's choice.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _existing_indexes(test_db, table: str) -> set[str]:
    """Return the names of all non-autoindex indexes on a given table."""
    with test_db.get_session() as s:
        rows = s.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = :t AND name NOT LIKE 'sqlite_autoindex_%'"
            ),
            {"t": table},
        ).all()
    return {r[0] for r in rows}


def _plan(test_db, sql: str, params: dict | None = None) -> str:
    """Return the EXPLAIN QUERY PLAN output for a raw SQL string."""
    with test_db.get_session() as s:
        rows = s.execute(text(f"EXPLAIN QUERY PLAN {sql}"), params or {}).all()
    return " | ".join(str(r) for r in rows)


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


def test_automation_tasks_indexes_created(test_db):
    names = _existing_indexes(test_db, "automation_tasks")
    assert "ix_automation_tasks_user_started" in names
    assert "ix_automation_tasks_status" in names


def test_applications_indexes_created(test_db):
    names = _existing_indexes(test_db, "applications")
    assert "ix_applications_user_timestamp" in names
    assert "ix_applications_user_status_ts" in names


def test_bot_runs_indexes_created(test_db):
    names = _existing_indexes(test_db, "bot_runs")
    assert "ix_bot_runs_start_time" in names


# ---------------------------------------------------------------------------
# Plan checks: the optimizer must actually pick the index
# ---------------------------------------------------------------------------


def test_count_automation_tasks_today_uses_index(test_db):
    # Seed a few rows so the optimizer doesn't trivially short-circuit.
    for i in range(5):
        test_db.create_automation_task(f"idx-{i}", "post", [], "/x", user_id="idx-u")

    plan = _plan(
        test_db,
        "SELECT COUNT(id) FROM automation_tasks "
        "WHERE user_id = :u AND started_at >= :c",
        {"u": "idx-u", "c": datetime.now(timezone.utc) - timedelta(hours=24)},
    )
    assert "ix_automation_tasks_user_started" in plan, plan


def test_list_automation_tasks_uses_index(test_db):
    for i in range(3):
        test_db.create_automation_task(f"idx2-{i}", "post", [], "/x", user_id="idx-u2")

    plan = _plan(
        test_db,
        "SELECT id FROM automation_tasks "
        "WHERE user_id = :u ORDER BY started_at DESC LIMIT 50",
        {"u": "idx-u2"},
    )
    assert "ix_automation_tasks_user_started" in plan, plan


def test_running_status_filter_uses_index(test_db):
    test_db.create_automation_task("idx3-a", "post", [], "/x", user_id="idx-u3")

    plan = _plan(
        test_db,
        "SELECT COUNT(id) FROM automation_tasks WHERE status = :s",
        {"s": "running"},
    )
    assert "ix_automation_tasks_status" in plan, plan


def test_recent_applications_uses_index(test_db):
    for i in range(3):
        test_db.log_application(
            "idx-app-u", status="applied", job_title=f"j{i}", company="c"
        )

    plan = _plan(
        test_db,
        "SELECT id FROM applications "
        "WHERE user_id = :u ORDER BY timestamp DESC LIMIT 20",
        {"u": "idx-app-u"},
    )
    # Either composite index satisfies this; both have user_id as the leading column.
    assert (
        "ix_applications_user_timestamp" in plan
        or "ix_applications_user_status_ts" in plan
    ), plan


def test_monthly_application_count_uses_index(test_db):
    for _ in range(3):
        test_db.log_application(
            "idx-app-u2", status="applied", job_title="t", company="c"
        )

    plan = _plan(
        test_db,
        "SELECT COUNT(id) FROM applications "
        "WHERE user_id = :u AND status = :s AND timestamp >= :c",
        {
            "u": "idx-app-u2",
            "s": "applied",
            "c": datetime.now(timezone.utc) - timedelta(days=30),
        },
    )
    # With status in the WHERE, the 3-column index is most selective.
    assert "ix_applications_user_status_ts" in plan, plan


def test_last_activity_snapshot_uses_index(test_db):
    for _ in range(3):
        test_db.log_application("idx-snap-u", status="applied", job_title="t", company="c")
    test_db.log_application("idx-snap-u", status="failed", job_title="t", company="c")

    plan = _plan(
        test_db,
        "SELECT id FROM applications "
        "WHERE user_id = :u AND status = :s "
        "ORDER BY timestamp DESC LIMIT 1",
        {"u": "idx-snap-u", "s": "applied"},
    )
    assert "ix_applications_user_status_ts" in plan, plan


def test_recent_bot_runs_uses_index(test_db):
    test_db.start_bot_run("idx-bot-u")
    test_db.start_bot_run("idx-bot-u")

    plan = _plan(
        test_db,
        "SELECT id FROM bot_runs ORDER BY start_time DESC LIMIT 10",
    )
    assert "ix_bot_runs_start_time" in plan, plan


# ---------------------------------------------------------------------------
# Idempotency: rerunning create_all (e.g. on every backend boot) is safe
# ---------------------------------------------------------------------------


def test_create_all_is_idempotent(test_db):
    """Re-running ``metadata.create_all`` on an existing DB must not raise.

    Real backends call this on every boot via ``DatabaseManager.__init__``;
    SQLAlchemy emits ``CREATE INDEX IF NOT EXISTS`` so the second pass is a
    no-op.
    """
    from models import Base

    Base.metadata.create_all(bind=test_db.engine)
    Base.metadata.create_all(bind=test_db.engine)

    names = _existing_indexes(test_db, "automation_tasks")
    assert "ix_automation_tasks_user_started" in names
