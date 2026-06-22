"""Evaluate classical OpenCV pipeline using YOLO dataset images + labels.

Produces report-ready metrics for the academic CV experiment (separate from
YOLO mAP). Uses the same fridge images/annotations already collected for YOLO.

Usage (from repo root, venv active):
  python scripts/eval_cv_opencv.py
  python scripts/eval_cv_opencv.py --data dataset_2/data.yaml --split valid --max-images 80
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
  sys.path.insert(0, str(_ROOT))

from backend.app.cv.corners import compare_corners
from backend.app.cv.homography import estimate_homography
from backend.app.cv.matching import match_images
from backend.app.cv.optical_flow import calc_optical_flow, to_gray
from backend.app.cv.orb_features import orb_summary
from backend.app.cv.preprocessing import VALID_MODES, apply_preprocess

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _load_yaml(path: Path) -> dict:
  with path.open(encoding="utf-8") as f:
    return yaml.safe_load(f)


def _resolve_split_dir(data_yaml: Path, split: str) -> Path:
  cfg = _load_yaml(data_yaml)
  rel = cfg.get(split) or cfg.get("val") or "valid/images"
  base = data_yaml.parent
  return (base / rel).resolve()


def _label_path(image_path: Path) -> Path:
  parts = list(image_path.parts)
  if "images" in parts:
    idx = parts.index("images")
    parts[idx] = "labels"
  else:
    parts[-2] = "labels"
  return Path(*parts[:-1]) / f"{image_path.stem}.txt"


def _parse_yolo_labels(label_file: Path, class_names: list[str]) -> list[dict]:
  if not label_file.is_file():
    return []
  boxes = []
  for line in label_file.read_text(encoding="utf-8").splitlines():
    parts = line.strip().split()
    if len(parts) < 5:
      continue
    cid = int(float(parts[0]))
    cx, cy, w, h = map(float, parts[1:5])
    name = class_names[cid] if 0 <= cid < len(class_names) else str(cid)
    boxes.append({"class_id": cid, "class_name": name, "cx": cx, "cy": cy, "w": w, "h": h})
  return boxes


def _crop_bbox(image: np.ndarray, box: dict, pad: float = 0.08) -> np.ndarray | None:
  h, w = image.shape[:2]
  bw, bh = box["w"] * w, box["h"] * h
  cx, cy = box["cx"] * w, box["cy"] * h
  x1 = int(max(0, cx - bw / 2 - pad * bw))
  y1 = int(max(0, cy - bh / 2 - pad * bh))
  x2 = int(min(w, cx + bw / 2 + pad * bw))
  y2 = int(min(h, cy + bh / 2 + pad * bh))
  if x2 - x1 < 24 or y2 - y1 < 24:
    return None
  return image[y1:y2, x1:x2].copy()


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
  a = a.astype(np.float32)
  b = b.astype(np.float32)
  mse = float(np.mean((a - b) ** 2))
  if mse <= 1e-10:
    return 99.0
  return round(20 * np.log10(255.0 / np.sqrt(mse)), 2)


def _list_images(split_dir: Path) -> list[Path]:
  if not split_dir.is_dir():
    raise FileNotFoundError(f"Split directory not found: {split_dir}")
  return sorted(
    p for p in split_dir.rglob("*") if p.suffix.lower() in _IMAGE_EXTS
  )


def _yolo_best_metrics(runs_glob: Path) -> dict | None:
  candidates = sorted(runs_glob.glob("train*/results.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
  if not candidates:
    return None
  csv_path = candidates[0]
  rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
  if not rows:
    return None
  best = max(rows, key=lambda r: float(r.get("metrics/mAP50(B)", 0) or 0))
  return {
    "run": csv_path.parent.name,
    "epoch": int(float(best["epoch"])),
    "mAP50": round(float(best["metrics/mAP50(B)"]), 4),
    "mAP50_95": round(float(best["metrics/mAP50-95(B)"]), 4),
    "precision": round(float(best["metrics/precision(B)"]), 4),
    "recall": round(float(best["metrics/recall(B)"]), 4),
  }


def eval_preprocessing(images: list[np.ndarray]) -> dict:
  totals = {m: {"orb_kp": [], "psnr": []} for m in VALID_MODES}
  for img in images:
    for mode in VALID_MODES:
      filtered = apply_preprocess(img, mode)
      totals[mode]["orb_kp"].append(orb_summary(filtered)["keypoint_count"])
      if mode == "none":
        totals[mode]["psnr"].append(99.0)
      else:
        totals[mode]["psnr"].append(_psnr(img, filtered))
  return {
    mode: {
      "mean_orb_keypoints": round(float(np.mean(vals["orb_kp"])), 1),
      "mean_psnr_vs_original": round(float(np.mean(vals["psnr"])), 2),
    }
    for mode, vals in totals.items()
  }


def eval_corners(images: list[np.ndarray]) -> dict:
  harris, shi = [], []
  for img in images:
    c = compare_corners(img)
    harris.append(c["harris_count"])
    shi.append(c["shi_tomasi_count"])
  return {
    "mean_harris_corners": round(float(np.mean(harris)), 1),
    "mean_shi_tomasi_corners": round(float(np.mean(shi)), 1),
    "shi_to_harris_ratio": round(float(np.mean(shi)) / max(1.0, float(np.mean(harris))), 3),
  }


def eval_optical_flow_synthetic(images: list[np.ndarray], dx: int = 8, dy: int = 4) -> dict:
  expected = float(np.hypot(dx, dy))
  errors, mags, tracked = [], [], []
  for img in images:
    h, w = img.shape[:2]
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    shifted = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)
    flow = calc_optical_flow(to_gray(img), to_gray(shifted))
    mag = float(flow["avg_magnitude"])
    mags.append(mag)
    tracked.append(int(flow["point_count"]))
    errors.append(abs(mag - expected))
  return {
    "synthetic_shift_px": {"dx": dx, "dy": dy, "expected_magnitude": round(expected, 3)},
    "mean_flow_magnitude": round(float(np.mean(mags)), 3),
    "mean_abs_error_px": round(float(np.mean(errors)), 3),
    "flow_accuracy_pct": round(max(0.0, 100.0 * (1.0 - float(np.mean(errors)) / expected)), 1),
    "mean_tracked_points": round(float(np.mean(tracked)), 1),
  }


def _affine_perturb(image: np.ndarray, rng: random.Random) -> np.ndarray:
  h, w = image.shape[:2]
  angle = rng.uniform(-7.0, 7.0)
  scale = rng.uniform(0.96, 1.04)
  m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
  return cv2.warpAffine(image, m, (w, h), borderMode=cv2.BORDER_REPLICATE)


def eval_orb_matching(
  samples: list[tuple[np.ndarray, str]],
  *,
  pairs_per_class: int = 5,
  seed: int = 42,
) -> dict:
  """ORB match: positive = crop vs lightly warped crop; negative = different class."""
  rng = random.Random(seed)
  by_class: dict[str, list[np.ndarray]] = {}
  for crop, name in samples:
    by_class.setdefault(name, []).append(crop)

  pos_scores: list[float] = []
  for crop, _ in samples:
    warped = _affine_perturb(crop, rng)
    pos_scores.append(match_images(crop, warped)["match_score"])

  neg_scores: list[float] = []
  comparisons = 0
  correct = 0
  class_names = [c for c in by_class if by_class[c]]
  if len(class_names) >= 2:
    for _ in range(pairs_per_class * len(class_names)):
      c_pos = rng.choice(class_names)
      others = [c for c in class_names if c != c_pos]
      if not others:
        continue
      c_neg = rng.choice(others)
      ref = rng.choice(by_class[c_pos])
      warped_pos = _affine_perturb(ref, rng)
      query_neg = rng.choice(by_class[c_neg])
      s_pos = match_images(ref, warped_pos)["match_score"]
      s_neg = match_images(ref, query_neg)["match_score"]
      pos_scores.append(s_pos)
      neg_scores.append(s_neg)
      comparisons += 1
      if s_pos > s_neg:
        correct += 1

  pos_mean = float(np.mean(pos_scores)) if pos_scores else 0.0
  neg_mean = float(np.mean(neg_scores)) if neg_scores else 0.0
  acc = round(100.0 * correct / comparisons, 1) if comparisons else None

  threshold = 0.08
  pos_hits = sum(1 for s in pos_scores if s >= threshold)
  neg_hits = sum(1 for s in neg_scores if s < threshold)
  total_cls = len(pos_scores) + len(neg_scores)
  threshold_acc = round(100.0 * (pos_hits + neg_hits) / total_cls, 1) if total_cls else None

  return {
    "mean_positive_match_score": round(pos_mean, 3),
    "mean_negative_match_score": round(neg_mean, 3),
    "pairwise_comparisons": comparisons,
    "pairwise_discrimination_accuracy_pct": acc,
    "threshold_match_score": threshold,
    "threshold_classification_accuracy_pct": threshold_acc,
    "match_score_gap_positive_minus_negative": round(pos_mean - neg_mean, 3),
    "note": (
      "Positive = YOLO crop vs lightly rotated/scaled crop. "
      "Negative = different food-class crops (same pipeline as /api/cv/match)."
    ),
  }


def eval_homography_self(images: list[np.ndarray]) -> dict:
  inlier_ratios, match_scores = [], []
  for img in images[: min(30, len(images))]:
    h, w = img.shape[:2]
    angle = np.deg2rad(5.0)
    scale = 1.03
    center = (w / 2, h / 2)
    m = cv2.getRotationMatrix2D(center, 5.0, scale)
    warped = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)
    est = estimate_homography(img, warped)
    mc = max(1, int(est["match_count"]))
    inlier_ratios.append(est["inliers"] / mc)
    match_scores.append(float(est["match_score"]))
  return {
    "mean_match_score_after_transform": round(float(np.mean(match_scores)), 3),
    "mean_homography_inlier_ratio": round(float(np.mean(inlier_ratios)), 3),
    "transform": "rotate_5deg_scale_1.03",
  }


def _collect_crops(
  image_paths: list[Path],
  class_names: list[str],
  max_crops: int,
) -> list[tuple[np.ndarray, str]]:
  crops: list[tuple[np.ndarray, str]] = []
  for path in image_paths:
    img = cv2.imread(str(path))
    if img is None:
      continue
    for box in _parse_yolo_labels(_label_path(path), class_names):
      c = _crop_bbox(img, box)
      if c is not None:
        crops.append((c, box["class_name"]))
    if len(crops) >= max_crops:
      break
  return crops[:max_crops]


def _markdown_report(report: dict) -> str:
  cv = report["opencv"]
  yolo = report.get("yolo_reference")
  lines = [
    "# OpenCV Experiment Results",
    "",
    f"Generated: {report['generated_at']}",
    f"Dataset: `{report['dataset']}` split `{report['split']}` ({report['num_images']} images)",
    "",
    "## 1. Preprocessing (filtering & enhancement)",
    "",
    "| Mode | Mean ORB keypoints | Mean PSNR vs original |",
    "|------|-------------------:|----------------------:|",
  ]
  for mode, row in cv["preprocessing"].items():
    lines.append(f"| {mode} | {row['mean_orb_keypoints']} | {row['mean_psnr_vs_original']} |")

  lines += [
    "",
    "## 2. Corner detection",
    "",
    f"- Mean Harris corners: **{cv['corners']['mean_harris_corners']}**",
    f"- Mean Shi-Tomasi corners: **{cv['corners']['mean_shi_tomasi_corners']}**",
    f"- Shi/Harris ratio: **{cv['corners']['shi_to_harris_ratio']}**",
    "",
    "## 3. ORB feature matching (YOLO crops)",
    "",
  ]
  m = cv["orb_matching"]
  lines.append(f"- Positive match (crop vs warped crop): **{m['mean_positive_match_score']}**")
  lines.append(f"- Negative match (different class): **{m['mean_negative_match_score']}**")
  lines.append(
    f"- Discrimination accuracy (pos > neg): **{m['pairwise_discrimination_accuracy_pct']}%** "
    f"({m['pairwise_comparisons']} pairs)"
  )
  lines.append(f"- Score gap (positive − negative): **{m['match_score_gap_positive_minus_negative']}**")
  lines.append(
    f"- Threshold classification (score ≥ {m.get('threshold_match_score', 0.08)}): "
    f"**{m.get('threshold_classification_accuracy_pct')}%**"
  )
  if m.get("note"):
    lines.append(f"- _{m['note']}_")
  lines += [
    "",
    "## 4. Optical flow (synthetic translation test)",
    "",
    f"- Expected motion magnitude: **{cv['optical_flow']['synthetic_shift_px']['expected_magnitude']} px**",
    f"- Measured mean magnitude: **{cv['optical_flow']['mean_flow_magnitude']} px**",
    f"- Mean absolute error: **{cv['optical_flow']['mean_abs_error_px']} px**",
    f"- Flow accuracy: **{cv['optical_flow']['flow_accuracy_pct']}%**",
    "",
    "## 5. Homography (RANSAC inlier ratio)",
    "",
    f"- Mean inlier ratio: **{cv['homography']['mean_homography_inlier_ratio']}**",
    f"- Mean match score after transform: **{cv['homography']['mean_match_score_after_transform']}**",
  ]
  if yolo:
    lines += [
      "",
      "## Reference: YOLO experiment (same dataset)",
      "",
      f"- Best run: `{yolo['run']}` epoch {yolo['epoch']}",
      f"- mAP@50: **{yolo['mAP50']}** | mAP@50-95: **{yolo['mAP50_95']}**",
      f"- Precision: **{yolo['precision']}** | Recall: **{yolo['recall']}**",
    ]
  lines.append("")
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Evaluate OpenCV pipeline on YOLO dataset")
  parser.add_argument("--data", default="dataset_2/data.yaml", help="Ultralytics data.yaml")
  parser.add_argument("--split", default="valid", help="Split key in data.yaml (valid/val/test/train)")
  parser.add_argument("--max-images", type=int, default=60, help="Max images to evaluate")
  parser.add_argument("--max-crops", type=int, default=200, help="Max YOLO bbox crops for matching")
  parser.add_argument("--out-dir", default="results/cv_experiment", help="Output directory")
  parser.add_argument("--seed", type=int, default=42)
  args = parser.parse_args()

  data_yaml = (_ROOT / args.data).resolve()
  cfg = _load_yaml(data_yaml)
  class_names = list(cfg.get("names") or [])
  split_dir = _resolve_split_dir(data_yaml, args.split)

  all_images = _list_images(split_dir)
  if not all_images:
    raise SystemExit(f"No images under {split_dir}")

  rng = random.Random(args.seed)
  chosen_paths = all_images if len(all_images) <= args.max_images else rng.sample(all_images, args.max_images)

  loaded: list[np.ndarray] = []
  for p in chosen_paths:
    img = cv2.imread(str(p))
    if img is not None:
      loaded.append(img)
  if not loaded:
    raise SystemExit("Failed to load any images.")

  crops = _collect_crops(chosen_paths, class_names, args.max_crops)

  print(f"Evaluating OpenCV on {len(loaded)} images, {len(crops)} YOLO crops...")

  opencv_results = {
    "preprocessing": eval_preprocessing(loaded),
    "corners": eval_corners(loaded),
    "orb_matching": eval_orb_matching(crops, seed=args.seed),
    "optical_flow": eval_optical_flow_synthetic(loaded),
    "homography": eval_homography_self(loaded),
  }

  yolo_ref = _yolo_best_metrics(_ROOT / "runs" / "detect")

  report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "dataset": str(data_yaml.relative_to(_ROOT)).replace("\\", "/"),
    "split": args.split,
    "num_images": len(loaded),
    "num_yolo_crops": len(crops),
    "opencv": opencv_results,
    "yolo_reference": yolo_ref,
  }

  out_dir = (_ROOT / args.out_dir).resolve()
  out_dir.mkdir(parents=True, exist_ok=True)
  json_path = out_dir / "opencv_metrics.json"
  md_path = out_dir / "opencv_report.md"
  json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
  md_path.write_text(_markdown_report(report), encoding="utf-8")

  print(f"\nWrote {json_path}")
  print(f"Wrote {md_path}")
  print("\n--- Summary ---")
  print(f"ORB discrimination: {opencv_results['orb_matching'].get('pairwise_discrimination_accuracy_pct')}%")
  print(f"ORB pos/neg scores: {opencv_results['orb_matching'].get('mean_positive_match_score')} / {opencv_results['orb_matching'].get('mean_negative_match_score')}")
  print(f"Optical flow accuracy: {opencv_results['optical_flow']['flow_accuracy_pct']}%")
  print(f"Homography inlier ratio: {opencv_results['homography']['mean_homography_inlier_ratio']}")
  if yolo_ref:
    print(f"YOLO mAP50 (reference): {yolo_ref['mAP50']}")


if __name__ == "__main__":
  main()
