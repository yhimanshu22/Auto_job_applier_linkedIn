@echo off
setlocal
cd /d "%~dp0"

set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo ========================================================
echo Starting Auto Job Applier (Premium Web UI + Supervisor)
echo ========================================================
echo Log directory: %LOGDIR%
echo.

echo [1/3] Starting Backend API Server...
start "LinkdApply API" /D "%~dp0backend" powershell -NoExit -Command "uv run uvicorn server:app --host 0.0.0.0 --port 8000 *>&1 | Tee-Object -FilePath '%LOGDIR%\api.log' -Append"

echo [2/3] Starting Next.js Frontend Dashboard...
start "LinkdApply Frontend" /D "%~dp0frontend" powershell -NoExit -Command "npm run dev *>&1 | Tee-Object -FilePath '%LOGDIR%\frontend-dev.log' -Append"

echo [3/3] Starting Bot Supervisor...
start "LinkdApply Supervisor" /D "%~dp0backend" powershell -NoExit -Command "uv run python server.py --supervisor *>&1 | Tee-Object -FilePath '%LOGDIR%\supervisor-console.log' -Append"

echo ========================================================
echo All services are running in new windows (output also saved to logs).
echo   Dashboard: http://localhost:3000
echo   API/Next logs:  %LOGDIR%\api.log
echo                   %LOGDIR%\frontend-dev.log
echo                   %LOGDIR%\supervisor-console.log
echo   Bot file logs: %~dp0backend\logs\supervisor.log
echo                    (and other files in that folder)
echo ========================================================
