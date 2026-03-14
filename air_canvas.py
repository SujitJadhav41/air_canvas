"""
air_canvas.py
=============
Core application class that ties together the webcam feed,
hand tracking, gesture recognition, and drawing engine.
"""

import cv2
import numpy as np
import time

from utils.hand_tracker import HandTracker
from utils.gesture_recognizer import GestureRecognizer
from utils.drawing_engine import DrawingEngine
from utils.toolbar import Toolbar
from utils.config import Config


class AirCanvas:
    """
    Main Air Canvas application.

    Manages the main loop:
      1. Capture frame from webcam
      2. Detect hand landmarks
      3. Recognize gesture
      4. Update drawing canvas
      5. Compose and display final frame
    """

    def __init__(self):
        self.config = Config()

        # ── Camera ──────────────────────────────────────────────
        self.cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS,          self.config.CAMERA_FPS)

        # ── Sub-systems ─────────────────────────────────────────
        self.tracker    = HandTracker(
            max_hands            = self.config.MAX_HANDS,
            detection_confidence = self.config.DETECTION_CONFIDENCE,
            tracking_confidence  = self.config.TRACKING_CONFIDENCE,
        )
        self.recognizer = GestureRecognizer()
        self.engine     = DrawingEngine(
            width      = self.config.FRAME_WIDTH,
            height     = self.config.FRAME_HEIGHT,
            brush_size = self.config.DEFAULT_BRUSH_SIZE,
            eraser_size= self.config.DEFAULT_ERASER_SIZE,
        )
        self.toolbar = Toolbar(
            width  = self.config.FRAME_WIDTH,
            height = self.config.TOOLBAR_HEIGHT,
        )

        # ── State ────────────────────────────────────────────────
        self.prev_x: int = 0
        self.prev_y: int = 0
        self.drawing: bool = False
        self.fps_counter: list = []

    # ─────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────
    def run(self) -> None:
        """Start the main application loop."""
        print("[AirCanvas] Starting… Press Q or ESC to quit, S to save.")

        if not self.cap.isOpened():
            print("[ERROR] Cannot open camera. Check CAMERA_INDEX in config.py")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)          # mirror for natural interaction
            h, w  = frame.shape[:2]

            # ── FPS bookkeeping ──────────────────────────────────
            t_now = time.time()
            self.fps_counter.append(t_now)
            self.fps_counter = [t for t in self.fps_counter if t_now - t < 1.0]
            fps = len(self.fps_counter)

            # ── Hand tracking ────────────────────────────────────
            frame_rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks   = self.tracker.find_hands(frame_rgb, frame)

            gesture     = "none"
            index_x, index_y = 0, 0

            if landmarks:
                lm = landmarks[0]           # use first detected hand

                # Fingertip coordinates (index = landmark 8)
                index_x = int(lm[8][0] * w)
                index_y = int(lm[8][1] * h)

                # Recognize gesture
                gesture = self.recognizer.recognize(lm)

                # ── Toolbar interaction ──────────────────────────
                if index_y < self.config.TOOLBAR_HEIGHT:
                    self.toolbar.handle_selection(index_x, index_y)
                    selected = self.toolbar.get_selected()
                    self.engine.set_color(selected["color"])
                    self.engine.set_tool(selected["tool"])
                    self.engine.set_brush_size(selected["brush_size"])
                    self.drawing = False
                    self.prev_x, self.prev_y = 0, 0

                # ── Drawing area ─────────────────────────────────
                else:
                    if gesture == "draw":
                        if self.prev_x == 0 and self.prev_y == 0:
                            self.prev_x, self.prev_y = index_x, index_y

                        self.engine.draw_line(
                            self.prev_x, self.prev_y,
                            index_x,    index_y,
                        )
                        self.drawing = True
                    elif gesture == "move":
                        self.drawing = False
                        self.prev_x, self.prev_y = 0, 0
                    elif gesture == "clear":
                        self.engine.clear()
                        self.drawing = False
                        self.prev_x, self.prev_y = 0, 0

                    if gesture == "draw":
                        self.prev_x, self.prev_y = index_x, index_y
                    else:
                        self.prev_x, self.prev_y = 0, 0

            else:
                self.drawing = False
                self.prev_x, self.prev_y = 0, 0

            # ── Compose final frame ──────────────────────────────
            output = self._compose(frame)

            # ── Overlay UI ───────────────────────────────────────
            self._draw_toolbar_ui(output)
            self._draw_hud(output, gesture, fps, index_x, index_y)

            # ── Draw cursor ──────────────────────────────────────
            if landmarks:
                self._draw_cursor(output, index_x, index_y, gesture)

            cv2.imshow("Air Canvas", output)

            # ── Key handling ─────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):       # Q or ESC → quit
                break
            elif key == ord('s'):           # S → save
                path = self.engine.save()
                print(f"[AirCanvas] Saved → {path}")

        self.cap.release()
        cv2.destroyAllWindows()
        print("[AirCanvas] Exited.")

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _compose(self, frame: np.ndarray) -> np.ndarray:
        """Blend the live camera frame with the drawing canvas."""
        canvas = self.engine.get_canvas()

        # Create a mask where canvas has non-black pixels
        mask = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

        # Remove drawing area from frame, then add canvas
        frame_bg = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
        result   = cv2.add(frame_bg, canvas)
        return result

    def _draw_toolbar_ui(self, frame: np.ndarray) -> None:
        """Render the toolbar panel on top of the frame."""
        self.toolbar.render(frame)

    def _draw_hud(
        self,
        frame: np.ndarray,
        gesture: str,
        fps: int,
        ix: int,
        iy: int,
    ) -> None:
        """Draw FPS counter, gesture label, and coordinates."""
        h, w = frame.shape[:2]

        # FPS
        cv2.putText(
            frame, f"FPS: {fps}",
            (w - 110, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (0, 255, 0), 2, cv2.LINE_AA,
        )

        # Gesture
        gesture_colors = {
            "draw":  (0, 255, 100),
            "move":  (255, 200, 0),
            "clear": (0, 0, 255),
            "none":  (150, 150, 150),
        }
        color = gesture_colors.get(gesture, (200, 200, 200))
        cv2.putText(
            frame, f"Gesture: {gesture.upper()}",
            (10, h - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65,
            color, 2, cv2.LINE_AA,
        )

        # Coordinates (only when hand detected)
        if ix or iy:
            cv2.putText(
                frame, f"({ix}, {iy})",
                (10, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (200, 200, 200), 1, cv2.LINE_AA,
            )

    def _draw_cursor(
        self,
        frame: np.ndarray,
        x: int,
        y: int,
        gesture: str,
    ) -> None:
        """Draw a circle cursor at the index fingertip."""
        tool = self.toolbar.get_selected()["tool"]

        if gesture == "draw":
            radius = self.engine.brush_size
            color  = self.engine.color
            cv2.circle(frame, (x, y), radius, color, -1)
            cv2.circle(frame, (x, y), radius + 2, (255, 255, 255), 1)
        elif gesture == "move":
            cv2.circle(frame, (x, y), 12, (255, 200, 0), 2)
            cv2.circle(frame, (x, y), 3,  (255, 200, 0), -1)
        elif tool == "eraser":
            r = self.engine.eraser_size
            cv2.rectangle(
                frame,
                (x - r, y - r), (x + r, y + r),
                (200, 200, 200), 2,
            )
        else:
            cv2.circle(frame, (x, y), 8,  (255, 255, 255), 2)
            cv2.circle(frame, (x, y), 2,  (255, 255, 255), -1)
