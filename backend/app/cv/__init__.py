"""Classical Computer Vision package for the Smart Fridge project.

This package layers university-course CV topics on top of the existing
YOLOv8 pipeline. Each module maps to one taught topic:

  preprocessing.py   -> Image Filtering & Enhancement
  corners.py         -> Harris / Shi-Tomasi corners + Non-Maximum Suppression
  orb_features.py    -> ORB keypoints & descriptors
  matching.py        -> Feature Matching (BFMatcher, Hamming)
  homography.py      -> Homography (findHomography + RANSAC) + warp
  optical_flow.py    -> Optical Flow (Lucas-Kanade PyrLK)
  tracking.py        -> Feature-based tracking (Shi-Tomasi + LK trajectories)
  events.py          -> Inventory events (YOLO + flow + tracking)
  stereo.py          -> Stereo Vision / 3D Reconstruction (demonstration)
  session_state.py   -> in-memory per-session frame/track buffer
  overlays.py        -> drawing + base64 encode helpers

These modules are intentionally visualization/analytics-first; they do NOT
modify YOLO detection results or inventory counting.
"""
