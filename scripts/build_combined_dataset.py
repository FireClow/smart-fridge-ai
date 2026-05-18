"""Gabung dataset_2 + dataset_3 + dataset_4 ke dataset_combined/.

Urutan kelas akhir:
  1) Semua nama di dataset_2 (indeks tidak berubah, anchor untuk label dataset_2).
  2) Kelas baru: nama dari dataset_3 / dataset_4 yang tidak bisa dipadankan ke kelas dataset_2
     (alias + heuristic tunggal/plural terhadap HANYA basis dataset_2).

Label dataset_3/4 kemudian diremap ke indeks baru (basis + kelas baru). Nama baru disortir secara
deterministik (snake_case hasil norm_label).

Catatan dataset_1: umumnya bukan struktur YOLO Ultralytics umum — tidak diproses skrip ini.

Penggunaan (dari root repo):
  pip install -r requirements.txt
  python scripts/build_combined_dataset.py --dry-run
  python scripts/build_combined_dataset.py
  python train.py --data dataset_combined/data.yaml

Penting: Jika jumlah kelas naik, backend / DB / daftar inventori harus disesuaikan manual.

Opsi:
  --dry-run   Hanya cetak ringkasan (termasuk daftar kelas baru), tidak menyalin file.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

try:
  import yaml
except ImportError as e:
  raise SystemExit("Install pyyaml: pip install pyyaml") from e


IMG_SUFFIXES = (
  ".jpg",
  ".jpeg",
  ".png",
  ".bmp",
  ".webp",
  ".tif",
  ".tiff",
)

# Aliases: normalized source name -> normalized target name (harus muat di basis dataset_2
# ATAU akan jadi kunci kelas baru setelah norm).
NAME_ALIASES: dict[str, str] = {
  "egg": "eggs",
  "strawberry": "strawberries",
  "tomatoes": "tomato",
  "tomato_paste": "tomato",
  "apples": "apple",
  "bananas": "banana",
  "carrots": "carrot",
  "potatoes": "potato",
  "onions": "onion",
  "lemons": "lime",
  "lemon": "lime",
  "beef_mince": "ground_beef",
  "chicken_thighs": "chicken",
  "mushroom": "mushrooms",
  "sweetcorn": "corn",
  "sweet_corn": "corn",
  "chocolate_chips": "chocolate",
  "steak": "beef",
}


def _project_root() -> Path:
  return Path(__file__).resolve().parent.parent


def norm_label(s: str) -> str:
  s = str(s).strip().lower().replace("-", "_")
  s = re.sub(r"\s+", "_", s)
  s = re.sub(r"_+", "_", s).strip("_")
  return s


def _load_yaml(path: Path) -> dict[str, Any]:
  with path.open(encoding="utf-8") as f:
    data = yaml.safe_load(f)
  if not isinstance(data, dict):
    raise ValueError(f"Invalid yaml (not a dict): {path}")
  return data


def _canonical_lookup(names: list[str]) -> dict[str, int]:
  return {norm_label(n): i for i, n in enumerate(names)}


def _resolve_to_dataset2_id(src_class_name: str, canon_norm_to_id: dict[str, int]) -> int | None:
  """Temukan indeks kelas pada dataset_2-only (untuk klasifikasi: basis vs kelas baru)."""
  n = norm_label(src_class_name)
  n = NAME_ALIASES.get(n, n)
  if n in canon_norm_to_id:
    return canon_norm_to_id[n]
  if n.endswith("ies") and len(n) > 3:
    cand = n[:-3] + "y"
    if cand in canon_norm_to_id:
      return canon_norm_to_id[cand]
  if n.endswith("es") and len(n) > 3:
    for cut in (2, 1):
      cand = n[:-cut]
      if cand in canon_norm_to_id:
        return canon_norm_to_id[cand]
  if n.endswith("s") and len(n) > 2:
    cand = n[:-1]
    if cand in canon_norm_to_id:
      return canon_norm_to_id[cand]
  return None


def _collect_new_class_norms(
  *,
  extras_sources: list[list[str]],
  base_norm_to_id: dict[str, int],
) -> dict[str, str]:
  """norm unik untuk kelas yang tidak dapat dipetakan ke dataset_2 -> nama di yaml (= norm)."""
  out: dict[str, str] = {}
  for src_list in extras_sources:
    for nm in src_list:
      s = str(nm)
      if _resolve_to_dataset2_id(s, base_norm_to_id) is not None:
        continue
      key = norm_label(s)
      key = NAME_ALIASES.get(key, key)
      if key in base_norm_to_id:
        continue
      if key not in out:
        out[key] = key
  return out


def _build_full_norm_to_id(names: list[str]) -> dict[str, int]:
  return {norm_label(n): i for i, n in enumerate(names)}


def _resolve_nm_to_final_id(src_class_name: str, full_norm_to_id: dict[str, int]) -> int | None:
  """Map salah satu nama string ke indeks dalam daftar gabungan final."""
  n = norm_label(src_class_name)
  n = NAME_ALIASES.get(n, n)
  if n in full_norm_to_id:
    return full_norm_to_id[n]
  if n.endswith("ies") and len(n) > 3:
    cand = n[:-3] + "y"
    if cand in full_norm_to_id:
      return full_norm_to_id[cand]
  if n.endswith("es") and len(n) > 3:
    for cut in (2, 1):
      cand = n[:-cut]
      if cand in full_norm_to_id:
        return full_norm_to_id[cand]
  if n.endswith("s") and len(n) > 2:
    cand = n[:-1]
    if cand in full_norm_to_id:
      return full_norm_to_id[cand]
  return None


def _build_complete_old_mapping(
  src_names: list[str],
  full_norm_to_id: dict[str, int],
) -> dict[int, int]:
  mapping: dict[int, int] = {}
  missing: list[int] = []
  for old_id, nm in enumerate(src_names):
    fid = _resolve_nm_to_final_id(nm, full_norm_to_id)
    if fid is not None:
      mapping[old_id] = fid
    else:
      missing.append(old_id)
  if missing:
    miss_names = [src_names[i] for i in missing[:15]]
    raise RuntimeError(f"Kelompok nama tidak bisa dipetakan meski ada kelas baru: {miss_names}")
  return mapping


def _iter_images(images_dir: Path) -> list[Path]:
  if not images_dir.is_dir():
    return []
  out: list[Path] = []
  for p in sorted(images_dir.iterdir()):
    if p.is_file() and p.suffix.lower() in IMG_SUFFIXES:
      out.append(p)
  return out


def _remap_label_text(text: str, old_to_new: dict[int, int]) -> str | None:
  lines_out: list[str] = []
  for line in text.splitlines():
    line = line.strip()
    if not line:
      continue
    parts = line.split()
    try:
      oid = int(parts[0])
    except ValueError:
      continue
    nid = old_to_new.get(oid)
    if nid is None:
      continue
    rest = parts[1:]
    lines_out.append(" ".join([str(nid), *rest]))
  if not lines_out:
    return None
  return "\n".join(lines_out) + "\n"


def _ingest_copy_only(
  *,
  src_root: Path,
  split: str,
  out_root: Path,
  prefix: str,
  stats: dict[str, int],
) -> None:
  img_dir = src_root / split / "images"
  lbl_dir = src_root / split / "labels"
  if not img_dir.is_dir():
    return
  for img in _iter_images(img_dir):
    stem = img.stem
    src_lbl = lbl_dir / f"{stem}.txt"
    new_stem = f"{prefix}_{stem}"
    dst_img = out_root / split / "images" / f"{new_stem}{img.suffix.lower()}"
    dst_lbl = out_root / split / "labels" / f"{new_stem}.txt"
    if not src_lbl.is_file():
      stats["missing_labels"] += 1
      continue
    shutil.copy2(img, dst_img)
    shutil.copy2(src_lbl, dst_lbl)
    stats["images_copied"] += 1


def _ingest_remapped(
  *,
  src_root: Path,
  split: str,
  out_root: Path,
  prefix: str,
  old_to_new: dict[int, int],
  stats: dict[str, int],
  drop_empty: bool,
) -> None:
  img_dir = src_root / split / "images"
  lbl_dir = src_root / split / "labels"
  if not img_dir.is_dir():
    return
  for img in _iter_images(img_dir):
    stem = img.stem
    src_lbl = lbl_dir / f"{stem}.txt"
    if not src_lbl.is_file():
      stats["missing_labels"] += 1
      continue
    text = src_lbl.read_text(encoding="utf-8", errors="replace")
    new_text = _remap_label_text(text, old_to_new)
    if new_text is None:
      stats["images_skipped_empty_labels"] += 1
      if drop_empty:
        continue
    new_stem = f"{prefix}_{stem}"
    dst_img = out_root / split / "images" / f"{new_stem}{img.suffix.lower()}"
    dst_lbl = out_root / split / "labels" / f"{new_stem}.txt"
    shutil.copy2(img, dst_img)
    dst_lbl.write_text(new_text, encoding="utf-8")
    stats["images_copied"] += 1


def _write_data_yaml(out_root: Path, names: list[str]) -> None:
  y = {
    "path": str(out_root.resolve()),
    "train": "train/images",
    "val": "valid/images",
    "nc": len(names),
    "names": names,
  }
  out_path = out_root / "data.yaml"
  with out_path.open("w", encoding="utf-8") as f:
    yaml.dump(y, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _finalize_names(names2: list[str], extras_norm_to_display: dict[str, str]) -> list[str]:
  base = [str(x) for x in names2]
  extras_sorted = [extras_norm_to_display[k] for k in sorted(extras_norm_to_display.keys())]
  return base + extras_sorted


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Gabung dataset_2-4: basis dataset_2 + kelas baru dari ds3/ds4",
  )
  parser.add_argument(
    "--out",
    type=Path,
    default=None,
    help="Folder output (default: <repo>/dataset_combined)",
  )
  parser.add_argument("--dry-run", action="store_true", help="Jangan tulis file")
  args = parser.parse_args()

  root = _project_root()
  out_root = (args.out if args.out else root / "dataset_combined").resolve()

  ds2 = root / "dataset_2"
  ds3 = root / "dataset_3"
  ds4 = root / "dataset_4"

  cfg2 = _load_yaml(ds2 / "data.yaml")
  names2 = cfg2.get("names")
  if not isinstance(names2, list):
    raise SystemExit("dataset_2/data.yaml: missing names list")
  base_strings = [str(x) for x in names2]
  base_norm_to_id = _canonical_lookup(base_strings)

  snames3: list[str] | None = None
  snames4: list[str] | None = None
  extras_sources: list[list[str]] = []
  reports: list[str] = []

  for label, yfile in (("dataset_3", ds3 / "data.yaml"), ("dataset_4", ds4 / "data.yaml")):
    if not yfile.is_file():
      reports.append(f"{label}: tidak ada data.yaml, dilewati untuk kelas baru.")
      continue
    cfg = _load_yaml(yfile)
    sn = cfg.get("names")
    if not isinstance(sn, list):
      reports.append(f"{label}: names invalid.")
      continue
    slist = [str(x) for x in sn]
    if label == "dataset_3":
      snames3 = slist
    else:
      snames4 = slist
    extras_sources.append(slist)

  new_norm_display = _collect_new_class_norms(
    extras_sources=extras_sources,
    base_norm_to_id=base_norm_to_id,
  )
  final_names = _finalize_names(base_strings, new_norm_display)
  full_norm_to_id = _build_full_norm_to_id(final_names)

  n_base = len(base_strings)
  n_new = len(new_norm_display)
  print(f"=== Kelas gabungan ({n_base} dari dataset_2 + {n_new} kelas baru = {len(final_names)} total) ===")
  if n_new > 0:
    print(f"Kelas baru (nama di data.yaml):\n  {', '.join(sorted(new_norm_display.keys()))}")
  else:
    print("Tidak ada kelas baru: semua nama ds3/ds4 terpetakan ke dataset_2 atau alias.")

  for label, sn in (("dataset_3", snames3), ("dataset_4", snames4)):
    if not sn:
      continue
    try:
      _build_complete_old_mapping(sn, full_norm_to_id)
    except RuntimeError as e:
      reports.append(f"{label}: error pemetaan: {e}")
    else:
      reports.append(f"{label}: {len(sn)} kelas sumber dapat dipetakan ke {len(final_names)} kelas gabungan.")

  for line in reports:
    print(line)

  print(f"\nOutput folder: {out_root}")
  print("dataset_1: tidak digabung otomatis (biasanya bukan YOLO layout siap pakai).")
  print("Reminder: Sesuaikan backend / kelas aplikasi jika nc berubah.")

  if args.dry_run:
    print("\n(dry-run: tidak ada file yang ditulis)")
    return

  new_manifest = root / "dataset_combined_classes.txt"
  rng_new = "(tidak ada)" if n_new <= 0 else f"{n_base}-{len(final_names) - 1}"
  head = (
    "# Urutan sama seperti nc/names di dataset_combined/data.yaml.\n"
    f"# Indeks dari dataset_2: 0-{n_base - 1}. Kelas tambahan dari ds3/ds4: {rng_new}\n\n"
  )
  body_lines = [f"{i}\t{nm}\n" for i, nm in enumerate(final_names)]
  new_manifest.write_text(head + "".join(body_lines), encoding="utf-8")

  if out_root.exists():
    shutil.rmtree(out_root)
  (out_root / "train" / "images").mkdir(parents=True)
  (out_root / "train" / "labels").mkdir(parents=True)
  (out_root / "valid" / "images").mkdir(parents=True)
  (out_root / "valid" / "labels").mkdir(parents=True)

  stats = {
    "images_copied": 0,
    "missing_labels": 0,
    "images_skipped_empty_labels": 0,
  }

  _ingest_copy_only(src_root=ds2, split="train", out_root=out_root, prefix="d2", stats=stats)
  _ingest_copy_only(src_root=ds2, split="valid", out_root=out_root, prefix="d2", stats=stats)

  for _, dpath, yfile, prefix in (
    ("dataset_3", ds3, ds3 / "data.yaml", "d3"),
    ("dataset_4", ds4, ds4 / "data.yaml", "d4"),
  ):
    if not yfile.is_file():
      continue
    cfg = _load_yaml(yfile)
    sn = cfg.get("names")
    if not isinstance(sn, list):
      continue
    slist = [str(x) for x in sn]
    mapper = _build_complete_old_mapping(slist, full_norm_to_id)
    _ingest_remapped(
      src_root=dpath,
      split="train",
      out_root=out_root,
      prefix=prefix,
      old_to_new=mapper,
      stats=stats,
      drop_empty=True,
    )

  _write_data_yaml(out_root, final_names)

  print("\n=== Selesai ===")
  for k, v in stats.items():
    print(f"  {k}: {v}")
  print(f"\ndaftar indeks kelas lengkap:\n  {new_manifest.relative_to(root)}")
  print("\nTrain dengan:\n  python train.py --data dataset_combined/data.yaml")


if __name__ == "__main__":
  main()
