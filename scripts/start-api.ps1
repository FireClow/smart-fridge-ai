# Start Smart Fridge FastAPI (frees dev ports, then starts on 8001).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$port = 8001
foreach ($p in @(8000, 8001)) {
  Write-Host "Stopping listeners on port $p..."
  Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
      Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2

Write-Host "Starting API on http://127.0.0.1:$port (YOLO loads at startup - wait ~20s)..."
Write-Host "Vite proxies /api -> port $port (see frontend/vite.config.js)"
& "$root\venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port $port
