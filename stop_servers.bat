@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo Stopping LinkdApply stack (bot + API + frontend)
echo ========================================================

call "%~dp0stop_bot.bat"

echo.
echo Stopping listeners on ports 8000 and 3000...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "foreach ($port in 8000, 3000) { " ^
  "  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; " ^
  "  foreach ($c in $conns) { " ^
  "    $procId = $c.OwningProcess; " ^
  "    try { $p = Get-Process -Id $procId -ErrorAction Stop; Write-Host ('  Port ' + $port + ': stopping PID ' + $procId + ' (' + $p.ProcessName + ')'); Stop-Process -Id $procId -Force } catch {} " ^
  "  } " ^
  "  if (-not $conns) { Write-Host ('  Port ' + $port + ': nothing listening.') } " ^
  "}"

echo ========================================================
echo Done.
echo ========================================================
