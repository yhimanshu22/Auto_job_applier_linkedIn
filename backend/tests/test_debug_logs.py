import os

import pytest

from utils.debug_logs import (
    API_LOG,
    LEGACY_BOT_LOG,
    SUPERVISOR_LOG,
    bot_log_path,
    collect_bot_logs_payload,
    log_file_path,
    logs_dir,
    tail_file,
)


def test_logs_dir_is_under_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    assert logs_dir() == str(tmp_path / "logs")
    assert os.path.isdir(logs_dir())


def test_bot_log_paths_use_txt(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    assert bot_log_path("main").endswith(os.path.join("logs", "bot-main.txt"))


def test_tail_file_returns_last_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    path = log_file_path(API_LOG)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(f"line-{i}" for i in range(1, 6)))
    text = tail_file(path, lines=2)
    assert "line-4" in text
    assert "line-5" in text
    assert "line-1" not in text


def test_collect_bot_logs_payload_includes_api_and_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    with open(log_file_path(API_LOG), "w", encoding="utf-8") as f:
        f.write("api started\n")
    with open(log_file_path(SUPERVISOR_LOG), "w", encoding="utf-8") as f:
        f.write("supervisor ready\n")
    with open(bot_log_path("1"), "w", encoding="utf-8") as f:
        f.write("applied job\n")

    payload = collect_bot_logs_payload(lines=50)
    assert payload["log_dir"] == logs_dir()
    assert any(f["filename"] == API_LOG for f in payload["files"])
    assert "api started" in payload["logs"]
    assert "supervisor ready" in payload["logs"]
    assert any(p["id"] == "1" for p in payload["profiles"])


def test_collect_bot_logs_empty_message(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    payload = collect_bot_logs_payload()
    assert payload["infra"] == []
    assert "No log files yet" in payload["logs"]
    assert payload["log_dir"] in payload["logs"]


def test_legacy_log_txt_included(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    with open(log_file_path(LEGACY_BOT_LOG), "w", encoding="utf-8") as f:
        f.write("legacy line\n")
    payload = collect_bot_logs_payload()
    assert "legacy line" in payload["logs"]
