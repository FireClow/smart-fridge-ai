# Start FastAPI (port 8001) in a new window, then Vite frontend (port 5173).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Opening API in a new PowerShell window (port 8001)..."
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\scripts\start-api.ps1"

Write-Host "Waiting for API health on port 8001 (up to 90s)..."
$healthUrl = "http://127.0.0.1:8001/api/health"
$ready = $false
for ($i = 0; $i -lt 45; $i++) {
  try {
    $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
    if ($resp.StatusCode -eq 200) {
      $ready = $true
      break
    }
  } catch {
    Start-Sleep -Seconds 2
  }
}
if (-not $ready) {
  Write-Warning "API not ready yet. Start API manually: .\scripts\start-api.ps1"
}

Write-Host "Starting Vite on http://localhost:5173"
Set-Location "$root\frontend"
npm run dev
