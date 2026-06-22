# Deploy on Replit

Smart Fridge AI runs as **one Repl**: FastAPI (YOLO + OpenCV + API) and the built React app on the same host.

## Import from GitHub

1. [Create a Repl](https://replit.com) → **Import from GitHub** → `FireClow/smart-fridge-ai`
2. Replit reads `.replit` and installs Python 3.11 + Node 20 automatically.

## Secrets (Tools → Secrets)

| Secret | Example |
|--------|---------|
| `SUPABASE_URL` | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | service role or anon key |
| `VITE_SUPABASE_URL` | same as `SUPABASE_URL` |
| `VITE_SUPABASE_KEY` | anon/publishable key for browser |
| `MODEL_PATH` | `runs/detect/train-5/weights/best.pt` |
| `ALLOWED_ORIGINS` | `https://your-repl-name.replit.app` |

Leave `VITE_API_URL` unset on Replit — production uses same-origin `/api/*`.

## YOLO weights

`runs/` and `*.pt` are not in git. Upload your trained weights into the Repl file tree (e.g. `runs/detect/train-5/weights/best.pt`) or set `MODEL_PATH` to where you place `best.pt`.

## Development

Click **Run**. This starts:

- FastAPI on port **8000**
- Vite dev server on port **5000** (webview)

## Production deploy

1. Set all Secrets above (including `VITE_*` for the frontend build).
2. **Deploy** → Replit runs the build in `.replit` and starts `scripts/replit-start.sh`.
3. One process on port **80** serves `/api/*` and the React SPA from `frontend/dist`.

Check health: `GET /api/health` — `yolo_loaded` should be `true` after the model finishes loading.

## Tips

- YOLO + PyTorch need RAM; use a **Reserved VM** if Autoscale runs out of memory.
- First cold start may take 30–60s while dependencies and the model load.
