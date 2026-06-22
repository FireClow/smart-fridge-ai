# OpenCV Experiment Results

Generated: 2026-06-22T14:05:10.239731+00:00
Dataset: `dataset_2/data.yaml` split `valid` (80 images)

## 1. Preprocessing (filtering & enhancement)

| Mode | Mean ORB keypoints | Mean PSNR vs original |
|------|-------------------:|----------------------:|
| none | 500.0 | 99.0 |
| gaussian | 499.2 | 36.64 |
| bilateral | 499.6 | 36.98 |
| clahe | 500.0 | 21.29 |

## 2. Corner detection

- Mean Harris corners: **1284.6**
- Mean Shi-Tomasi corners: **200.0**
- Shi/Harris ratio: **0.156**

## 3. ORB feature matching (YOLO crops)

- Positive match (crop vs warped crop): **0.212**
- Negative match (different class): **0.019**
- Discrimination accuracy (pos > neg): **18.7%** (150 pairs)
- Score gap (positive − negative): **0.193**
- Threshold classification (score ≥ 0.08): **44.6%**
- _Positive = YOLO crop vs lightly rotated/scaled crop. Negative = different food-class crops (same pipeline as /api/cv/match)._

## 4. Optical flow (synthetic translation test)

- Expected motion magnitude: **8.944 px**
- Measured mean magnitude: **8.981 px**
- Mean absolute error: **0.039 px**
- Flow accuracy: **99.6%**

## 5. Homography (RANSAC inlier ratio)

- Mean inlier ratio: **0.991**
- Mean match score after transform: **0.706**

## Reference: YOLO experiment (same dataset)

- Best run: `train-6` epoch 39
- mAP@50: **0.9726** | mAP@50-95: **0.628**
- Precision: **0.9554** | Recall: **0.971**
