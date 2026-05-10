@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ========================================================
echo Stopping LinkdApply bot (supervisor + workers)
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pattern = 'server\.py.*--(supervisor|bot)|runAiBot\.py'; " ^
  "$killed = 0; " ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match $pattern) } | ForEach-Object { " ^
  "  Write-Host ('  Ending PID ' + $_.ProcessId + ' — ' + $_.Name); " ^
  "  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; " ^
  "  $killed++ " ^
  "}; " ^
  "if ($killed -eq 0) { Write-Host '  No matching bot/supervisor processes found.' }"

echo.
echo Stopping Chromedriver (if running)...
taskkill /F /IM chromedriver.exe >nul 2>&1
if errorlevel 1 (echo   No chromedriver.exe process.) else (echo   chromedriver.exe stopped.)

echo ========================================================
echo Bot stop finished. Close Chrome manually if a bot window remains.
echo To stop API ^(8000^) and Next.js ^(3000^), close those windows or run stop_servers.bat
echo ========================================================
