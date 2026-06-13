"""PyInstaller entrypoint for the LinkdApply Tauri desktop sidecar."""

import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

from dotenv import load_dotenv

load_dotenv()
_user_data = os.getenv("LINKDAPPLY_USER_DATA", "").strip()
if _user_data:
    load_dotenv(os.path.join(_user_data, ".env"), override=True)

import uvicorn  # noqa: E402

from server import app  # noqa: E402

if __name__ == "__main__":
    host = os.getenv("LINKDAPPLY_API_HOST", "127.0.0.1")
    port = int(os.getenv("LINKDAPPLY_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")
