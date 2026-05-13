"""Tests for the LinkedIn automation integration.

Covers the route surface, service-level helpers, DB persistence, env injection,
plan gating, and the Linkedln-Automation-Framework package layout.

``subprocess.Popen`` is monkeypatched so we never actually launch Selenium /
Chrome from the test suite.
"""

import os
import subprocess
from datetime import datetime, timedelta, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


class FakePopen:
    """Drop-in mock for ``subprocess.Popen`` used by the automation service.

    Defaults to "still running" until the test calls :meth:`exit` to simulate a
    process completion with a chosen exit code.
    """

    instances: list["FakePopen"] = []

    def __init__(self, *args, **kwargs):
        self.pid = 99999
        self._exit_code: int | None = None
        self.cmd = args[0] if args else kwargs.get("args")
        self.cwd = kwargs.get("cwd")
        self.env = kwargs.get("env")
        FakePopen.instances.append(self)

    def poll(self):
        return self._exit_code

    def wait(self, timeout=None):
        return self._exit_code if self._exit_code is not None else 0

    def terminate(self):
        if self._exit_code is None:
            self._exit_code = -15

    def kill(self):
        if self._exit_code is None:
            self._exit_code = -9

    def exit(self, code: int = 0) -> None:
        self._exit_code = code


@pytest.fixture
def fake_popen(monkeypatch):
    """Replace ``subprocess.Popen`` (and ``subprocess.run`` for taskkill) with fakes.

    Patching ``subprocess.Popen`` globally would also affect any internal use of
    ``subprocess.run`` (which builds a ``with Popen(...)`` block). To keep
    ``stop_task`` happy on Windows where it shells out to ``taskkill``, we also
    stub ``subprocess.run`` so it never touches the real OS.
    """
    FakePopen.instances = []
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service.subprocess, "Popen", FakePopen)

    class _CompletedProcess:
        def __init__(self, returncode=0):
            self.returncode = returncode
            self.stdout = b""
            self.stderr = b""

    def fake_run(*args, **kwargs):
        return _CompletedProcess(returncode=0)

    monkeypatch.setattr(la_service.subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "run", fake_run)
    yield FakePopen
    for t in list(la_service._tasks.values()):
        proc = t.process
        if isinstance(proc, FakePopen) and proc._exit_code is None:
            proc._exit_code = 0
        la_service._reap(t)
    la_service._tasks.clear()


@pytest.fixture
def clear_automation_tasks(test_db):
    """Wipe ``automation_tasks`` rows so each test starts from zero."""
    from sqlalchemy import text

    with test_db.get_session() as s:
        s.execute(text("DELETE FROM automation_tasks"))
        s.commit()
    # Also empty the in-memory registry to keep state predictable.
    from services import linkedin_automation as la_service

    la_service._tasks.clear()
    yield
    from services import linkedin_automation as la_service

    la_service._tasks.clear()


@pytest.fixture
def clear_automation_config(test_db):
    """Remove any persisted ``linkedin_automation`` config rows."""
    from sqlalchemy import text

    with test_db.get_session() as s:
        s.execute(text("DELETE FROM configs WHERE category = 'linkedin_automation'"))
        s.commit()
    yield
    with test_db.get_session() as s:
        s.execute(text("DELETE FROM configs WHERE category = 'linkedin_automation'"))
        s.commit()


# ---------------------------------------------------------------------------
# Package layout
# ---------------------------------------------------------------------------


def test_package_is_importable():
    """The new ``linkedin_automation`` package should resolve from the backend."""
    import linkedin_automation  # noqa: F401
    from linkedin_automation import config  # noqa: F401


def test_package_has_main_entrypoint():
    """``__main__`` must exist so ``python -m linkedin_automation`` works."""
    import importlib

    spec = importlib.util.find_spec("linkedin_automation.__main__")
    assert spec is not None, "linkedin_automation.__main__ should be importable"


def test_framework_dir_resolves_to_package(monkeypatch):
    from services import linkedin_automation as la_service

    fdir = la_service.get_framework_dir()
    assert os.path.basename(fdir) == "linkedin_automation"
    assert os.path.isdir(fdir)
    assert os.path.isfile(os.path.join(fdir, "__main__.py"))
    assert os.path.isfile(os.path.join(fdir, "__init__.py"))


# ---------------------------------------------------------------------------
# Service: command + env building
# ---------------------------------------------------------------------------


def test_build_command_post_with_text():
    from services import linkedin_automation as la_service

    cmd = la_service._build_command(
        "post",
        {"post_text": "hello", "no_ai": True, "debug": True, "headless": True},
    )
    assert cmd[1:4] == ["-m", "linkedin_automation", "post"]
    assert "--no-ai" in cmd
    assert "--debug" in cmd
    assert "--headless" in cmd
    assert "--post-text" in cmd
    assert cmd[cmd.index("--post-text") + 1] == "hello"


def test_build_command_engage_defaults_and_overrides():
    from services import linkedin_automation as la_service

    cmd = la_service._build_command(
        "engage", {"engage_action": "comment", "max_actions": 7}
    )
    assert "--action" in cmd
    assert cmd[cmd.index("--action") + 1] == "comment"
    assert cmd[cmd.index("--max-actions") + 1] == "7"


def test_build_command_pursue_boolean_flags_and_lists():
    from services import linkedin_automation as la_service

    cmd = la_service._build_command(
        "pursue",
        {
            "profile_name": "Alice Test",
            "max_posts": 4,
            "perspectives": ["insightful", "funny"],
            "bio_keywords": ["investor"],
            "should_follow": False,
            "should_like": True,
            "should_comment": False,
        },
    )
    assert cmd[3] == "pursue"
    assert cmd[4] == "Alice Test"
    assert "--max-posts" in cmd and cmd[cmd.index("--max-posts") + 1] == "4"
    assert cmd[cmd.index("--perspectives") + 1 : cmd.index("--perspectives") + 3] == [
        "insightful",
        "funny",
    ]
    assert "--no-follow" in cmd
    assert "--no-comment" in cmd
    assert "--no-like" not in cmd


def test_build_command_calendar_requires_niche():
    from services import linkedin_automation as la_service

    with pytest.raises(ValueError):
        la_service._build_command("generate-calendar", {})


def test_build_command_unknown_action_rejected():
    from services import linkedin_automation as la_service

    with pytest.raises(ValueError):
        la_service._build_command("teleport", {"foo": "bar"})


def test_build_env_sets_cookie_path_and_pythonpath():
    from services import linkedin_automation as la_service

    env = la_service._build_env()
    assert env["LINKEDIN_COOKIE_PATH"].endswith("linkedin_cookies.pkl")
    assert la_service.get_base_path() in env["PYTHONPATH"]


# ---------------------------------------------------------------------------
# Per-account cookie path
#
# A single shared ``linkedin_cookies.pkl`` meant whichever LinkedIn identity
# logged in first won — every subsequent run reused that session even when
# the dashboard had selected a different account. The path is now derived
# from the resolved account, with the legacy path kept for the primary so
# existing sessions survive the upgrade.
# ---------------------------------------------------------------------------


def test_cookie_slug_sanitises_email():
    from services.linkedin_automation import _cookie_slug

    assert _cookie_slug("himu09854@gmail.com") == "himu09854_at_gmail.com"
    assert _cookie_slug("YHimanshu220456@Gmail.com") == "yhimanshu220456_at_gmail.com"
    # Anything outside [a-z0-9._-] collapses to underscores; trailing
    # underscores trimmed so we don't produce names like ``foo_.pkl``.
    assert _cookie_slug("weird ::name++") == "weird_name"
    assert _cookie_slug("") == "default"


def test_get_cookie_path_for_account_returns_legacy_when_no_account():
    from services.linkedin_automation import (
        get_cookie_path_for_account,
        get_shared_cookie_path,
    )

    assert get_cookie_path_for_account(None) == get_shared_cookie_path()
    assert get_cookie_path_for_account("") == get_shared_cookie_path()
    assert get_cookie_path_for_account("   ") == get_shared_cookie_path()


def test_get_cookie_path_for_account_returns_legacy_for_primary():
    from services.linkedin_automation import (
        get_cookie_path_for_account,
        get_shared_cookie_path,
    )

    legacy = get_shared_cookie_path()
    # Case-insensitive match against the primary returns the legacy path
    # so the existing main-account session survives the migration.
    assert (
        get_cookie_path_for_account("himu09854@gmail.com", "Himu09854@Gmail.com")
        == legacy
    )


def test_get_cookie_path_for_account_returns_per_account_for_other():
    from services.linkedin_automation import (
        get_cookie_path_for_account,
        get_shared_cookie_path,
    )

    primary = "himu09854@gmail.com"
    path = get_cookie_path_for_account("yhimanshu220456@gmail.com", primary)
    assert path != get_shared_cookie_path()
    # Per-account paths live under ``<root>/cookies/<slug>.pkl``.
    assert os.sep + "cookies" + os.sep in path or "/cookies/" in path
    assert path.endswith("yhimanshu220456_at_gmail.com.pkl")


def test_build_env_uses_per_account_cookie_when_secondary_account_selected(
    monkeypatch,
):
    """Selecting a non-primary account must point the subprocess at its own
    cookie pickle so the previous account's session can't be reused."""
    from services import linkedin_automation as la_service

    monkeypatch.setenv("LINKEDIN_USERNAME", "himu09854@gmail.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "pw-primary")
    monkeypatch.setenv("LINKEDIN_USERNAME_1", "yhimanshu220456@gmail.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_1", "pw-secondary")

    env = la_service._build_env(account="yhimanshu220456@gmail.com")

    assert env["LINKEDIN_USERNAME"] == "yhimanshu220456@gmail.com"
    assert env["LINKEDIN_PASSWORD"] == "pw-secondary"
    # The cookie path must NOT be the legacy single file — that's what made
    # both accounts share a session before.
    assert not env["LINKEDIN_COOKIE_PATH"].endswith(os.sep + "linkedin_cookies.pkl")
    assert env["LINKEDIN_COOKIE_PATH"].endswith("yhimanshu220456_at_gmail.com.pkl")


def test_build_env_keeps_legacy_cookie_path_for_primary_account(monkeypatch):
    """Asking for the primary account explicitly still uses the legacy file
    so the user's existing main-account session survives this change."""
    from services import linkedin_automation as la_service

    monkeypatch.setenv("LINKEDIN_USERNAME", "himu09854@gmail.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "pw-primary")

    env = la_service._build_env(account="himu09854@gmail.com")

    assert env["LINKEDIN_USERNAME"] == "himu09854@gmail.com"
    assert env["LINKEDIN_COOKIE_PATH"].endswith("linkedin_cookies.pkl")


# ---------------------------------------------------------------------------
# DB methods
# ---------------------------------------------------------------------------


def test_db_create_get_finalize_automation_task(test_db, clear_automation_tasks):
    test_db.create_automation_task(
        "la-post-aaa", "post", ["--post-text", "hi"], "/tmp/x.log", user_id="u-1"
    )
    row = test_db.get_automation_task("la-post-aaa")
    assert row is not None
    assert row["status"] == "running"
    assert row["action"] == "post"
    assert row["user_id"] == "u-1"
    assert row["args"] == ["--post-text", "hi"]
    assert row["exit_code"] is None

    test_db.finalize_automation_task("la-post-aaa", exit_code=0)
    row = test_db.get_automation_task("la-post-aaa")
    assert row["status"] == "completed"
    assert row["exit_code"] == 0
    assert row["ended_at"] is not None


def test_db_finalize_nonzero_marks_failed(test_db, clear_automation_tasks):
    test_db.create_automation_task("la-x", "engage", [], "/tmp/y.log", user_id="u-2")
    test_db.finalize_automation_task("la-x", exit_code=1)
    assert test_db.get_automation_task("la-x")["status"] == "failed"


def test_db_finalize_with_explicit_status(test_db, clear_automation_tasks):
    test_db.create_automation_task("la-y", "engage", [], "/tmp/y.log", user_id="u-3")
    test_db.finalize_automation_task("la-y", exit_code=-9, status="stopped")
    assert test_db.get_automation_task("la-y")["status"] == "stopped"


def test_db_list_filters_by_user(test_db, clear_automation_tasks):
    test_db.create_automation_task("a1", "post", [], "/tmp/a.log", user_id="alice")
    test_db.create_automation_task("b1", "post", [], "/tmp/b.log", user_id="bob")

    alice = test_db.list_automation_tasks(user_id="alice")
    assert {r["id"] for r in alice} == {"a1"}

    bob = test_db.list_automation_tasks(user_id="bob")
    assert {r["id"] for r in bob} == {"b1"}

    everyone = test_db.list_automation_tasks()
    assert {r["id"] for r in everyone} == {"a1", "b1"}


def test_count_automation_tasks_today_window(test_db, clear_automation_tasks):
    from sqlalchemy import update
    from models import AutomationTask

    test_db.create_automation_task("recent", "post", [], "/x", user_id="w")
    test_db.create_automation_task("old", "post", [], "/x", user_id="w")
    # Backdate `old` by 48 hours so it falls outside the 24h window.
    with test_db.get_session() as s:
        s.execute(
            update(AutomationTask)
            .where(AutomationTask.id == "old")
            .values(started_at=datetime.now(timezone.utc) - timedelta(hours=48))
        )
        s.commit()

    assert test_db.count_automation_tasks_today("w") == 1


def test_get_automation_task_stats_aggregates(test_db, clear_automation_tasks):
    test_db.create_automation_task("p1", "post", [], "/x", user_id="s")
    test_db.create_automation_task("p2", "post", [], "/x", user_id="s")
    test_db.create_automation_task("e1", "engage", [], "/x", user_id="s")
    test_db.finalize_automation_task("p1", exit_code=0)
    test_db.finalize_automation_task("e1", exit_code=1)

    stats = test_db.get_automation_task_stats(user_id="s")
    assert stats["total_all_time"] == 3
    assert stats["last_24h"] == 3
    assert stats["by_action_30d"] == {"post": 2, "engage": 1}
    assert stats["by_status_30d"]["completed"] == 1
    assert stats["by_status_30d"]["failed"] == 1
    assert stats["by_status_30d"]["running"] == 1
    assert stats["running"] == 1


def _count_selects(engine, fn):
    """Run ``fn`` and return how many SELECT statements were issued."""
    from sqlalchemy import event

    selects: list[str] = []

    def before_exec(conn, cursor, statement, parameters, context, executemany):
        stripped = statement.lstrip().upper()
        if stripped.startswith("SELECT"):
            selects.append(statement)

    event.listen(engine, "before_cursor_execute", before_exec)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", before_exec)
    return result, selects


def test_get_automation_task_stats_emits_two_queries(
    test_db, clear_automation_tasks
):
    """The refactor must compress the 6 prior queries down to 2."""
    for i in range(3):
        test_db.create_automation_task(f"q-{i}", "post", [], "/x", user_id="qcount")
    test_db.create_automation_task("q-e", "engage", [], "/x", user_id="qcount")
    test_db.finalize_automation_task("q-0", exit_code=0)

    _, selects = _count_selects(
        test_db.engine, lambda: test_db.get_automation_task_stats(user_id="qcount")
    )
    assert len(selects) == 2, (
        f"Expected 2 SELECTs, got {len(selects)}:\n" + "\n---\n".join(selects)
    )


def test_get_automation_task_stats_emits_two_queries_without_user_filter(
    test_db, clear_automation_tasks
):
    """The global path (``user_id=None``) must also use 2 queries."""
    test_db.create_automation_task("gq-1", "post", [], "/x", user_id="anyone")

    _, selects = _count_selects(
        test_db.engine, lambda: test_db.get_automation_task_stats(user_id=None)
    )
    assert len(selects) == 2, (
        f"Expected 2 SELECTs (no user filter), got {len(selects)}"
    )


def test_get_automation_task_stats_empty_db_safe(test_db, clear_automation_tasks):
    """Zero rows must not produce ``None`` totals or KeyErrors."""
    stats = test_db.get_automation_task_stats(user_id="ghost")
    assert stats == {
        "total_all_time": 0,
        "last_24h": 0,
        "last_30d": 0,
        "running": 0,
        "by_action_30d": {},
        "by_status_30d": {},
    }


def test_get_automation_task_stats_ignores_other_users(
    test_db, clear_automation_tasks
):
    """Per-user filter must not bleed across users in either count or breakdown."""
    test_db.create_automation_task("u1-a", "post", [], "/x", user_id="user-1")
    test_db.create_automation_task("u1-b", "engage", [], "/x", user_id="user-1")
    test_db.create_automation_task("u2-a", "post", [], "/x", user_id="user-2")

    stats = test_db.get_automation_task_stats(user_id="user-1")
    assert stats["total_all_time"] == 2
    assert stats["by_action_30d"] == {"post": 1, "engage": 1}


def test_get_automation_task_stats_respects_30d_window(
    test_db, clear_automation_tasks
):
    """Tasks older than 30 days drop out of ``last_30d`` and breakdowns but
    still count toward ``total_all_time``."""
    from sqlalchemy import update
    from models import AutomationTask

    test_db.create_automation_task("recent", "post", [], "/x", user_id="win")
    test_db.create_automation_task("old", "post", [], "/x", user_id="win")
    with test_db.get_session() as s:
        s.execute(
            update(AutomationTask)
            .where(AutomationTask.id == "old")
            .values(started_at=datetime.now(timezone.utc) - timedelta(days=45))
        )
        s.commit()

    stats = test_db.get_automation_task_stats(user_id="win")
    assert stats["total_all_time"] == 2
    assert stats["last_30d"] == 1
    assert stats["last_24h"] == 1
    assert stats["by_action_30d"] == {"post": 1}


# ---------------------------------------------------------------------------
# Settings injection
# ---------------------------------------------------------------------------


def test_get_automation_settings_masks_sensitive_keys(
    test_db, clear_automation_config
):
    test_db.set_config("openai_api_key", "sk-secret", category="linkedin_automation")
    test_db.set_config("project_name", "Plain", category="linkedin_automation")

    from services.linkedin_env import get_automation_settings

    masked = get_automation_settings(mask_sensitive=True)
    assert masked["openai_api_key"] == "set"
    assert masked["project_name"] == "Plain"

    raw = get_automation_settings(mask_sensitive=False)
    assert raw["openai_api_key"] == "sk-secret"


def test_apply_dashboard_automation_settings_into_env(
    test_db, clear_automation_config
):
    test_db.set_config("openai_api_key", "sk-abc", category="linkedin_automation")
    test_db.set_config("marketing_mode", True, category="linkedin_automation")
    test_db.set_config("use_gemini", False, category="linkedin_automation")
    test_db.set_config("project_url", "https://example.com", category="linkedin_automation")

    from services.linkedin_env import apply_dashboard_automation_settings

    env: dict = {}
    apply_dashboard_automation_settings(env)
    assert env["OPENAI_API_KEY"] == "sk-abc"
    assert env["MARKETING_MODE"] == "true"
    assert env["USE_GEMINI"] == "false"
    assert env["PROJECT_URL"] == "https://example.com"
    # An unset key should not appear at all.
    assert "GEMINI_API_KEY" not in env


# ---------------------------------------------------------------------------
# Routes: health + stats + tasks listing
# ---------------------------------------------------------------------------


def test_health_endpoint(client):
    res = client.get("/api/linkedin-automation/health")
    assert res.status_code == 200
    body = res.json()
    assert body["framework_available"] is True
    assert body["main_py_exists"] is True  # __main__.py exists under the package
    # We don't make assumptions about a saved cookie in CI.
    assert "shared_cookie_path" in body


def test_stats_endpoint_for_empty_user(client, clear_automation_tasks):
    res = client.get("/api/linkedin-automation/stats?user_id=fresh-user")
    assert res.status_code == 200
    body = res.json()
    assert body["last_24h"] == 0
    assert body["last_30d"] == 0
    assert body["total_all_time"] == 0
    assert body["running"] == 0
    assert body["daily_used"] == body["last_24h"]
    assert body["daily_limit"] >= 1


def test_stats_endpoint_admin_user_uses_agency_plan(client):
    res = client.get("/api/linkedin-automation/stats?user_id=local-user")
    assert res.status_code == 200
    body = res.json()
    assert body["plan"] == "agency"
    assert body["daily_limit"] >= 1000


def test_tasks_list_endpoint_returns_db_rows(
    client, test_db, clear_automation_tasks
):
    test_db.create_automation_task("hist-1", "post", [], "/log/hist-1", user_id="lu")
    test_db.finalize_automation_task("hist-1", exit_code=0)

    res = client.get("/api/linkedin-automation/tasks?user_id=lu")
    assert res.status_code == 200
    ids = {t["id"] for t in res.json()["tasks"]}
    assert "hist-1" in ids


def test_get_task_falls_back_to_db_when_not_in_memory(
    client, test_db, clear_automation_tasks
):
    test_db.create_automation_task("dead-1", "engage", [], "/log/dead-1", user_id="lu")
    test_db.finalize_automation_task("dead-1", exit_code=0)

    res = client.get("/api/linkedin-automation/tasks/dead-1")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "dead-1"
    assert body["status"] == "completed"
    assert body["running"] is False


def test_get_task_404_when_unknown(client, clear_automation_tasks):
    res = client.get("/api/linkedin-automation/tasks/does-not-exist")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Routes: config GET/POST
# ---------------------------------------------------------------------------


def test_config_get_returns_keys_with_sensitive_masked(
    client, test_db, clear_automation_config
):
    test_db.set_config("openai_api_key", "sk-stored", category="linkedin_automation")

    res = client.get("/api/linkedin-automation/config")
    assert res.status_code == 200
    body = res.json()
    assert body["openai_api_key"] == "set"
    assert "project_name" in body


def test_config_post_writes_settings_and_preserves_masked(
    client, test_db, clear_automation_config
):
    # First write a real OpenAI key.
    res1 = client.post(
        "/api/linkedin-automation/config",
        json={"openai_api_key": "sk-real-1", "project_name": "Acme"},
    )
    assert res1.status_code == 200
    assert res1.json()["settings"]["openai_api_key"] == "set"

    # Then submit with the masked sentinel; the real key should be preserved.
    res2 = client.post(
        "/api/linkedin-automation/config",
        json={"openai_api_key": "set", "project_name": "Acme Updated"},
    )
    assert res2.status_code == 200
    # Read raw to verify the sentinel didn't overwrite the real key.
    from services.linkedin_env import get_automation_settings

    raw = get_automation_settings(mask_sensitive=False)
    assert raw["openai_api_key"] == "sk-real-1"
    assert raw["project_name"] == "Acme Updated"


def test_config_post_rejects_empty_body(client):
    res = client.post("/api/linkedin-automation/config", json={})
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# Routes: action endpoints + gating
# ---------------------------------------------------------------------------


def test_post_endpoint_requires_subscription_for_non_admin(client, test_db):
    test_db.upsert_subscription("anon-user", plan="free_trial", status="inactive")
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "hi", "user_id": "anon-user"},
    )
    assert res.status_code == 402


def test_post_endpoint_blocks_expired_trial(client, test_db):
    expired = datetime.utcnow() - timedelta(hours=1)
    test_db.upsert_subscription(
        "expired-auto-user",
        plan="free_trial",
        status="trialing",
        current_period_end=expired.isoformat(),
    )
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "hi", "user_id": "expired-auto-user"},
    )
    assert res.status_code == 402
    assert "expired" in res.json()["detail"].lower()


def test_post_endpoint_blocks_when_daily_limit_reached(
    client, test_db, clear_automation_tasks
):
    test_db.upsert_subscription("freeq", plan="free_trial", status="active")
    # free_trial daily cap is 5 (see AUTOMATION_DAILY_LIMITS)
    for i in range(5):
        test_db.create_automation_task(
            f"q-{i}", "post", [], "/log/q", user_id="freeq"
        )
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "x", "user_id": "freeq"},
    )
    assert res.status_code == 403
    assert "daily automation limit" in res.json()["detail"].lower()


def test_post_endpoint_admin_bypass_starts_task(
    client, fake_popen, clear_automation_tasks
):
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "Hello world", "no_ai": True, "user_id": "local-user"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["action"] == "post"
    assert body["running"] is True
    assert body["id"].startswith("la-post-")
    assert len(fake_popen.instances) == 1
    spawned = fake_popen.instances[0]
    assert "-m" in spawned.cmd and "linkedin_automation" in spawned.cmd
    assert spawned.cwd.endswith("linkedin_automation")
    assert "LINKEDIN_COOKIE_PATH" in spawned.env


def test_post_endpoint_persists_task_to_db(
    client, test_db, fake_popen, clear_automation_tasks
):
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "persist me", "user_id": "local-user"},
    )
    assert res.status_code == 200
    task_id = res.json()["id"]

    row = test_db.get_automation_task(task_id)
    assert row is not None
    assert row["status"] == "running"
    assert row["user_id"] == "local-user"


def test_engage_endpoint_admin_bypass(client, fake_popen, clear_automation_tasks):
    res = client.post(
        "/api/linkedin-automation/engage",
        json={"engage_action": "both", "max_actions": 3, "user_id": "local-user"},
    )
    assert res.status_code == 200
    spawned = fake_popen.instances[-1]
    assert "engage" in spawned.cmd
    assert "--action" in spawned.cmd


def test_pursue_endpoint_requires_profile_name(client, fake_popen):
    res = client.post(
        "/api/linkedin-automation/pursue",
        json={"user_id": "local-user", "max_posts": 2},
    )
    # Pydantic returns 422 for missing required `profile_name`.
    assert res.status_code == 422


def test_calendar_endpoint_requires_niche(client, fake_popen):
    res = client.post(
        "/api/linkedin-automation/calendar",
        json={"user_id": "local-user", "total_posts": 5},
    )
    assert res.status_code == 422


def test_calendar_endpoint_happy_path(client, fake_popen, clear_automation_tasks):
    res = client.post(
        "/api/linkedin-automation/calendar",
        json={"niche": "fitness", "total_posts": 3, "user_id": "local-user"},
    )
    assert res.status_code == 200
    assert res.json()["action"] == "generate-calendar"
    spawned = fake_popen.instances[-1]
    assert "generate-calendar" in spawned.cmd
    assert "--niche" in spawned.cmd


# ---------------------------------------------------------------------------
# Routes: stop task
# ---------------------------------------------------------------------------


def test_stop_task_terminates_running_process(
    client, fake_popen, clear_automation_tasks
):
    start = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "to be stopped", "user_id": "local-user"},
    )
    assert start.status_code == 200
    task_id = start.json()["id"]

    stop = client.post(f"/api/linkedin-automation/tasks/{task_id}/stop")
    assert stop.status_code == 200
    body = stop.json()
    assert body["stopped"] is True
    assert body["task"]["status"] == "stopped"


def test_stop_task_404_when_unknown(client):
    res = client.post("/api/linkedin-automation/tasks/no-such-id/stop")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Routes: combined /dashboard endpoint + ETag
# ---------------------------------------------------------------------------


def test_dashboard_returns_combined_payload(client, clear_automation_tasks):
    res = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    assert res.status_code == 200
    body = res.json()
    assert {"tasks", "stats", "health", "etag"} <= set(body.keys())
    assert "ETag" in res.headers
    # Plan info threaded into stats
    assert body["stats"]["plan"] == "agency"
    assert body["stats"]["daily_used"] == body["stats"]["last_24h"]
    # Health probes the framework dir + entrypoint
    assert body["health"]["framework_available"] is True
    assert body["health"]["main_py_exists"] is True


def test_dashboard_etag_is_stable_when_nothing_changes(
    client, test_db, clear_automation_tasks
):
    test_db.create_automation_task("etag-1", "post", [], "/log", user_id="lu")
    test_db.finalize_automation_task("etag-1", exit_code=0)

    res1 = client.get("/api/linkedin-automation/dashboard?user_id=lu")
    res2 = client.get("/api/linkedin-automation/dashboard?user_id=lu")
    assert res1.headers["ETag"] == res2.headers["ETag"]
    assert res1.json()["etag"] == res2.json()["etag"]


def test_dashboard_returns_304_for_matching_if_none_match(
    client, test_db, clear_automation_tasks
):
    test_db.create_automation_task("etag-2", "post", [], "/log", user_id="lu")
    test_db.finalize_automation_task("etag-2", exit_code=0)

    first = client.get("/api/linkedin-automation/dashboard?user_id=lu")
    etag = first.headers["ETag"]

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=lu",
        headers={"If-None-Match": etag},
    )
    assert second.status_code == 304
    assert second.headers["ETag"] == etag
    # 304 body must be empty (no JSON to parse).
    assert second.content in (b"", b"null")


def test_dashboard_etag_changes_when_new_task_added(
    client, test_db, clear_automation_tasks
):
    first = client.get("/api/linkedin-automation/dashboard?user_id=lu")
    etag_before = first.headers["ETag"]

    test_db.create_automation_task("etag-3", "post", [], "/log", user_id="lu")

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=lu",
        headers={"If-None-Match": etag_before},
    )
    assert second.status_code == 200
    assert second.headers["ETag"] != etag_before


def test_dashboard_etag_changes_when_task_completes(
    client, test_db, clear_automation_tasks
):
    test_db.create_automation_task("etag-4", "post", [], "/log", user_id="lu")
    first = client.get("/api/linkedin-automation/dashboard?user_id=lu")
    etag_before = first.headers["ETag"]

    test_db.finalize_automation_task("etag-4", exit_code=0)

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=lu",
        headers={"If-None-Match": etag_before},
    )
    assert second.status_code == 200
    assert second.headers["ETag"] != etag_before


def test_dashboard_wildcard_if_none_match_returns_304(
    client, clear_automation_tasks
):
    """Standard HTTP: ``If-None-Match: *`` should also yield 304 when content exists."""
    res = client.get(
        "/api/linkedin-automation/dashboard?user_id=lu",
        headers={"If-None-Match": "*"},
    )
    assert res.status_code == 304


def test_dashboard_etag_per_user(client, test_db, clear_automation_tasks):
    """Two users with different state must get different ETags."""
    test_db.create_automation_task("u1-t1", "post", [], "/log", user_id="dashboard-u1")
    test_db.create_automation_task("u2-t1", "post", [], "/log", user_id="dashboard-u2")
    test_db.create_automation_task("u2-t2", "engage", [], "/log", user_id="dashboard-u2")

    r1 = client.get("/api/linkedin-automation/dashboard?user_id=dashboard-u1")
    r2 = client.get("/api/linkedin-automation/dashboard?user_id=dashboard-u2")
    assert r1.headers["ETag"] != r2.headers["ETag"]


# ---------------------------------------------------------------------------
# LinkedIn account discovery + per-task account capture
# ---------------------------------------------------------------------------


@pytest.fixture
def configured_accounts(test_db):
    """Plant a primary + 2 extra LinkedIn accounts in the DB secrets category."""
    test_db.set_config("username", "primary@example.com", category="secrets")
    test_db.set_config("password", "primary-pw", category="secrets")
    test_db.set_config(
        "linkedin_extra_accounts",
        [
            {"username": "alice@example.com", "password": "alice-pw"},
            {"username": "bob@example.com", "password": "bob-pw"},
        ],
        category="secrets",
    )
    yield
    # Wipe so other tests stay isolated.
    test_db.set_config("username", "", category="secrets")
    test_db.set_config("password", "", category="secrets")
    test_db.set_config("linkedin_extra_accounts", [], category="secrets")


def test_list_linkedin_accounts_returns_primary_and_extras(
    test_db, configured_accounts
):
    from services.linkedin_env import list_linkedin_accounts

    rows = list_linkedin_accounts()
    assert len(rows) == 3
    assert rows[0] == {
        "username": "primary@example.com",
        "primary": True,
        "has_password": True,
    }
    assert {r["username"] for r in rows[1:]} == {"alice@example.com", "bob@example.com"}
    for r in rows[1:]:
        assert r["primary"] is False
        assert r["has_password"] is True


def test_apply_linkedin_account_overrides_credentials(test_db, configured_accounts):
    from services.linkedin_env import apply_linkedin_account

    env: dict = {"LINKEDIN_USERNAME": "primary@example.com", "LINKEDIN_PASSWORD": "primary-pw"}
    resolved = apply_linkedin_account(env, "alice@example.com")
    assert resolved == "alice@example.com"
    assert env["LINKEDIN_USERNAME"] == "alice@example.com"
    assert env["LINKEDIN_PASSWORD"] == "alice-pw"


def test_apply_linkedin_account_is_case_insensitive(test_db, configured_accounts):
    from services.linkedin_env import apply_linkedin_account

    env: dict = {}
    resolved = apply_linkedin_account(env, "ALICE@example.COM")
    assert resolved == "alice@example.com"
    assert env["LINKEDIN_USERNAME"] == "alice@example.com"


def test_apply_linkedin_account_returns_none_for_unknown(test_db, configured_accounts):
    from services.linkedin_env import apply_linkedin_account

    env: dict = {}
    assert apply_linkedin_account(env, "noone@example.com") is None
    # env must not have been mutated when the account isn't found.
    assert "LINKEDIN_USERNAME" not in env


def test_accounts_endpoint_returns_active_and_list(client, test_db, configured_accounts):
    res = client.get("/api/linkedin-automation/accounts")
    assert res.status_code == 200
    body = res.json()
    assert body["active"] == "primary@example.com"
    usernames = [a["username"] for a in body["accounts"]]
    assert usernames == [
        "primary@example.com",
        "alice@example.com",
        "bob@example.com",
    ]


def test_dashboard_endpoint_includes_accounts(client, test_db, configured_accounts):
    res = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    assert res.status_code == 200
    body = res.json()
    assert "accounts" in body
    assert body["accounts"]["active"] == "primary@example.com"
    assert len(body["accounts"]["accounts"]) == 3


def test_post_endpoint_captures_account_on_task(
    client, fake_popen, test_db, configured_accounts, clear_automation_tasks
):
    res = client.post(
        "/api/linkedin-automation/post",
        json={
            "post_text": "Hi from Alice",
            "user_id": "local-user",
            "account": "alice@example.com",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["account_username"] == "alice@example.com"

    row = test_db.get_automation_task(body["id"])
    assert row["account_username"] == "alice@example.com"

    spawned = fake_popen.instances[-1]
    assert spawned.env["LINKEDIN_USERNAME"] == "alice@example.com"
    assert spawned.env["LINKEDIN_PASSWORD"] == "alice-pw"


def test_post_endpoint_defaults_to_primary_when_no_account(
    client, fake_popen, test_db, configured_accounts, clear_automation_tasks
):
    res = client.post(
        "/api/linkedin-automation/post",
        json={"post_text": "Hi from primary", "user_id": "local-user"},
    )
    assert res.status_code == 200
    assert res.json()["account_username"] == "primary@example.com"


def test_post_endpoint_400_for_unknown_account(
    client, fake_popen, test_db, configured_accounts, clear_automation_tasks
):
    res = client.post(
        "/api/linkedin-automation/post",
        json={
            "post_text": "x",
            "user_id": "local-user",
            "account": "missing@example.com",
        },
    )
    assert res.status_code == 400
    assert "missing@example.com" in res.json()["detail"]
    # No subprocess was spawned for the bad request.
    assert not fake_popen.instances


# ---------------------------------------------------------------------------
# Env-only accounts (loaded from .env: LINKEDIN_USERNAME_<n>)
# ---------------------------------------------------------------------------


@pytest.fixture
def env_only_accounts(test_db, monkeypatch):
    """No DB-side accounts; two env-only accounts loaded as if from .env."""
    test_db.set_config("username", "", category="secrets")
    test_db.set_config("password", "", category="secrets")
    test_db.set_config("linkedin_extra_accounts", [], category="secrets")
    monkeypatch.setenv("LINKEDIN_USERNAME_1", "envuser1@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_1", "env-pw-1")
    monkeypatch.setenv("LINKEDIN_USERNAME_2", "envuser2@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_2", "env-pw-2")
    monkeypatch.delenv("LINKEDIN_USERNAME", raising=False)
    monkeypatch.delenv("LINKEDIN_PASSWORD", raising=False)
    yield
    test_db.set_config("linkedin_extra_accounts", [], category="secrets")


def test_list_linkedin_accounts_includes_env_only_accounts(test_db, env_only_accounts):
    from services.linkedin_env import list_linkedin_accounts

    rows = list_linkedin_accounts()
    usernames = [r["username"] for r in rows]
    assert usernames == ["envuser1@example.com", "envuser2@example.com"]
    for r in rows:
        assert r["has_password"] is True
        # No DB primary, no LINKEDIN_USERNAME — neither env entry should be
        # promoted to primary just because it's index 1.
        assert r["primary"] is False


def test_accounts_endpoint_surfaces_env_only_accounts(client, test_db, env_only_accounts):
    """Regression: the billing tile + dashboard selector showed 0 even when
    the user had two LINKEDIN_USERNAME_<n> entries in their .env file."""
    res = client.get("/api/linkedin-automation/accounts")
    assert res.status_code == 200
    body = res.json()
    assert [a["username"] for a in body["accounts"]] == [
        "envuser1@example.com",
        "envuser2@example.com",
    ]


def test_apply_linkedin_account_resolves_env_only_account(test_db, env_only_accounts):
    from services.linkedin_env import apply_linkedin_account

    env = {
        "LINKEDIN_USERNAME_1": "envuser1@example.com",
        "LINKEDIN_PASSWORD_1": "env-pw-1",
        "LINKEDIN_USERNAME_2": "envuser2@example.com",
        "LINKEDIN_PASSWORD_2": "env-pw-2",
    }
    resolved = apply_linkedin_account(env, "envuser2@example.com")
    assert resolved == "envuser2@example.com"
    assert env["LINKEDIN_USERNAME"] == "envuser2@example.com"
    assert env["LINKEDIN_PASSWORD"] == "env-pw-2"


def test_db_primary_takes_precedence_over_duplicate_env_entry(
    test_db, monkeypatch
):
    """When the same username appears in both DB and env, the merged listing
    keeps the DB entry (with its primary=True flag) and drops the env dup."""
    from services.linkedin_env import list_linkedin_accounts

    test_db.set_config("username", "alice@example.com", category="secrets")
    test_db.set_config("password", "db-pw", category="secrets")
    test_db.set_config("linkedin_extra_accounts", [], category="secrets")
    monkeypatch.setenv("LINKEDIN_USERNAME_1", "alice@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_1", "env-pw")
    monkeypatch.setenv("LINKEDIN_USERNAME_2", "bob@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_2", "env-pw")

    rows = list_linkedin_accounts()
    assert [r["username"] for r in rows] == [
        "alice@example.com",
        "bob@example.com",
    ]
    assert rows[0]["primary"] is True
    assert rows[1]["primary"] is False

    # Cleanup
    test_db.set_config("username", "", category="secrets")
    test_db.set_config("password", "", category="secrets")


# ---------------------------------------------------------------------------
# Form defaults: dashboard inputs round-trip through the DB
# ---------------------------------------------------------------------------


@pytest.fixture
def clear_form_defaults(test_db):
    """Wipe ``linkedin_automation_form_defaults`` before/after each test."""
    from routes.linkedin_automation import FORM_DEFAULTS_CATEGORY

    def _wipe():
        try:
            cfg = test_db.get_all_by_category(FORM_DEFAULTS_CATEGORY) or {}
        except Exception:
            cfg = {}
        if isinstance(cfg, dict):
            for k in list(cfg.keys()):
                test_db.set_config(k, None, FORM_DEFAULTS_CATEGORY)

    _wipe()
    yield
    _wipe()


def test_form_defaults_empty_when_nothing_saved(client, clear_form_defaults):
    res = client.get("/api/linkedin-automation/form-defaults")
    assert res.status_code == 200
    assert res.json() == {}


def test_form_defaults_put_then_get_round_trip(client, clear_form_defaults):
    payload = {
        "tab": "engage",
        "selected_account": "alice@example.com",
        "engage_action": "like",
        "engage_max_actions": 12,
        "common_headless": False,
    }
    put = client.put("/api/linkedin-automation/form-defaults", json=payload)
    assert put.status_code == 200
    assert put.json()["status"] == "saved"

    got = client.get("/api/linkedin-automation/form-defaults").json()
    for k, v in payload.items():
        assert got[k] == v, f"key {k!r}: expected {v!r}, got {got.get(k)!r}"


def test_form_defaults_put_merges_partial_updates(client, clear_form_defaults):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"engage_action": "both", "engage_max_actions": 5},
    )
    # Second PUT only touches one of the two keys — the other must survive.
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"engage_max_actions": 9},
    )
    got = client.get("/api/linkedin-automation/form-defaults").json()
    assert got["engage_action"] == "both"
    assert got["engage_max_actions"] == 9


def test_form_defaults_put_none_clears_individual_key(client, clear_form_defaults):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"pursue_profile_name": "Lara", "pursue_max_posts": 8},
    )
    res = client.put(
        "/api/linkedin-automation/form-defaults",
        json={"pursue_profile_name": None},
    )
    assert res.status_code == 200
    got = client.get("/api/linkedin-automation/form-defaults").json()
    # The unset key is gone, the other stays.
    assert "pursue_profile_name" not in got
    assert got["pursue_max_posts"] == 8


def test_form_defaults_put_rejects_unknown_keys(client, clear_form_defaults):
    res = client.put(
        "/api/linkedin-automation/form-defaults",
        json={"some_random_key": "x"},
    )
    assert res.status_code == 400
    assert "some_random_key" in res.json()["detail"]


def test_form_defaults_delete_clears_all(client, clear_form_defaults):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"tab": "post", "engage_action": "like"},
    )
    res = client.delete("/api/linkedin-automation/form-defaults")
    assert res.status_code == 200
    assert res.json()["status"] == "cleared"
    assert client.get("/api/linkedin-automation/form-defaults").json() == {}


def test_form_defaults_delete_with_prefix_only_clears_matching_keys(
    client, clear_form_defaults
):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={
            "tab": "engage",
            "engage_action": "like",
            "engage_max_actions": 7,
            "calendar_niche": "fitness",
        },
    )
    res = client.delete("/api/linkedin-automation/form-defaults?prefix=engage_")
    assert res.status_code == 200
    removed = set(res.json()["removed"])
    assert removed == {"engage_action", "engage_max_actions"}

    got = client.get("/api/linkedin-automation/form-defaults").json()
    assert got == {"tab": "engage", "calendar_niche": "fitness"}


def test_dashboard_endpoint_includes_form_defaults(client, clear_form_defaults):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"tab": "post", "engage_max_actions": 11},
    )
    res = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    assert res.status_code == 200
    body = res.json()
    assert body["form_defaults"]["tab"] == "post"
    assert body["form_defaults"]["engage_max_actions"] == 11


def test_dashboard_etag_changes_when_form_defaults_change(client, clear_form_defaults):
    first = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    etag_before = first.headers["ETag"]

    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"tab": "calendar"},
    )

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=local-user",
        headers={"If-None-Match": etag_before},
    )
    # The change must bust the cached ETag — a 304 here would mean the
    # frontend is showing stale form defaults.
    assert second.status_code == 200
    assert second.headers["ETag"] != etag_before


def test_dashboard_etag_unchanged_when_form_defaults_unchanged(
    client, clear_form_defaults
):
    client.put(
        "/api/linkedin-automation/form-defaults",
        json={"engage_action": "like"},
    )
    first = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    etag = first.headers["ETag"]

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=local-user",
        headers={"If-None-Match": etag},
    )
    assert second.status_code == 304


def test_form_defaults_strips_unknown_keys_already_in_db(
    client, test_db, clear_form_defaults
):
    """Legacy / mis-injected keys must not leak through the read path."""
    from routes.linkedin_automation import FORM_DEFAULTS_CATEGORY

    test_db.set_config("legacy_key", "x", FORM_DEFAULTS_CATEGORY)
    test_db.set_config("engage_action", "comment", FORM_DEFAULTS_CATEGORY)

    got = client.get("/api/linkedin-automation/form-defaults").json()
    assert "legacy_key" not in got
    assert got["engage_action"] == "comment"


# ---------------------------------------------------------------------------
# /tasks/{id}/artifact — surface generate-calendar output to the dashboard
# ---------------------------------------------------------------------------


@pytest.fixture
def planted_calendar(test_db, tmp_path, monkeypatch):
    """Plant a fake content_calendar.txt inside a mocked framework directory."""
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))

    calendar_path = tmp_path / "content_calendar.txt"
    calendar_path.write_text(
        "Day 1: Kick-off post\nDay 2: Behind the scenes\nDay 3: Customer story\n",
        encoding="utf-8",
    )

    test_db.create_automation_task(
        "la-generate-calendar-fixture",
        "generate-calendar",
        ["generate-calendar", "--niche", "Fitness", "--total-posts", "3"],
        "/tmp/calendar.log",
        user_id="local-user",
    )
    test_db.finalize_automation_task("la-generate-calendar-fixture", exit_code=0)
    yield {"task_id": "la-generate-calendar-fixture", "path": calendar_path}


def test_artifact_returns_generated_calendar(client, planted_calendar):
    res = client.get(
        f"/api/linkedin-automation/tasks/{planted_calendar['task_id']}/artifact"
    )
    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "content_calendar.txt"
    assert body["action"] == "generate-calendar"
    assert "Day 1: Kick-off post" in body["content"]
    assert body["truncated"] is False
    assert body["size_bytes"] > 0


def test_artifact_honors_custom_output_flag(
    client, test_db, tmp_path, monkeypatch
):
    """`--output Topics.txt` should resolve relative to the framework cwd."""
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))

    (tmp_path / "Topics.txt").write_text("Hello world", encoding="utf-8")
    test_db.create_automation_task(
        "la-generate-calendar-custom",
        "generate-calendar",
        [
            "generate-calendar",
            "--niche",
            "DevOps",
            "--total-posts",
            "1",
            "--output",
            "Topics.txt",
        ],
        "/tmp/calendar.log",
        user_id="local-user",
    )
    test_db.finalize_automation_task("la-generate-calendar-custom", exit_code=0)

    res = client.get(
        "/api/linkedin-automation/tasks/la-generate-calendar-custom/artifact"
    )
    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "Topics.txt"
    assert body["content"] == "Hello world"


def test_artifact_404_for_unknown_task(client):
    res = client.get(
        "/api/linkedin-automation/tasks/la-generate-calendar-missing/artifact"
    )
    assert res.status_code == 404


def test_artifact_400_for_non_calendar_action(client, test_db):
    test_db.create_automation_task(
        "la-post-no-artifact",
        "post",
        ["post", "--post-text", "Hi"],
        "/tmp/post.log",
        user_id="local-user",
    )
    test_db.finalize_automation_task("la-post-no-artifact", exit_code=0)

    res = client.get("/api/linkedin-automation/tasks/la-post-no-artifact/artifact")
    assert res.status_code == 400
    assert "post" in res.json()["detail"]


def test_artifact_404_when_calendar_file_missing(
    client, test_db, tmp_path, monkeypatch
):
    """Task exists, action matches, but the file was deleted or never written."""
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))

    test_db.create_automation_task(
        "la-generate-calendar-empty",
        "generate-calendar",
        ["generate-calendar", "--niche", "AI", "--total-posts", "1"],
        "/tmp/calendar.log",
        user_id="local-user",
    )
    test_db.finalize_automation_task("la-generate-calendar-empty", exit_code=0)

    res = client.get(
        "/api/linkedin-automation/tasks/la-generate-calendar-empty/artifact"
    )
    assert res.status_code == 404


def test_artifact_rejects_path_traversal(
    client, test_db, tmp_path, monkeypatch
):
    """`--output ../escape.txt` must not leak files outside the framework dir."""
    from services import linkedin_automation as la_service

    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(framework_dir))

    # Sibling file the attacker would target — exists, but outside framework.
    escape = tmp_path / "escape.txt"
    escape.write_text("secret", encoding="utf-8")

    test_db.create_automation_task(
        "la-generate-calendar-traversal",
        "generate-calendar",
        [
            "generate-calendar",
            "--niche",
            "Evil",
            "--total-posts",
            "1",
            "--output",
            "../escape.txt",
        ],
        "/tmp/calendar.log",
        user_id="local-user",
    )
    test_db.finalize_automation_task("la-generate-calendar-traversal", exit_code=0)

    res = client.get(
        "/api/linkedin-automation/tasks/la-generate-calendar-traversal/artifact"
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# /calendar — direct read of the framework's content_calendar.txt
# ---------------------------------------------------------------------------


def test_calendar_endpoint_returns_default_file(client, tmp_path, monkeypatch):
    """`GET /calendar` reads `content_calendar.txt` from the framework dir."""
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))
    (tmp_path / "content_calendar.txt").write_text(
        "Day 1: Hello\nDay 2: World\n", encoding="utf-8"
    )

    res = client.get("/api/linkedin-automation/calendar")
    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "content_calendar.txt"
    assert "Day 1: Hello" in body["content"]
    assert body["truncated"] is False
    assert isinstance(body["mtime"], (int, float))


def test_calendar_endpoint_honors_file_query(client, tmp_path, monkeypatch):
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))
    (tmp_path / "Topics.txt").write_text("custom output", encoding="utf-8")

    res = client.get("/api/linkedin-automation/calendar?file=Topics.txt")
    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "Topics.txt"
    assert body["content"] == "custom output"


def test_calendar_endpoint_404_when_missing(client, tmp_path, monkeypatch):
    from services import linkedin_automation as la_service

    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(tmp_path))
    res = client.get("/api/linkedin-automation/calendar")
    assert res.status_code == 404


def test_calendar_endpoint_rejects_path_traversal(client, tmp_path, monkeypatch):
    from services import linkedin_automation as la_service

    framework_dir = tmp_path / "framework"
    framework_dir.mkdir()
    monkeypatch.setattr(la_service, "get_framework_dir", lambda: str(framework_dir))

    (tmp_path / "secret.txt").write_text("leak", encoding="utf-8")
    res = client.get(
        "/api/linkedin-automation/calendar?file=" + "../secret.txt"
    )
    assert res.status_code == 403


def test_dashboard_etag_changes_when_accounts_change(
    client, test_db, configured_accounts
):
    first = client.get("/api/linkedin-automation/dashboard?user_id=local-user")
    etag_before = first.headers["ETag"]

    # Add a new extra account and re-check.
    test_db.set_config(
        "linkedin_extra_accounts",
        [
            {"username": "alice@example.com", "password": "alice-pw"},
            {"username": "bob@example.com", "password": "bob-pw"},
            {"username": "charlie@example.com", "password": "charlie-pw"},
        ],
        category="secrets",
    )

    second = client.get(
        "/api/linkedin-automation/dashboard?user_id=local-user",
        headers={"If-None-Match": etag_before},
    )
    assert second.status_code == 200
    assert second.headers["ETag"] != etag_before
