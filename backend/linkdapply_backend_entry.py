"""PyInstaller entrypoint for the LinkdApply Tauri desktop sidecar."""

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_BACKEND_DIR, "config")
for _path in (_CONFIG_DIR, _BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))
_user_data = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
if _user_data:
    load_dotenv(os.path.join(_user_data, ".env"), override=True)

if getattr(sys, "frozen", False):
    from app_paths import get_runtime_writable_root

    os.chdir(get_runtime_writable_root())

import uvicorn  # noqa: E402

from server import app  # noqa: E402


def main() -> None:
    """CLI modes for the packaged sidecar (API server, supervisor, bot worker)."""
    if "--bot" in sys.argv:
        from runAiBot import main as bot_main

        bot_main()
        return
    if "--supervisor" in sys.argv:
        from supervisor import main as supervisor_main

        supervisor_main()
        return

    host = os.getenv("LINKDAPPLY_API_HOST", "127.0.0.1")
    port = int(os.getenv("LINKDAPPLY_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
