#Requires -Version 5.1
<#
.SYNOPSIS
  Membantu setup Supabase cloud untuk Smart Fridge AI (Windows).

.DESCRIPTION
  1. Membuka dashboard Supabase (buat project baru jika belum ada).
  2. Opsional: menulis .env dari parameter agar tidak copy-paste manual.

.EXAMPLE
  .\scripts\setup_supabase_windows.ps1

.EXAMPLE
  .\scripts\setup_supabase_windows.ps1 `
    -SupabaseUrl "https://abcdefgh.supabase.co" `
    -SupabaseKey "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...." `
    -DatabaseUrl "postgresql://postgres:YOUR_PASSWORD@db.abcdefgh.supabase.co:5432/postgres"
#>
param(
  [string] $SupabaseUrl = "",
  [string] $SupabaseKey = "",
  [string] $DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "Membuka Supabase Dashboard (buat project baru -> pilih region, set password DB)..." -ForegroundColor Cyan
Start-Process "https://supabase.com/dashboard"

if ($SupabaseUrl -and $SupabaseKey) {
  $py = Join-Path $root "venv\Scripts\python.exe"
  if (-not (Test-Path $py)) { $py = "python" }
  $args = @(
    (Join-Path $root "scripts\configure_supabase_env.py"),
    "--url", $SupabaseUrl,
    "--key", $SupabaseKey
  )
  if ($DatabaseUrl) { $args += @("--database-url", $DatabaseUrl) }
  & $py @args
  Write-Host "Selesai menulis .env" -ForegroundColor Green
} else {
  Write-Host @"

Langkah berikutnya (manual):
1) Di Supabase: Project Settings -> Data API -> salin Project URL dan anon public key.
2) Jalankan dari folder project ini:

   .\venv\Scripts\python.exe .\scripts\configure_supabase_env.py --url "https://....supabase.co" --key "eyJ...."

   Opsional (agar schema bisa di-push dari PC tanpa SQL Editor):
   tambahkan --database-url "postgresql://postgres:PASSWORD@db....supabase.co:5432/postgres"

3) Buat tabel: SQL Editor -> paste isi supabase_schema.sql -> Run
   ATAU jika Anda sudah set --database-url di langkah 2:
   .\venv\Scripts\python.exe .\scripts\apply_supabase_schema.py

4) Jalankan aplikasi:
   .\venv\Scripts\python.exe .\app.py

   Uji koneksi + model tanpa webcam:
   `$env:SKIP_WEBCAM='1'; .\venv\Scripts\python.exe .\app.py`

"@ -ForegroundColor Yellow
}
