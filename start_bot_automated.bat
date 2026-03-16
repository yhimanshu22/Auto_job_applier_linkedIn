@echo off
cd /d "%~dp0"
echo Starting Bot Supervisor in background...
start /b python supervisor.py
echo.
echo Supervisor is running. You can check logs in logs/supervisor.log
echo To stop it, find and kill the 'python supervisor.py' process.
pause
