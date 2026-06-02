"""Image upload / webcam frame scan using YOLOv8."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from backend.app.limiter import limiter
from backend.app.services.scan_service import process_scan

router = APIRouter(prefix="/scan", tags=["scan"])


def get_yolo(request: Request):
  model = getattr(request.app.state, "yolo", None)
  if model is None:
    raise HTTPException(
      status_code=503,
      detail="YOLO model not loaded. Set MODEL_PATH to a valid .pt file and restart the API.",
    )
  return model


async def get_optional_user_id(request: Request) -> str | None:
  return getattr(request.state, "user_id", None)


@router.post("/image")
@limiter.limit("30/minute")
async def scan_image(
  request: Request,
  file: UploadFile = File(...),
  confidence: float = Query(0.6, ge=0.05, le=0.99),
  preprocess_mode: str = Query("none"),
  model=Depends(get_yolo),
  user_id: str | None = Depends(get_optional_user_id),
) -> dict[str, Any]:
  """Run detection on one image; upsert inventory and append detection logs.

  `preprocess_mode` (none|gaussian|bilateral|clahe) applies an Image
  Filtering & Enhancement step before YOLO inference.
  """
  raw = await file.read()
  return await process_scan(
    raw=raw,
    content_type=file.content_type,
    confidence=confidence,
    model=model,
    user_id=user_id,
    preprocess_mode=preprocess_mode,
  )
