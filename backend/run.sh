#!/usr/bin/env bash
# Run the API using backend/.venv (uv project). Clears a parent-repo VIRTUAL_ENV
# so uv does not warn about a mismatched active environment.
set -euo pipefail
cd "$(dirname "$0")"
unset VIRTUAL_ENV
exec uv run uvicorn server:app --host "${BACKEND_HOST:-127.0.0.1}" --port "${BACKEND_PORT:-8000}" "$@"
