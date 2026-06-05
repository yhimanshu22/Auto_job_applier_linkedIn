$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue

$BackendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "127.0.0.1" }
$BackendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }

uv run uvicorn server:app --host $BackendHost --port $BackendPort @args
