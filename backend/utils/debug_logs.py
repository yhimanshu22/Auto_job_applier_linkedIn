"""
Plain-text debug logs under backend/logs/ (local dev and AWS EC2).

Files (all .txt):
  api.txt                 — FastAPI / uvicorn server
  supervisor.txt          — supervisor process (structured logging)
  supervisor-console.txt  — supervisor stdout/stderr
  bot-<id>.txt            — job-applier application log (print_lg)
  bot-<id>-console.txt    — job-applier subprocess stdout/stderr
  log.txt                 — legacy single-bot log when BOT_ID is unset

Legacy .log names are still read if present from older runs.
"""

from __future__ import annotations

import glob
import logging
import os
from datetime import datetime, timezone
from typing import Iterable

from app_paths import get_logs_dir

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

API_LOG = "api.txt"
SUPERVISOR_LOG = "supervisor.txt"
SUPERVISOR_CONSOLE_LOG = "supervisor-console.txt"
LEGACY_BOT_LOG = "log.txt"
BOT_LOG_GLOB = "bot-*.txt"

_LEGACY_READ_ALIASES: dict[str, tuple[str, ...]] = {
    SUPERVISOR_LOG: ("supervisor.log",),
    SUPERVISOR_CONSOLE_LOG: ("supervisor-console.log",),
}

_configured: set[str] = set()


def logs_dir() -> str:
    path = get_logs_dir()
    os.makedirs(path, exist_ok=True)
    return path


def log_file_path(basename: str) -> str:
    return os.path.join(logs_dir(), basename)


def safe_bot_id(bot_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in bot_id)


def bot_log_path(bot_id: str) -> str:
    return log_file_path(f"bot-{safe_bot_id(bot_id)}.txt")


def bot_console_path(bot_id: str) -> str:
    return log_file_path(f"bot-{safe_bot_id(bot_id)}-console.txt")


def resolve_readable_path(basename: str) -> str:
    """Prefer canonical .txt; fall back to legacy .log if that is all that exists."""
    primary = log_file_path(basename)
    if os.path.isfile(primary):
        return primary
    for legacy in _LEGACY_READ_ALIASES.get(basename, ()):
        alt = log_file_path(legacy)
        if os.path.isfile(alt):
            return alt
    return primary


def append_session_marker(path: str, label: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n[{ts}] {label}\n{'=' * 60}\n")
        f.flush()


def configure_file_logger(
    name: str,
    filename: str,
    *,
    level: str | None = None,
    also_stdout: bool = True,
) -> logging.Logger:
    """Attach a UTF-8 .txt file handler once per logger name."""
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if name in _configured:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    path = log_file_path(filename)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if also_stdout and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(log_level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.propagate = False
    _configured.add(name)
    return logger


def configure_api_logging() -> logging.Logger:
    """Log API server events to logs/api.txt (local and AWS)."""
    logger = configure_file_logger("linkdapply.api", API_LOG)
    path = log_file_path(API_LOG)

    root = logging.getLogger()
    root.setLevel(logger.level)
    if not any(
        isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", None) == os.path.abspath(path)
        for h in root.handlers
    ):
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                root.addHandler(handler)
                break

    for uvicorn_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uvicorn_name)
        uv_logger.setLevel(logger.level)
        for handler in logger.handlers:
            if handler not in uv_logger.handlers:
                uv_logger.addHandler(handler)
    return logger


def tail_file(path: str, lines: int = 120) -> str:
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            buf = f.readlines()
        return "".join(buf[-lines:])
    except Exception as ex:
        return f"(read error: {ex})"


def list_log_files() -> list[dict]:
    """Metadata for every .txt log in logs/ (for debugging dashboards and SSH)."""
    out: list[dict] = []
    for path in sorted(glob.glob(os.path.join(logs_dir(), "*.txt"))):
        try:
            st = os.stat(path)
            out.append(
                {
                    "filename": os.path.basename(path),
                    "path": path,
                    "size_bytes": st.st_size,
                    "modified_utc": datetime.fromtimestamp(
                        st.st_mtime, tz=timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
        except OSError:
            continue
    return out


def _profile_id_from_filename(filename: str) -> str | None:
    if not filename.startswith("bot-") or not filename.endswith(".txt"):
        return None
    inner = filename[len("bot-") : -len(".txt")]
    if inner.endswith("-console"):
        return None
    return inner


def collect_bot_logs_payload(*, lines: int = 120) -> dict:
    """Build the /api/bot/logs response from canonical .txt files."""
    lines = max(20, min(int(lines), 500))
    log_dir = logs_dir()

    infra_specs: Iterable[tuple[str, str]] = (
        ("API server", API_LOG),
        ("Supervisor console (stdout/stderr)", SUPERVISOR_CONSOLE_LOG),
        ("Supervisor", SUPERVISOR_LOG),
    )

    infra: list[dict] = []
    infra_text_parts: list[str] = []
    for title, basename in infra_specs:
        path = resolve_readable_path(basename)
        chunk = tail_file(path, lines).strip()
        filename = os.path.basename(path)
        if chunk or os.path.isfile(path):
            infra.append({"title": title, "filename": filename, "content": chunk})
        if chunk:
            infra_text_parts.append(f"--- {title} ({filename}) ---\n{chunk}")

    profiles: list[dict] = []
    profile_text_parts: list[str] = []
    seen_ids: set[str] = set()

    for path in sorted(glob.glob(os.path.join(log_dir, BOT_LOG_GLOB))):
        basename = os.path.basename(path)
        profile_id = _profile_id_from_filename(basename)
        if not profile_id or profile_id in seen_ids:
            continue
        seen_ids.add(profile_id)
        chunk = tail_file(path, lines).strip()
        profiles.append({"id": profile_id, "filename": basename, "content": chunk})
        if chunk:
            profile_text_parts.append(
                f"--- Bot profile {profile_id} ({basename}) ---\n{chunk}"
            )

        console_path = bot_console_path(profile_id)
        legacy_console = log_file_path(
            f"bot-{safe_bot_id(profile_id)}-stdout.log"
        )
        console_read = console_path if os.path.isfile(console_path) else legacy_console
        if os.path.isfile(console_read):
            console_chunk = tail_file(console_read, lines).strip()
            console_name = os.path.basename(console_read)
            if console_chunk:
                infra.append(
                    {
                        "title": f"Bot {profile_id} console",
                        "filename": console_name,
                        "content": console_chunk,
                    }
                )
                infra_text_parts.append(
                    f"--- Bot {profile_id} console ({console_name}) ---\n{console_chunk}"
                )

    legacy_path = log_file_path(LEGACY_BOT_LOG)
    if os.path.isfile(legacy_path):
        chunk = tail_file(legacy_path, lines).strip()
        if chunk:
            infra.append(
                {
                    "title": "Legacy bot log",
                    "filename": LEGACY_BOT_LOG,
                    "content": chunk,
                }
            )
            infra_text_parts.append(f"--- Legacy bot log ({LEGACY_BOT_LOG}) ---\n{chunk}")

    legacy_parts = infra_text_parts + profile_text_parts
    if not legacy_parts:
        msg = (
            "No log files yet. Start the bot from the dashboard to capture supervisor output "
            f"under {log_dir}/ (api.txt, supervisor.txt, bot-<id>.txt)."
        )
        return {
            "log_dir": log_dir,
            "files": list_log_files(),
            "logs": msg,
            "infra": [],
            "profiles": [],
        }

    return {
        "log_dir": log_dir,
        "files": list_log_files(),
        "logs": "\n".join(legacy_parts),
        "infra": infra,
        "profiles": profiles,
    }
