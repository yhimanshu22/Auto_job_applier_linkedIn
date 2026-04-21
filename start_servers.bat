@echo off
echo ========================================================
echo Starting Auto Job Applier (Premium Web UI)
echo ========================================================

echo [1/2] Starting Backend API Server...
cd backend
start cmd /k "uv run uvicorn server:app --host 0.0.0.0 --port 8000"

echo [2/2] Starting Next.js Frontend Dashboard...
cd ../frontend
start cmd /k "npm run dev"

echo ========================================================
echo Both servers have been spun up in new windows!
echo Please open your browser to http://localhost:3000
echo ========================================================
