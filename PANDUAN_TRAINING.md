# Panduan menaikkan akurasi model (YOLOv8 — Smart Fridge)

Panduan ini mengikuti setup proyek Anda: `train.py` memakai `dataset_2/data.yaml`, default `yolov8n.pt`, `epochs=30`, `imgsz=640`.

## Urutan prioritas (dari paling berpengaruh)

### 1. Data & anotasi

- [ ] **Cukup gambar per kelas** — rule of thumb: ratusan per kelas untuk domain sempit (kulkas) lebih stabil; puluhan saja sering underfit.
- [ ] **Variasi scene**: cahaya terang/redup, rak penuh/sepi, sudut kamera beda, blur ringan.
- [ ] **Bounding box rapat** di objek — tidak terlalu besar/kecil; satu objek satu kotak.
- [ ] **Kelas seimbang** — jika satu makanan jarang, tambah foto atau duplikasi strategis (bukan copy-paste persis).
- [ ] **Val set jujur** — beda sesi/hari dari train (bukan frame berurutan dari video yang sama dengan train).

Struktur dataset Ultralytics biasanya:

```text
dataset_2/
  data.yaml
  images/train/   ...
  images/val/     ...
  labels/train/   ...
  labels/val/     ...
```

Pastikan `data.yaml` path `train`/`val` benar dan nama kelas sama dengan label.

### 1b. Gabung banyak folder dengan kelas baru (dataset_3 & dataset_4)

`dataset_2`, `dataset_3`, dan `dataset_4` punya sekema kelas berbeda. Skrip **`scripts/build_combined_dataset.py`** akan:

1. Menyimpan **urutan kelas `dataset_2` terlebih dulu** (indeks tidak berubah dari `data.yaml`-nya).
2. Menambahkan **kelas baru** untuk setiap nama di dataset_3/4 yang **tidak** bisa dipadankan ke `dataset_2` (plus alias heuristic di skrip).

Output: **`dataset_combined/`** + **`dataset_combined_classes.txt`** (indeks `\t` nama lengkap untuk referensi aplikasi/backend).

```powershell
python scripts/build_combined_dataset.py --dry-run
python scripts/build_combined_dataset.py
python train.py --data dataset_combined/data.yaml --epochs 100
```

Sesuaikan **backend / inventori / label UI** kalau **`nc`** bertambah besar.

Catatan **`dataset_1`**: tidak digabung otomatis oleh skrip tersebut (layout sering lain).
### 2. Train lebih “serius” (setelah data rapi)

Jalankan dari root repo (setelah `venv` aktif):

```powershell
# Baseline lebih kuat dari default script lama
python train.py --model yolov8s.pt --epochs 100 --imgsz 640 --patience 25

# Jika GPU cukup: resolusi lebih tinggi (objek kecil di kulkas)
python train.py --model yolov8m.pt --epochs 100 --imgsz 768 --batch 8
```

- **Model**: `n` < `s` < `m` < `l` < `x` — akurasi naik, inferensi lebih berat (penting untuk Scan real-time).
- **Epochs**: 30 sering kurang; naikkan sampai kurva **mAP** di `results.csv` melambat.
- **Patience**: early stopping agar tidak overfit berlebihan.
- **imgsz**: 768 atau 1024 jika objek kecil sering terlewat (butuh VRAM lebih).

### 3. Baca hasil training

Setelah train, buka folder run terbaru di `runs/detect/train-*/`:

- `results.png` — mAP train/val
- `val_batch*_pred.jpg` — prediksi vs ground truth: lihat salah **lokasi**, **kelas**, atau **miss**

Metrik utama: **mAP50** dan **mAP50-95** di val. Bandingkan antar eksperimen, bukan hanya “loss turun”.

### 4. Inference di aplikasi

Setelah dapat `best.pt` baru:

1. Set `MODEL_PATH` di `.env` ke path `weights/best.pt` run terbaru, atau salin file ke path yang dipakai backend.
2. Restart API (`scripts/start-api.ps1` atau uvicorn).

Sesuaikan **confidence** di kode/UI jika banyak false positive atau banyak miss (trade-off precision vs recall).

### 5. Checklist cepat “kenapa masih jelek?”

| Gejala | Arah perbaikan |
|--------|----------------|
| Banyak **miss** (tidak kedeteksi) | Lebih banyak data, `imgsz` lebih besar, model `s`/`m`, epoch lebih banyak |
| Banyak **salah kelas** | Perbaiki label; seimbangkan kelas; kurangi kelas yang terlalu mirip tanpa konteks |
| Kotak **melenceng** | Perbaiki bbox label; train lebih lama; model sedikit lebih besar |
| Val bagus, **webcam jelek** | Domain gap — tambah foto dari kamera yang sama dengan lighting mirip produksi |

## Perintah lengkap `train.py`

```text
python train.py -h
```

---

**Ringkas:** akurasi naik paling konsisten dari **data + label + val yang benar**, lalu **model lebih besar**, **epoch cukup**, dan **imgsz** sesuai ukuran objek di frame.
