# Smart Fridge AI

Real-time food inventory management using YOLOv8 object detection for smart refrigerators.

## Stack

- **Frontend:** React, Vite, Tailwind CSS, Axios, React Router
- **Backend:** FastAPI, Ultralytics YOLOv8, OpenCV
- **Database:** Supabase (PostgreSQL + Auth + Realtime)

## Setup

### 1. Python environment

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 2. Environment

Copy `.env.example` to `.env` and set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`), and `MODEL_PATH`.

Copy `frontend/.env.example` to `frontend/.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.

### 3. Database (Supabase SQL Editor)

Run in order:

1. `supabase_schema.sql`
2. `supabase_migration_inventory_expiry.sql` (if upgrading an old DB)
3. `supabase_migration_multi_user.sql`

Enable **Email** auth in Supabase → Authentication → Providers.

Enable **Realtime** for `inventory`, `detection_logs`, `expiration_notifications`.

### 4. YOLO weights

Train or place weights at `runs/detect/train-5/weights/best.pt` (see `train.py`).

### 5. Run locally

**API** (from repo root):

```bash
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Dashboard:**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **503** on scan | `MODEL_PATH` file missing — train or copy `best.pt` |
| **500** on scan | Check Supabase credentials; run migrations; see API logs |
| **502** on scan | Database write failed — RLS or missing columns |
| **404** `/api/api/...` | Set `VITE_API_URL` to `http://localhost:8000` without `/api` suffix |
| CORS error | Add your origin to `ALLOWED_ORIGINS` in `.env` |
| Camera + `python app.py` | Do not use same webcam on Windows simultaneously |

## Why Scan Now failed (before fixes)

1. Uncaught Supabase/YOLO exceptions → opaque **500**
2. Missing **python-multipart** for file uploads
3. Auto-scan **overlapping** POST requests every 3s
4. **Fake FPS** in UI (not measured)

Fixes: scan service with error mapping, in-flight guard + chained timeouts for auto-scan, real `fps` from inference timing.

## Project structure

```
backend/
  app/          # services, auth, metrics, limiter
  routers/      # REST routes
  main.py       # FastAPI entry
frontend/src/
  pages/        # Dashboard, Inventory, History, Notifications, Settings, Auth
  services/     # Axios API client
  context/      # Auth, Settings
```
