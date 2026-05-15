# Smart Fridge Web Dashboard

React + Vite + Tailwind dashboard with multi-page routing, Supabase Auth, and Axios API client.

## Prerequisites

- Node.js 18+
- Python venv with root + `backend/requirements.txt`
- Supabase project with migrations applied (see root `README.md`)

## Frontend env

```bash
cd frontend
cp .env.example .env
```

Set `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`. Leave `VITE_API_URL` empty in dev (Vite proxies `/api` → port 8000).

## Run

```bash
npm install
npm run dev
```

Open http://localhost:5173

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

## Demo mode

`VITE_USE_DUMMY=true` — local dummy data only, no auth or API.
