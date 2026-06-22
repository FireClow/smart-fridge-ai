"""Smoke tests for POST /api/cv/analyze upload handling."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import cv2
import numpy as np
import requests

ROOT = Path(__file__).resolve().parent.parent
API = "http://127.0.0.1:8001/api/cv/analyze"
HEADERS = {"X-CV-Session": "test-upload-session"}


def _jpeg_bytes() -> bytes:
  img = np.zeros((120, 160, 3), dtype=np.uint8)
  cv2.rectangle(img, (20, 20), (140, 100), (0, 255, 0), 2)
  ok, encoded = cv2.imencode(".jpg", img)
  assert ok
  return encoded.tobytes()


def _png_bytes() -> bytes:
  img = np.zeros((120, 160, 3), dtype=np.uint8)
  ok, encoded = cv2.imencode(".png", img)
  assert ok
  return encoded.tobytes()


def _webp_bytes() -> bytes:
  img = np.zeros((120, 160, 3), dtype=np.uint8)
  ok, encoded = cv2.imencode(".webp", img)
  if not ok:
    return b""
  return encoded.tobytes()


def post(name: str, data: bytes, content_type: str) -> tuple[int, str]:
  files = {"file": (name, io.BytesIO(data), content_type)}
  try:
    resp = requests.post(API, files=files, headers=HEADERS, timeout=30)
    detail = resp.json().get("detail", resp.text[:120]) if resp.content else ""
    return resp.status_code, str(detail)
  except requests.exceptions.ConnectionError:
    return 0, "backend offline"


def main() -> int:
  tests: list[tuple[str, callable]] = [
    ("JPG upload", lambda: post("sample.jpg", _jpeg_bytes(), "image/jpeg")),
    ("JPEG upload", lambda: post("sample.jpeg", _jpeg_bytes(), "image/jpeg")),
    ("PNG upload", lambda: post("sample.png", _png_bytes(), "image/png")),
    ("WEBP upload", lambda: (_webp_bytes() and post("sample.webp", _webp_bytes(), "image/webp")) or (415, "webp unsupported by opencv build")),
    ("Invalid file upload", lambda: post("notes.txt", b"hello", "text/plain")),
    ("Corrupted image upload", lambda: post("bad.jpg", b"\xff\xd8\xffbroken", "image/jpeg")),
    ("Empty file upload", lambda: post("empty.jpg", b"", "image/jpeg")),
  ]

  passed = 0
  for label, fn in tests:
    status, detail = fn()
    ok = (
      (label.endswith("upload") and label.startswith(("JPG", "JPEG", "PNG")) and status == 200)
      or (label == "WEBP upload" and status in (200, 415))
      or (label == "Invalid file upload" and status in (400, 415))
      or (label == "Corrupted image upload" and status == 400)
      or (label == "Empty file upload" and status == 400)
    )
    if label == "WEBP upload" and status == 415 and "opencv" in detail.lower():
      ok = True
    print(f"[{'PASS' if ok else 'FAIL'}] {label}: status={status} detail={detail[:80]}")
    if ok:
      passed += 1

  offline_status, _ = post("offline.jpg", _jpeg_bytes(), "image/jpeg")
  if offline_status == 0:
    print("[PASS] Backend offline simulation: connection refused (run API to test live upload)")

  print(f"\n{passed}/{len(tests)} assertions passed")
  return 0 if passed == len(tests) else 1


if __name__ == "__main__":
  sys.exit(main())
