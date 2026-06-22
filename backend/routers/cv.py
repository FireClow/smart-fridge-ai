"""Computer Vision analysis endpoints (classical CV topics).

These routes layer course topics (filtering, corners, ORB, matching,
homography, optical flow, tracking, events) on top of the existing YOLO
pipeline. With the exception of event detection, none of these modify YOLO
results or inventory; they are for visualization and academic demonstration.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from backend.app.cv import corners as corners_mod
from backend.app.cv import orb_features as orb_mod
from backend.app.cv.events import detect_events
from backend.app.cv.homography import estimate_homography
from backend.app.cv.matching import match_images
from backend.app.cv.optical_flow import calc_optical_flow, to_gray
from backend.app.cv.overlays import (
  draw_corner_comparison,
  draw_flow_vectors,
  draw_keypoints,
  draw_tracks,
  encode_jpeg_base64,
)
from backend.app.cv.preprocessing import apply_preprocess, normalize_mode
from backend.app.cv.session_state import get_session, reset_session
from backend.app.limiter import limiter
from database import (
  connect_to_supabase,
  get_cv_events,
  get_reference_image,
  insert_cv_event,
  upload_reference_image,
)

router = APIRouter(prefix="/cv", tags=["computer-vision"])

_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_ALLOWED_CONTENT_TYPES = {
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
  "image/pjpeg",
}
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _session_key(request: Request) -> str:
  uid = getattr(request.state, "user_id", None)
  if uid:
    return str(uid)
  return request.headers.get("X-CV-Session", "anonymous")


def _decode(raw: bytes, filename: str | None = None, content_type: str | None = None) -> np.ndarray:
  if not raw:
    raise HTTPException(status_code=400, detail="Empty file body.")
  if len(raw) > _MAX_UPLOAD_BYTES:
    raise HTTPException(status_code=413, detail="Image too large (max 5 MB).")

  ctype = (content_type or "").split(";", 1)[0].strip().lower()
  if ctype and ctype not in _ALLOWED_CONTENT_TYPES:
    raise HTTPException(
      status_code=415,
      detail="Unsupported image type. Use JPG, JPEG, PNG, or WEBP.",
    )

  ext = ""
  if filename and "." in filename:
    ext = filename[filename.rfind(".") :].lower()
  if ext and ext not in _ALLOWED_EXTENSIONS:
    raise HTTPException(
      status_code=415,
      detail="Unsupported file extension. Use JPG, JPEG, PNG, or WEBP.",
    )

  image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
  if image is None:
    raise HTTPException(
      status_code=400,
      detail="Could not decode image content (corrupt or unsupported format).",
    )
  return image


def _get_yolo(request: Request):
  model = getattr(request.app.state, "yolo", None)
  if model is None:
    raise HTTPException(
      status_code=503,
      detail="YOLO model not loaded. Set MODEL_PATH to a valid .pt file and restart the API.",
    )
  return model


def _get_supabase():
  try:
    return connect_to_supabase()
  except (ValueError, ConnectionError) as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/analyze")
@limiter.limit("60/minute")
async def analyze(
  request: Request,
  file: UploadFile = File(...),
  preprocess_mode: str = Query("none"),
) -> dict[str, Any]:
  """Run filtering + Harris/Shi-Tomasi + ORB + optical flow + tracking.

  Stateless w.r.t. YOLO/DB; uses the per-session frame buffer for the
  frame-to-frame topics (optical flow, tracking).
  """
  raw = await file.read()
  original = _decode(raw, filename=file.filename, content_type=file.content_type)

  mode = normalize_mode(preprocess_mode)
  filtered = apply_preprocess(original, mode) if mode != "none" else original

  # Phase 2: Harris + Shi-Tomasi corners (+ NMS inside corners module).
  corner_data = corners_mod.compare_corners(filtered)
  corner_vis = draw_corner_comparison(filtered, corner_data["harris"], corner_data["shi_tomasi"])

  # Phase 3: ORB keypoints + descriptors.
  keypoints, descriptors = orb_mod.extract_orb(filtered)
  orb_vis = draw_keypoints(filtered, keypoints)
  descriptor_count = int(descriptors.shape[0]) if descriptors is not None else 0

  # Phase 6 + 7: optical flow and feature tracking use session state.
  state = get_session(_session_key(request))
  curr_gray = to_gray(filtered)

  flow = {"vectors": [], "avg_magnitude": 0.0, "point_count": 0}
  if state.prev_gray is not None and state.prev_gray.shape == curr_gray.shape:
    flow = calc_optical_flow(state.prev_gray, curr_gray)
  flow_vis = draw_flow_vectors(filtered, flow["vectors"])

  track_data = state.tracker.update(filtered)
  track_vis = draw_tracks(filtered, track_data["tracks"])

  state.prev_gray = curr_gray

  metrics = {
    "harris_count": corner_data["harris_count"],
    "shi_tomasi_count": corner_data["shi_tomasi_count"],
    "orb_keypoints": len(keypoints),
    "orb_descriptors": descriptor_count,
    "optical_flow_magnitude": flow["avg_magnitude"],
    "flow_point_count": flow["point_count"],
    "active_tracks": track_data["active_tracks"],
    "preprocess_mode": mode,
  }
  state.last_metrics = metrics

  return {
    "metrics": metrics,
    "original_image_base64": encode_jpeg_base64(original),
    "filtered_image_base64": encode_jpeg_base64(filtered) if mode != "none" else None,
    "corner_image_base64": encode_jpeg_base64(corner_vis),
    "orb_image_base64": encode_jpeg_base64(orb_vis),
    "flow_image_base64": encode_jpeg_base64(flow_vis),
    "tracking_image_base64": encode_jpeg_base64(track_vis),
  }


@router.get("/metrics")
def metrics(request: Request) -> dict[str, Any]:
  """Latest analyze() metrics for this session (for dashboard cards)."""
  state = get_session(_session_key(request))
  return {"metrics": state.last_metrics, "last_detections": state.last_detections}


@router.post("/reset")
def reset(request: Request) -> dict[str, str]:
  reset_session(_session_key(request))
  return {"status": "reset"}


@router.post("/match")
@limiter.limit("30/minute")
async def match(
  request: Request,
  file: UploadFile = File(...),
  class_name: str = Query(...),
) -> dict[str, Any]:
  """Phase 4: ORB + BFMatcher(Hamming) between a stored reference and the crop."""
  client = _get_supabase()
  ref_bytes = get_reference_image(client, class_name)
  if not ref_bytes:
    raise HTTPException(
      status_code=404,
      detail=f"No reference image stored for '{class_name}'. Upload one first.",
    )
  reference = _decode(bytes(ref_bytes))
  upload_raw = await file.read()
  current = _decode(upload_raw, filename=file.filename, content_type=file.content_type)

  result = match_images(reference, current)
  return {
    "class_name": class_name,
    "match_count": result["match_count"],
    "ref_keypoints": result["ref_keypoints"],
    "cur_keypoints": result["cur_keypoints"],
    "match_score": result["match_score"],
    "reference_image_base64": encode_jpeg_base64(reference),
    "current_image_base64": encode_jpeg_base64(current),
    "match_image_base64": encode_jpeg_base64(result["match_image"]),
  }


@router.post("/homography")
@limiter.limit("30/minute")
async def homography(
  request: Request,
  file: UploadFile = File(...),
  class_name: str = Query(...),
  warp: bool = Query(False),
) -> dict[str, Any]:
  """Phase 5: homography via findHomography + RANSAC, with optional warp."""
  client = _get_supabase()
  ref_bytes = get_reference_image(client, class_name)
  if not ref_bytes:
    raise HTTPException(
      status_code=404,
      detail=f"No reference image stored for '{class_name}'. Upload one first.",
    )
  reference = _decode(bytes(ref_bytes))
  upload_raw = await file.read()
  current = _decode(upload_raw, filename=file.filename, content_type=file.content_type)

  result = estimate_homography(reference, current)
  warped_b64 = None
  if warp and result["warped"] is not None:
    warped_b64 = encode_jpeg_base64(result["warped"])

  return {
    "class_name": class_name,
    "inliers": result["inliers"],
    "outliers": result["outliers"],
    "match_count": result["match_count"],
    "match_score": result["match_score"],
    "homography": result["homography"],
    "match_image_base64": encode_jpeg_base64(result["vis"]) if result["vis"] is not None else None,
    "warped_image_base64": warped_b64,
  }


@router.post("/events")
@limiter.limit("60/minute")
async def events(
  request: Request,
  file: UploadFile = File(...),
  confidence: float = Query(0.6, ge=0.05, le=0.99),
) -> dict[str, Any]:
  """Phase 8: classify Added/Removed/Moved from YOLO + optical flow + tracking."""
  model = _get_yolo(request)
  upload_raw = await file.read()
  image = _decode(upload_raw, filename=file.filename, content_type=file.content_type)

  # YOLO detections (read-only inference; does not change inventory here).
  results = model(image, verbose=False)
  curr_counts: dict[str, int] = {}
  if results and results[0].boxes is not None:
    for box in results[0].boxes:
      if float(box.conf[0]) < confidence:
        continue
      name = model.names[int(box.cls[0])]
      curr_counts[name] = curr_counts.get(name, 0) + 1

  state = get_session(_session_key(request))
  curr_gray = to_gray(image)
  flow = {"avg_magnitude": 0.0}
  if state.prev_gray is not None and state.prev_gray.shape == curr_gray.shape:
    flow = calc_optical_flow(state.prev_gray, curr_gray)
  state.prev_gray = curr_gray

  detected = detect_events(state.last_detections, curr_counts, flow["avg_magnitude"])
  state.last_detections = curr_counts

  user_id = getattr(request.state, "user_id", None)
  stored: list[dict] = []
  if detected:
    try:
      client = _get_supabase()
      for ev in detected:
        insert_cv_event(
          client, ev["item_name"], ev["event_type"], ev["magnitude"], user_id=user_id
        )
        stored.append(ev)
    except HTTPException:
      raise
    except Exception:
      # Persistence is best-effort; still return the detected events.
      stored = detected

  return {
    "events": detected,
    "stored": len(stored),
    "detections": curr_counts,
    "optical_flow_magnitude": flow["avg_magnitude"],
  }


@router.get("/events")
def list_events(request: Request, limit: int = 50) -> list[dict]:
  client = _get_supabase()
  user_id = getattr(request.state, "user_id", None)
  return get_cv_events(client, limit=min(max(limit, 1), 200), user_id=user_id)


@router.post("/reference/{class_name}")
@limiter.limit("20/minute")
async def upload_reference(
  request: Request,
  class_name: str,
  file: UploadFile = File(...),
) -> dict[str, Any]:
  """Store/replace the reference image for a food class (Supabase Storage)."""
  client = _get_supabase()
  raw = await file.read()
  image = _decode(raw, filename=file.filename, content_type=file.content_type)
  ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
  if not ok:
    raise HTTPException(status_code=400, detail="Could not encode reference image.")
  try:
    path = upload_reference_image(client, class_name, encoded.tobytes())
  except Exception as exc:
    raise HTTPException(status_code=502, detail=f"Reference upload failed: {exc}") from exc
  return {"class_name": class_name, "path": path}


@router.get("/reference/{class_name}")
def fetch_reference(request: Request, class_name: str) -> dict[str, Any]:
  client = _get_supabase()
  raw = get_reference_image(client, class_name)
  if not raw:
    return {"class_name": class_name, "exists": False, "image_base64": None}
  image = _decode(bytes(raw))
  return {
    "class_name": class_name,
    "exists": True,
    "image_base64": encode_jpeg_base64(image),
  }
