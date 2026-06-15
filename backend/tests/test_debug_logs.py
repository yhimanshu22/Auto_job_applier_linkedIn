import os

import pytest

from utils.debug_logs import (
    API_LOG,
    SUPERVISOR_LOG,
    bot_log_path,
    collect_bot_logs_payload,
    logs_dir,
    run_has_logs,
    run_logs_dir,
    scoped_log_path,
    tail_file,
)


def test_logs_dir_is_under_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    assert logs_dir() == str(tmp_path / "logs")
    assert os.path.isdir(logs_dir())


def test_bot_log_paths_use_run_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    monkeypatch.setenv("BOT_RUN_ID", "42")
    assert bot_log_path("main").endswith(
        os.path.join("logs", "runs", "42", "bot-main.txt")
    )
    assert scoped_log_path(SUPERVISOR_LOG).endswith(
        os.path.join("logs", "runs", "42", SUPERVISOR_LOG)
    )


def test_tail_file_returns_last_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    path = os.path.join(logs_dir(), API_LOG)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(f"line-{i}" for i in range(1, 6)))
    text = tail_file(path, lines=2)
    assert "line-4" in text
    assert "line-5" in text
    assert "line-1" not in text


def test_collect_run_scoped_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    run_dir = run_logs_dir(7)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, SUPERVISOR_LOG), "w", encoding="utf-8") as f:
        f.write("supervisor run 7\n")
    with open(os.path.join(run_dir, "bot-1.txt"), "w", encoding="utf-8") as f:
        f.write("applied job\n")

    payload = collect_bot_logs_payload(lines=50, run_id=7)
    assert payload["run_id"] == 7
    assert payload["log_dir"] == run_dir
    assert "supervisor run 7" in payload["logs"]
    assert any(p["id"] == "1" for p in payload["profiles"])
    assert run_has_logs(7)


def test_collect_bot_logs_payload_legacy_root(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    with open(os.path.join(logs_dir(), API_LOG), "w", encoding="utf-8") as f:
        f.write("api started\n")
    with open(os.path.join(logs_dir(), SUPERVISOR_LOG), "w", encoding="utf-8") as f:
        f.write("supervisor ready\n")
    with open(os.path.join(logs_dir(), "bot-1.txt"), "w", encoding="utf-8") as f:
        f.write("applied job\n")

    payload = collect_bot_logs_payload(lines=50)
    assert payload["log_dir"] == logs_dir()
    assert "api started" in payload["logs"]
    assert "supervisor ready" in payload["logs"]
    assert any(p["id"] == "1" for p in payload["profiles"])


def test_collect_bot_logs_empty_message(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    payload = collect_bot_logs_payload()
    assert payload["infra"] == []
    assert "No log files yet" in payload["logs"]
    assert payload["log_dir"] in payload["logs"]
