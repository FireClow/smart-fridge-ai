"""Pydantic schemas for Smart Fridge API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryItem(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  item_name: str
  quantity: int
  updated_at: datetime | None = None
  expires_at: datetime | None = None
  expiry_locked: bool = False


class InventoryExpiryPatch(BaseModel):
  expires_at: datetime | None = None
  expiry_locked: bool | None = None


class DetectionLog(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  item_name: str
  quantity: int
  confidence: float
  detected_at: datetime | None = None


class Stats(BaseModel):
  total_items: int = Field(description="Sum of all quantities")
  total_categories: int = Field(description="Distinct item_name count")
  avg_confidence: float | None = Field(
    default=None,
    description="Mean confidence from recent logs (0-1)",
  )
  last_detected: datetime | None = Field(
    default=None,
    description="Most recent detected_at in detection_logs",
  )
  fps_hint: float | None = Field(
    default=None,
    description="Optional hint for UI; not measured server-side",
  )
  expiring_soon_count: int = Field(
    default=0,
    description="Inventory rows with expires_at within the next 3 days (not yet expired)",
  )


class ScanItemResult(BaseModel):
  item_name: str
  quantity: int
  confidence: float
  expires_at: datetime | None = None
  expiry_locked: bool = False


class ScanResponse(BaseModel):
  items: list[ScanItemResult]
  annotated_image_base64: str | None = None
  original_image_base64: str | None = None
  filtered_image_base64: str | None = None
  preprocess_mode: str = "none"
  inference_ms: float = 0
  fps: float = 0
  detected_count: int = 0


class ExpirationNotification(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: str | None = None
  inventory_id: int | None = None
  item_name: str
  expires_at: datetime | None = None
  days_remaining: int | None = None
  message: str
  read: bool = False
  created_at: datetime | None = None
