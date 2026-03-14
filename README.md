# ✋ Air Canvas
### Hand Gesture Based Virtual Drawing System

Draw in the air using only your hand and a webcam — no mouse, no stylus, no touch.

---

## Features

| Feature | Description |
|---|---|
| ☝ Air Drawing | Move your index finger to paint on screen |
| ✌ Pen Lift | Two fingers up = move without drawing |
| ✋ Clear | All fingers open = clear the canvas |
| 🎨 Colours | 7 colour swatches in the toolbar |
| 🧹 Eraser | Dedicated eraser tool |
| 🖌 Brush Size | Increase / decrease brush thickness |
| 💾 Save | Press **S** to save the drawing |
| ⚡ Real-time | 30 FPS, low-latency tracking |

---

## Project Structure

```
air_canvas/
├── main.py                  ← Entry point — run this
├── air_canvas.py            ← Core application class
├── requirements.txt
├── saved_drawings/          ← Auto-created when you save
└── utils/
    ├── __init__.py
    ├── config.py            ← All tunable settings
    ├── hand_tracker.py      ← MediaPipe hand detection wrapper
    ├── gesture_recognizer.py← Gesture → action mapping
    ├── drawing_engine.py    ← Canvas management & drawing ops
    └── toolbar.py           ← On-screen toolbar UI
```

---

## Installation

### 1. Clone / download the project

```bash
git clone <repo-url>
cd air_canvas
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `mediapipe` requires Python 3.8 – 3.11.  
> Use `pip install mediapipe-silicon` on Apple Silicon Macs.

---

## Running

```bash
python main.py
```

A window titled **Air Canvas** will open.  
Hold your hand in front of the webcam.

---

## Controls

### Hand Gestures

| Gesture | Fingers Up | Action |
|---|---|---|
| ☝ Draw | Index only | Draw on canvas |
| ✌ Move | Index + Middle | Move without drawing |
| ✋ Clear | All four fingers | Clear entire canvas |
| 👆 Select | Index in toolbar area | Pick colour / tool |

### Keyboard

| Key | Action |
|---|---|
| **S** | Save drawing as PNG |
| **Q** or **ESC** | Quit |

---

## Configuration

Edit `utils/config.py` to change defaults:

```python
CAMERA_INDEX   = 0          # Change if you have multiple cameras
FRAME_WIDTH    = 1280       # Reduce (e.g. 640) for better performance
FRAME_HEIGHT   = 720
DEFAULT_BRUSH_SIZE  = 8
DEFAULT_ERASER_SIZE = 30
DETECTION_CONFIDENCE = 0.8  # Lower = more sensitive hand detection
```

### Add / change colours

```python
COLORS = [
    ((255, 0,   0),   "Blue"),
    ((0,   255, 0),   "Green"),
    # Add your own (BGR, label) tuples here
]
```

---

## How It Works

```
Webcam Frame
     │
     ▼
cv2.flip()  ──  Mirror for natural interaction
     │
     ▼
MediaPipe Hands  ──  Detect 21 hand landmarks
     │
     ▼
GestureRecognizer  ──  Which fingers are up?
     │
     ├─ draw   ──  DrawingEngine.draw_line()
     ├─ move   ──  Reset previous point
     ├─ clear  ──  DrawingEngine.clear()
     └─ none   ──  Idle
     │
     ▼
Compose  ──  Blend canvas with camera frame
     │
     ▼
Display  ──  cv2.imshow()
```

**Key landmark:** MediaPipe landmark **#8** is the index fingertip.  
Its (x, y) pixel position drives all drawing operations.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot open camera" | Change `CAMERA_INDEX` in config.py (try 1, 2…) |
| Hand not detected | Improve lighting; reduce `DETECTION_CONFIDENCE` |
| Laggy performance | Lower `FRAME_WIDTH` / `FRAME_HEIGHT` in config.py |
| Shaky lines | Increase `TRACKING_CONFIDENCE` or slow your hand |
| mediapipe install fails | Check Python version is 3.8–3.11 |

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| opencv-python | ≥ 4.8 | Image capture, drawing, display |
| mediapipe | ≥ 0.10 | Hand landmark detection |
| numpy | ≥ 1.24 | Array operations |

---

## License

MIT — free to use, modify, and distribute.
