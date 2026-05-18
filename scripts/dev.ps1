# Start FastAPI (port 8001) in a new window, then Vite frontend (port 5173).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Opening API in a new PowerShell window (port 8001)..."
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\scripts\start-api.ps1"

Write-Host "Waiting 5s for API to bind..."
Start-Sleep -Seconds 5

Write-Host "Starting Vite on http://localhost:5173"
Set-Location "$root\frontend"
npm run dev
