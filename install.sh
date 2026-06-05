#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/yhimanshu22/Auto_job_applier_linkedIn.git}"
REPO_DIR="${REPO_DIR:-Auto_job_applier_linkedIn}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing dependency: $1"
    exit 1
  }
}

require_cmd git
require_cmd python
require_cmd npm

if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"

# Backend
cd backend
python -m pip install -U uv >/dev/null
uv sync

# Ensure a .env exists (user can fill it later)
if [ ! -f ".env" ] && [ -f "linkedin_automation/.env.example" ]; then
  cp "linkedin_automation/.env.example" ".env"
fi
if [ ! -f "linkedin_automation/.env" ] && [ -f "linkedin_automation/.env.example" ]; then
  cp "linkedin_automation/.env.example" "linkedin_automation/.env"
fi

echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT} ..."
nohup uv run uvicorn server:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" > backend.log 2>&1 &

# Frontend
cd ../frontend
npm install

echo "Starting frontend on http://localhost:3000 ..."
exec npm run dev

