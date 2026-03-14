"""
utils/config.py
===============
Centralised configuration for Air Canvas.
Edit values here to tune the application behaviour.
"""


class Config:
    # ── Camera ──────────────────────────────────────────────────
    CAMERA_INDEX: int   = 0          # 0 = default webcam
    FRAME_WIDTH:  int   = 1280
    FRAME_HEIGHT: int   = 720
    CAMERA_FPS:   int   = 30

    # ── MediaPipe ────────────────────────────────────────────────
    MAX_HANDS:             int   = 1
    DETECTION_CONFIDENCE:  float = 0.8
    TRACKING_CONFIDENCE:   float = 0.7

    # ── Drawing defaults ─────────────────────────────────────────
    DEFAULT_BRUSH_SIZE:  int = 8
    DEFAULT_ERASER_SIZE: int = 30

    # ── Toolbar ──────────────────────────────────────────────────
    TOOLBAR_HEIGHT: int = 80         # pixels

    # ── Colours available in toolbar ────────────────────────────
    # Each entry: (BGR tuple, label)
    COLORS = [
        ((255,   0,   0), "Blue"),
        ((  0, 255,   0), "Green"),
        ((  0,   0, 255), "Red"),
        ((  0, 255, 255), "Yellow"),
        ((255,   0, 255), "Magenta"),
        ((255, 165,   0), "Orange"),
        ((255, 255, 255), "White"),
    ]

    # ── Save directory ───────────────────────────────────────────
    SAVE_DIR: str = "saved_drawings"
