"""FastAPI application for Smart Fridge dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
  sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.model_loader import load_yolo_model, resolve_model_path
from backend.routers.cv import router as cv_router
from backend.routers.inventory import router as inventory_router
from backend.routers.logs import router as logs_router, stats_router
from backend.routers.notifications import router as notifications_router
from backend.routers.scan import router as scan_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.limiter import limiter

load_dotenv(_ROOT / ".env")

_LOG = logging.getLogger(__name__)
_DEBUG_LOG = _ROOT / "debug-1fd1ee.log"


def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
  # #region agent log
  try:
    payload = {
      "sessionId": "1fd1ee",
      "timestamp": int(time.time() * 1000),
      "location": location,
      "message": message,
      "data": data,
      "hypothesisId": hypothesis_id,
    }
    with _DEBUG_LOG.open("a", encoding="utf-8") as f:
      f.write(json.dumps(payload) + "\n")
  except OSError:
    pass
  # #endregion


def _cors_origins() -> list[str]:
  raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
  )
  return [o.strip() for o in raw.split(",") if o.strip()]


def _supabase_configured() -> bool:
  url = os.getenv("SUPABASE_URL", "").strip()
  key = os.getenv("SUPABASE_KEY", "").strip() or os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY", ""
  ).strip()
  return bool(url and key and "your-project" not in url and "your-anon" not in key)


@asynccontextmanager
async def lifespan(app: FastAPI):
  model_path = resolve_model_path()
  app.state.yolo = None
  app.state.model_path = str(model_path)
  app.state.yolo_load_error = None
  app.state.yolo_loading = True
  _agent_log("main.py:lifespan", "lifespan_start", {"model_path": str(model_path)}, "C")

  async def _load_yolo() -> None:
    _agent_log("main.py:lifespan", "yolo_load_start", {}, "C")
    try:
      model = await asyncio.to_thread(load_yolo_model)
      app.state.yolo = model
      app.state.model_path = str(resolve_model_path())
      _LOG.info("YOLO model loaded from %s", app.state.model_path)
      _agent_log(
        "main.py:lifespan",
        "yolo_load_ok",
        {"model_path": app.state.model_path},
        "C",
      )
    except Exception as exc:
      app.state.yolo = None
      app.state.yolo_load_error = f"{type(exc).__name__}: {exc}"
      _LOG.warning("YOLO not loaded: %s", exc)
      _agent_log(
        "main.py:lifespan",
        "yolo_load_fail",
        {"error": app.state.yolo_load_error},
        "C",
      )
    finally:
      app.state.yolo_loading = False

  yolo_task = asyncio.create_task(_load_yolo())
  _agent_log("main.py:lifespan", "server_accepting_requests", {}, "B")
  yield
  yolo_task.cancel()


app = FastAPI(
  title="Smart Fridge API",
  description="REST API for Smart Refrigerator inventory dashboard",
  version="2.0.0",
  lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
  CORSMiddleware,
  allow_origins=_cors_origins(),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.middleware("http")
async def attach_user_from_header(request: Request, call_next):
  auth = request.headers.get("Authorization", "")
  if auth.startswith("Bearer "):
    token = auth[7:].strip()
    if token:
      try:
        from backend.app.auth.deps import user_id_from_token

        request.state.user_id = user_id_from_token(token)
      except Exception:
        request.state.user_id = None
  else:
    request.state.user_id = None
  return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
  detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
  return JSONResponse(
    status_code=exc.status_code,
    content={"detail": detail, "code": f"http_{exc.status_code}"},
  )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
  return JSONResponse(
    status_code=422,
    content={"detail": exc.errors(), "code": "validation_error"},
  )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
  _LOG.exception("Unhandled error: %s", exc)
  return JSONResponse(
    status_code=500,
    content={"detail": "Internal server error.", "code": "internal_error"},
  )


app.include_router(inventory_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(scan_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(cv_router, prefix="/api")


@app.get("/api/health")
def health(request: Request) -> dict:
  yolo = getattr(request.app.state, "yolo", None)
  path = getattr(request.app.state, "model_path", str(resolve_model_path()))
  _agent_log(
    "main.py:health",
    "health_hit",
    {
      "yolo_loaded": yolo is not None,
      "yolo_loading": getattr(request.app.state, "yolo_loading", False),
    },
    "D",
  )
  return {
    "status": "ok",
    "yolo_loaded": yolo is not None,
    "yolo_loading": getattr(request.app.state, "yolo_loading", False),
    "model_path": path,
    "model_exists": Path(path).is_file(),
    "yolo_load_error": getattr(request.app.state, "yolo_load_error", None),
    "supabase_configured": _supabase_configured(),
  }


@app.get("/api/model/info")
def model_info(request: Request) -> dict:
  yolo = getattr(request.app.state, "yolo", None)
  path = getattr(request.app.state, "model_path", str(resolve_model_path()))
  if yolo is None:
    return {
      "loaded": False,
      "path": path,
      "exists": Path(path).exists(),
      "num_classes": 0,
      "classes": [],
    }
  names = getattr(yolo, "names", {}) or {}
  classes = [names[i] for i in sorted(names.keys())] if names else []
  return {
    "loaded": True,
    "path": path,
    "exists": True,
    "num_classes": len(classes),
    "classes": classes,
  }
