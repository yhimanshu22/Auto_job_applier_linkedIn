@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Building LinkdApply Full Production Release (Standalone)
echo ========================================================

:: Cleanup previous build junctions to prevent recursive bloat
echo [0/5] Cleaning up old build artifacts...
if exist "frontend\public\dist" (
    echo Removing old dist junction...
    rmdir "frontend\public\dist"
)

echo.
echo [1/5] Downloading Portable Node.js...
cd electron
if not exist node.exe (
    powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/win-x64/node.exe' -OutFile 'node.exe'"
)
cd ..

echo.
echo [2/5] Building Next.js Frontend...
cd frontend
call npm install
:: Ensure standalone output is enabled
call npm run build

:: Copy static assets to standalone
echo Copying Next.js static assets...
if not exist ".next\standalone\.next\static" mkdir ".next\standalone\.next\static"
if not exist ".next\standalone\public" mkdir ".next\standalone\public"
xcopy /E /I /Y ".next\static" ".next\standalone\.next\static"
:: Important: Do NOT copy the dist folder if it somehow still exists
xcopy /E /I /Y "public" ".next\standalone\public" /EXCLUDE:..\build_exclude.txt
cd ..

echo.
echo [3/5] Building Python Backend (PyInstaller)...
cd backend
call uv pip install pyinstaller
call uv run pyinstaller --noconfirm server.spec
cd ..

echo.
echo [4/5] Building Electron App...
cd electron
call npm install
call npm run build
cd ..

echo.
echo [5/5] Linking dist folder to frontend public...
if not exist "frontend\public\dist" (
    mklink /J "frontend\public\dist" "electron\dist"
)
:: Also update standalone public folder since it was copied before step 4
if exist "frontend\.next\standalone\public" (
    if not exist "frontend\.next\standalone\public\dist" mkdir "frontend\.next\standalone\public\dist"
    xcopy /Y "electron\dist\*.exe" "frontend\.next\standalone\public\dist\"
)

echo.
echo ========================================================
echo BUILD SUCCESSFUL!
echo The installer is located in the electron/dist/ folder.
echo ========================================================
pause

