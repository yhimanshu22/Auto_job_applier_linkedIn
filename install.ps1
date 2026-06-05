$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:REPO_URL) { $env:REPO_URL } else { "https://github.com/yhimanshu22/Auto_job_applier_linkedIn.git" }
$RepoDir = if ($env:REPO_DIR) { $env:REPO_DIR } else { "Auto_job_applier_linkedIn" }
$BackendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "127.0.0.1" }
$BackendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }

function Require-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing dependency: $name"
  }
}

Require-Command git
Require-Command python
Require-Command npm

if (-not (Test-Path "$RepoDir\.git")) {
  git clone $RepoUrl $RepoDir
}

Set-Location $RepoDir

# Backend (uv project venv lives in backend/.venv — not repo root)
Set-Location backend
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
python -m pip install -U uv | Out-Null
uv sync

if (-not (Test-Path ".\.env") -and (Test-Path ".\linkedin_automation\.env.example")) {
  Copy-Item ".\linkedin_automation\.env.example" ".\.env"
}
if (-not (Test-Path ".\linkedin_automation\.env") -and (Test-Path ".\linkedin_automation\.env.example")) {
  Copy-Item ".\linkedin_automation\.env.example" ".\linkedin_automation\.env"
}

Write-Host "Starting backend on http://$BackendHost`:$BackendPort ..."
Start-Process -NoNewWindow -FilePath "uv" -ArgumentList @(
  "run", "uvicorn", "server:app",
  "--host", $BackendHost,
  "--port", $BackendPort
) -RedirectStandardOutput "backend.log" -RedirectStandardError "backend.err.log"

# Frontend
Set-Location ..\frontend
npm install

Write-Host "Starting frontend on http://localhost:3000 ..."
npm run dev

