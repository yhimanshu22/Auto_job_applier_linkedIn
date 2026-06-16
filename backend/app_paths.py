"""Resolved backend install / bundle paths (same semantics as legacy server.get_base_path)."""

import os
import sys


def get_base_path() -> str:
    """Install / bundle root (read-only under Program Files when packaged)."""
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
        if os.path.basename(base_path) == "dist":
            return os.path.dirname(base_path)
        return base_path
    return os.path.dirname(os.path.abspath(__file__))


def _ensure_packaged_runtime_subdirs(root: str) -> None:
    """CSV / uploads / Chrome expect these folders relative to the bot cwd."""
    for sub in ("logs", "all excels", "all resumes", "chrome_profiles", "cookies"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)


def get_runtime_writable_root() -> str:
    """
    Writable root for DB, logs, uploads, chrome_profiles, bot working directory.
    Set LINKDAPPLY_USER_DATA to override the writable data directory; otherwise uses the backend folder.
    """
    override = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
    if override:
        os.makedirs(override, exist_ok=True)
        _ensure_packaged_runtime_subdirs(override)
        return override
    return get_base_path()


def get_logs_dir() -> str:
    """Logs under writable root (required when installed under Program Files)."""
    log_dir = os.path.join(get_runtime_writable_root(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_config_path(filename: str) -> str:
    """Bundled config templates (read-only in production installs)."""
    return os.path.join(get_base_path(), "config", filename)


def get_bundled_framework_dir() -> str:
    """Read-only automation bundle (PyInstaller ``_MEIPASS`` or source tree)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return os.path.join(meipass, "linkedin_automation")
    return os.path.join(get_base_path(), "linkedin_automation")


def _seed_framework_workspace(workspace: str) -> None:
    """Copy default topics/calendar templates into the writable workspace once."""
    bundled = get_bundled_framework_dir()
    if not os.path.isdir(bundled):
        return
    import shutil

    for name in ("topics.txt", "content_calendar.txt"):
        dest = os.path.join(workspace, name)
        if os.path.isfile(dest):
            continue
        src = os.path.join(bundled, name)
        if os.path.isfile(src):
            try:
                shutil.copy2(src, dest)
            except OSError:
                pass


def get_framework_workspace_dir() -> str:
    """
    Writable cwd for automation subprocesses (generated topics, calendar files).

    Dev servers without ``LINKDAPPLY_USER_DATA`` use the source package tree.
    Packaged desktop installs use ``%APPDATA%/LinkdApply/linkedin_automation``.
    """
    if getattr(sys, "frozen", False) or os.getenv("LINKDAPPLY_USER_DATA", "").strip():
        workspace = os.path.join(get_runtime_writable_root(), "linkedin_automation")
        os.makedirs(workspace, exist_ok=True)
        _seed_framework_workspace(workspace)
        return workspace
    return os.path.join(get_base_path(), "linkedin_automation")


# Secrets the packaged desktop app must share with supervisor/bot subprocesses.
_RUNTIME_SECRET_KEYS = (
    "ENCRYPTION_KEY",
    "LLM_API_KEY",
    "LLM_API_URL",
    "LLM_MODEL",
    "LLM_SPEC",
    "AI_PROVIDER",
    "USE_AI",
)


def _parse_env_file(path: str) -> dict[str, str]:
    """Read KEY=value lines from a dotenv file (no interpolation)."""
    out: dict[str, str] = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if key:
                out[key] = value.strip().strip("'\"")
    return out


def load_env_files() -> None:
    """Load backend/.env then optional ``LINKDAPPLY_USER_DATA/.env`` override."""
    from dotenv import load_dotenv

    backend = get_base_path()
    load_dotenv(os.path.join(backend, ".env"))
    user_data = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
    if user_data:
        load_dotenv(os.path.join(user_data, ".env"), override=True)


def persist_runtime_secrets_to_user_env() -> bool:
    """
    Copy critical secrets from the current process env into ``LINKDAPPLY_USER_DATA/.env``.

    Packaged installs run the API and bot from ``%APPDATA%\\LinkdApply`` but only load
    secrets from that folder's ``.env``. Dev machines often keep keys in ``backend/.env``
    instead — this bridges them so bot workers can decrypt DB secrets and call the LLM.
    """
    user_data = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
    if not user_data:
        return False

    env_path = os.path.join(user_data, ".env")
    on_disk = _parse_env_file(env_path)
    additions: list[str] = []
    for key in _RUNTIME_SECRET_KEYS:
        value = os.getenv(key, "").strip()
        if not value:
            continue
        if on_disk.get(key) == value:
            continue
        if on_disk.get(key):
            continue
        additions.append(f"{key}={value}")

    if not additions:
        return False

    os.makedirs(user_data, exist_ok=True)
    header = (
        "# Auto-synced from backend/.env — required for bot workers in the packaged app.\n"
        if not os.path.isfile(env_path)
        else ""
    )
    with open(env_path, "a", encoding="utf-8") as fh:
        if header:
            fh.write(header)
        fh.write("\n".join(additions))
        fh.write("\n")
    return True


def subprocess_env(base: dict | None = None) -> dict[str, str]:
    """Env for supervisor/bot child processes (PYTHONPATH + dotenv secrets)."""
    load_env_files()
    env = dict(base or os.environ)
    for key, value in os.environ.items():
        env[key] = value

    backend = get_base_path()
    config_dir = os.path.join(backend, "config")
    parts: list[str] = [backend, config_dir]
    existing = env.get("PYTHONPATH", "")
    if existing:
        for part in existing.split(os.pathsep):
            if part and part not in parts:
                parts.append(part)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env
