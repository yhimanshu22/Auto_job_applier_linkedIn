#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

kill_pid() {
  local pid=$1
  [ -n "$pid" ] && [ "$pid" != "0" ] || return 0
  if command -v taskkill >/dev/null 2>&1; then
    taskkill //PID "$pid" //F >/dev/null 2>&1 || kill -9 "$pid" 2>/dev/null || true
  else
    kill -9 "$pid" 2>/dev/null || true
  fi
}

kill_port() {
  local port=$1
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
  elif command -v netstat >/dev/null 2>&1; then
    pids=$(netstat -ano 2>/dev/null | grep -E ":${port}[[:space:]]" | awk '{print $NF}' | sort -u | grep -E '^[0-9]+$' || true)
  fi

  if [ -z "$pids" ]; then
    return 0
  fi

  echo "Stopping process(es) on port ${port} ..."
  for pid in $pids; do
    kill_pid "$pid"
  done
  sleep 1
}

ensure_frontend_env() {
  local env_file="$ROOT/frontend/.env.local"
  local template="$ROOT/frontend/.env.local.template"

  [ -f "$template" ] || return 0

  if [ ! -f "$env_file" ]; then
    echo "Creating frontend/.env.local from .env.local.template ..."
    cp "$template" "$env_file"
    return 0
  fi

  if ! grep -qE '^GOOGLE_CLIENT_ID=.+' "$env_file" 2>/dev/null; then
    echo "frontend/.env.local is missing Google OAuth credentials; restoring from .env.local.template ..."
    cp "$template" "$env_file"
  fi
}

clear_next_dev_lock() {
  local lock_file="$ROOT/frontend/.next/dev/lock"
  [ -f "$lock_file" ] || return 0

  local lock_pid
  lock_pid=$(sed -n 's/.*"pid":\([0-9]*\).*/\1/p' "$lock_file" 2>/dev/null || true)
  if [ -n "$lock_pid" ]; then
    echo "Stopping existing Next.js dev server (PID ${lock_pid}) ..."
    kill_pid "$lock_pid"
    sleep 1
  fi
  rm -f "$lock_file"
}

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

kill_port "$BACKEND_PORT"

cd "$ROOT/backend"
unset VIRTUAL_ENV
echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT} ..."
# `uv run uvicorn` fails on Windows ("Failed to canonicalize script path"); -m works.
uv run python -m uvicorn server:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACKEND_PID=$!
sleep 1
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Backend failed to start. Run manually: cd backend && uv run python -m uvicorn server:app"
  exit 1
fi

ensure_frontend_env
clear_next_dev_lock
kill_port "$FRONTEND_PORT"
rm -rf "$ROOT/frontend/.next/dev"

cd "$ROOT/frontend"
echo "Starting frontend on http://localhost:${FRONTEND_PORT} ..."
npm run dev &
FRONTEND_PID=$!

wait
