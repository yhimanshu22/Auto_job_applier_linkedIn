"""
Plain-text debug logs under backend/logs/ (local dev and desktop sidecar).

Layout:
  api.txt                    — FastAPI / uvicorn (always at logs root)
  log.txt                    — legacy single-bot log when BOT_ID is unset
  runs/<bot_run_id>/         — one folder per dashboard bot start (BOT_RUN_ID)
    supervisor.txt
    supervisor-console.txt
    bot-<account_id>.txt
    bot-<account_id>-console.txt

Legacy flat bot-<id>.txt at logs root are still read when no run folder exists.
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
RUNS_SUBDIR = "runs"

_LEGACY_READ_ALIASES: dict[str, tuple[str, ...]] = {
    SUPERVISOR_LOG: ("supervisor.log",),
    SUPERVISOR_CONSOLE_LOG: ("supervisor-console.log",),
}

_configured: set[str] = set()


def logs_dir() -> str:
    path = get_logs_dir()
    os.makedirs(path, exist_ok=True)
    return path


def bot_run_id() -> str | None:
    rid = (os.getenv("BOT_RUN_ID") or "").strip()
    return rid or None


def run_logs_dir(run_id: int | str) -> str:
    return os.path.join(logs_dir(), RUNS_SUBDIR, str(run_id).strip())


def scoped_logs_base() -> str:
    """Active write directory: runs/<BOT_RUN_ID>/ when set, else logs root."""
    rid = bot_run_id()
    if rid:
        base = run_logs_dir(rid)
        os.makedirs(base, exist_ok=True)
        return base
    return logs_dir()


def scoped_log_path(basename: str) -> str:
    return os.path.join(scoped_logs_base(), basename)


def log_file_path(basename: str) -> str:
    """Root logs path (api.txt). Bot/supervisor paths should use scoped_log_path."""
    return os.path.join(logs_dir(), basename)


def safe_bot_id(bot_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in bot_id)


def bot_log_path(bot_id: str) -> str:
    return scoped_log_path(f"bot-{safe_bot_id(bot_id)}.txt")


def bot_console_path(bot_id: str) -> str:
    return scoped_log_path(f"bot-{safe_bot_id(bot_id)}-console.txt")


def run_has_logs(run_id: int | str) -> bool:
    d = run_logs_dir(run_id)
    if not os.path.isdir(d):
        return False
    try:
        return any(name.endswith(".txt") for name in os.listdir(d))
    except OSError:
        return False


def latest_run_logs_dir() -> str | None:
    runs_root = os.path.join(logs_dir(), RUNS_SUBDIR)
    if not os.path.isdir(runs_root):
        return None
    best_id: int | None = None
    best_path: str | None = None
    for name in os.listdir(runs_root):
        path = os.path.join(runs_root, name)
        if not os.path.isdir(path):
            continue
        try:
            rid = int(name)
        except ValueError:
            continue
        if best_id is None or rid > best_id:
            best_id = rid
            best_path = path
    return best_path


def resolve_readable_path(basename: str, *, base_dir: str | None = None) -> str:
    """Prefer canonical .txt; fall back to legacy .log if that is all that exists."""
    root = base_dir or logs_dir()
    primary = os.path.join(root, basename)
    if os.path.isfile(primary):
        return primary
    for legacy in _LEGACY_READ_ALIASES.get(basename, ()):
        alt = os.path.join(root, legacy)
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
    path = scoped_log_path(filename) if filename != API_LOG else log_file_path(filename)
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


def list_log_files(*, base_dir: str | None = None) -> list[dict]:
    """Metadata for .txt logs under base_dir (default: logs root + all run folders)."""
    out: list[dict] = []

    def _scan(directory: str, prefix: str = "") -> None:
        pattern = os.path.join(directory, "*.txt")
        for path in sorted(glob.glob(pattern)):
            try:
                st = os.stat(path)
                name = os.path.basename(path)
                out.append(
                    {
                        "filename": f"{prefix}{name}" if prefix else name,
                        "path": path,
                        "size_bytes": st.st_size,
                        "modified_utc": datetime.fromtimestamp(
                            st.st_mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )
            except OSError:
                continue

    if base_dir:
        _scan(base_dir)
        return out

    _scan(logs_dir())
    runs_root = os.path.join(logs_dir(), RUNS_SUBDIR)
    if os.path.isdir(runs_root):
        for run_name in sorted(os.listdir(runs_root), reverse=True):
            run_path = os.path.join(runs_root, run_name)
            if os.path.isdir(run_path):
                _scan(run_path, prefix=f"runs/{run_name}/")
    return out


def _profile_id_from_filename(filename: str) -> str | None:
    if not filename.startswith("bot-") or not filename.endswith(".txt"):
        return None
    inner = filename[len("bot-") : -len(".txt")]
    if inner.endswith("-console"):
        return None
    return inner


def _collect_from_directory(
    log_dir: str,
    *,
    lines: int,
    include_api: bool = True,
) -> dict:
    infra_specs: Iterable[tuple[str, str]] = (
        ("Supervisor console (stdout/stderr)", SUPERVISOR_CONSOLE_LOG),
        ("Supervisor", SUPERVISOR_LOG),
    )

    infra: list[dict] = []
    infra_text_parts: list[str] = []

    if include_api:
        api_path = resolve_readable_path(API_LOG, base_dir=logs_dir())
        api_chunk = tail_file(api_path, lines).strip()
        if api_chunk or os.path.isfile(api_path):
            infra.append(
                {
                    "title": "API server",
                    "filename": os.path.basename(api_path),
                    "content": api_chunk,
                }
            )
        if api_chunk:
            infra_text_parts.append(
                f"--- API server ({os.path.basename(api_path)}) ---\n{api_chunk}"
            )

    for title, basename in infra_specs:
        path = resolve_readable_path(basename, base_dir=log_dir)
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

        console_path = os.path.join(log_dir, f"bot-{safe_bot_id(profile_id)}-console.txt")
        legacy_console = os.path.join(log_dir, f"bot-{safe_bot_id(profile_id)}-stdout.log")
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

    legacy_parts = infra_text_parts + profile_text_parts
    run_id = os.path.basename(log_dir.rstrip("/\\"))
    if not legacy_parts:
        msg = (
            f"No log files yet for run {run_id}. "
            f"Expected files under {log_dir}/"
        )
        return {
            "log_dir": log_dir,
            "run_id": int(run_id) if run_id.isdigit() else run_id,
            "files": list_log_files(base_dir=log_dir),
            "logs": msg,
            "infra": [],
            "profiles": [],
        }

    return {
        "log_dir": log_dir,
        "run_id": int(run_id) if run_id.isdigit() else run_id,
        "files": list_log_files(base_dir=log_dir),
        "logs": "\n".join(legacy_parts),
        "infra": infra,
        "profiles": profiles,
    }


def _collect_legacy_root(*, lines: int) -> dict:
    """Pre-run-scoping layout: flat files under logs/."""
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
        if not os.path.isfile(console_path):
            console_path = log_file_path(f"bot-{safe_bot_id(profile_id)}-stdout.log")
        if os.path.isfile(console_path):
            console_chunk = tail_file(console_path, lines).strip()
            if console_chunk:
                console_name = os.path.basename(console_path)
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
            f"under {log_dir}/runs/<run_id>/ (or legacy flat files at logs root)."
        )
        return {
            "log_dir": log_dir,
            "run_id": None,
            "files": list_log_files(),
            "logs": msg,
            "infra": [],
            "profiles": [],
        }

    return {
        "log_dir": log_dir,
        "run_id": None,
        "files": list_log_files(),
        "logs": "\n".join(legacy_parts),
        "infra": infra,
        "profiles": profiles,
    }


def collect_bot_logs_payload(*, lines: int = 120, run_id: int | str | None = None) -> dict:
    """Build the /api/bot/logs response from run-scoped or legacy log files."""
    lines = max(20, min(int(lines), 500))

    if run_id is not None and str(run_id).strip():
        run_dir = run_logs_dir(run_id)
        if os.path.isdir(run_dir):
            return _collect_from_directory(run_dir, lines=lines)
        os.makedirs(run_dir, exist_ok=True)
        return _collect_from_directory(run_dir, lines=lines)

    latest = latest_run_logs_dir()
    if latest:
        return _collect_from_directory(latest, lines=lines)

    return _collect_legacy_root(lines=lines)
