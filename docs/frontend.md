# Smart Fridge Web Dashboard

React + Vite + Tailwind dashboard with multi-page routing, Supabase Auth, and Axios API client.

## Prerequisites

- Node.js 18+
- Python venv with root + `backend/requirements.txt`
- Supabase project with migrations applied (see [project setup](README.md))

## Frontend env

```bash
cd frontend
cp .env.example .env
```

Set `VITE_SUPABASE_URL`, `VITE_SUPABASE_KEY` (publishable/anon key from Supabase Dashboard). Leave `VITE_API_URL` empty in dev (Vite proxies `/api` → FastAPI).

You can also put `SUPABASE_URL` + `SUPABASE_KEY` in the **repo root** `.env` — the Vite build reads both (handy for Vercel if you already set backend-style names).

### Vercel deploy

In Vercel → **Environment Variables** (Production), set **either**:

| Option A (recommended) | Option B (same as root `.env`) |
|--------------------------|--------------------------------|
| `VITE_SUPABASE_URL` | `SUPABASE_URL` |
| `VITE_SUPABASE_KEY` | `SUPABASE_KEY` (anon/publishable, not service role) |

Then **Redeploy** (disable build cache if the old bundle still shows "not configured").

Optional: `VITE_API_URL` = your hosted FastAPI URL (Render/Railway) without a `/api` suffix.

## Run

**Butuh 2 proses:** frontend (Vite) + backend (FastAPI). Tanpa API, proxy `/api` gagal (`ECONNREFUSED 127.0.0.1:8001`).

**Opsi A — satu perintah (Windows):**

```powershell
# Dari root project
.\scripts\dev.ps1
```

**Opsi B — dua terminal:**

```powershell
# Terminal 1 (root project)
.\scripts\start-api.ps1

# Terminal 2
cd frontend
npm install
npm run dev
```

Tunggu ~20 detik sampai API selesai load YOLO, lalu buka http://localhost:5173

Register / sign in with email + password (enable Email provider in Supabase).

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — camera, stats, alerts |
| `/inventory` | Full inventory grid |
| `/history` | Detection logs |
| `/notifications` | Expiration warnings |
| `/settings` | Confidence, auto-scan default, logout |
| `/login`, `/register` | Auth |

## Scan API

**Scan now** posts JPEG to `POST /api/scan/image`. Response includes `fps`, `inference_ms`, `items`, `annotated_image_base64`.

Auto-scan uses a 3s chained timeout (no overlapping requests).

## Realtime

The dashboard subscribes to Supabase `postgres_changes` on `inventory`, `detection_logs`, and `expiration_notifications`. Run `supabase_migration_realtime.sql` (or enable Realtime in the Supabase dashboard) so the UI updates without a full page reload.
