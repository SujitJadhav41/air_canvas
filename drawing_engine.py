"""
utils/drawing_engine.py
========================
Manages the virtual canvas (an in-memory image) and all drawing
operations: lines, erasing, clearing, and saving.
"""

import cv2
import numpy as np
import os
import time
from typing import Tuple


class DrawingEngine:
    """
    Maintains a transparent BGR canvas and exposes drawing primitives.

    The canvas is the same size as the camera frame.  Pixels that have
    not been drawn on are black (0, 0, 0) and are composited away
    by the main application loop.

    Parameters
    ----------
    width, height : int
        Canvas dimensions (should match the camera frame size).
    brush_size : int
        Default brush radius in pixels.
    eraser_size : int
        Default eraser half-size in pixels.
    """

    TOOL_PEN    = "pen"
    TOOL_ERASER = "eraser"

    def __init__(
        self,
        width:       int = 1280,
        height:      int = 720,
        brush_size:  int = 8,
        eraser_size: int = 30,
    ) -> None:
        self.width       = width
        self.height      = height
        self.brush_size  = brush_size
        self.eraser_size = eraser_size
        self.color       = (255, 0, 0)      # BGR – default blue
        self.tool        = self.TOOL_PEN

        self._canvas = np.zeros((height, width, 3), dtype=np.uint8)

    # ─────────────────────────────────────────────────────────────
    # Settings
    # ─────────────────────────────────────────────────────────────
    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Set the active drawing colour (BGR)."""
        self.color = color

    def set_tool(self, tool: str) -> None:
        """Set active tool: 'pen' or 'eraser'."""
        if tool in (self.TOOL_PEN, self.TOOL_ERASER):
            self.tool = tool

    def set_brush_size(self, size: int) -> None:
        """Set the brush (or eraser) radius."""
        if size > 0:
            self.brush_size = size

    # ─────────────────────────────────────────────────────────────
    # Drawing primitives
    # ─────────────────────────────────────────────────────────────
    def draw_line(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
    ) -> None:
        """
        Draw a line segment from (x1, y1) to (x2, y2) on the canvas.

        When the eraser tool is active the line is drawn in black
        (effectively removing prior marks) with the eraser size.
        """
        if self.tool == self.TOOL_ERASER:
            # Erase by drawing black thick line
            cv2.line(
                self._canvas,
                (x1, y1), (x2, y2),
                (0, 0, 0),
                self.eraser_size * 2,
                cv2.LINE_AA,
            )
            # Also erase with a filled circle at the endpoint
            cv2.circle(
                self._canvas,
                (x2, y2),
                self.eraser_size,
                (0, 0, 0),
                -1,
            )
        else:
            cv2.line(
                self._canvas,
                (x1, y1), (x2, y2),
                self.color,
                self.brush_size * 2,
                cv2.LINE_AA,
            )
            # Rounded cap at endpoint
            cv2.circle(
                self._canvas,
                (x2, y2),
                self.brush_size,
                self.color,
                -1,
            )

    def draw_point(self, x: int, y: int) -> None:
        """Draw a single dot at (x, y)."""
        if self.tool == self.TOOL_ERASER:
            cv2.circle(self._canvas, (x, y), self.eraser_size, (0, 0, 0), -1)
        else:
            cv2.circle(self._canvas, (x, y), self.brush_size, self.color, -1)

    def clear(self) -> None:
        """Wipe the entire canvas to black."""
        self._canvas[:] = 0

    # ─────────────────────────────────────────────────────────────
    # Canvas access
    # ─────────────────────────────────────────────────────────────
    def get_canvas(self) -> np.ndarray:
        """Return a reference to the internal canvas (BGR)."""
        return self._canvas

    def get_canvas_copy(self) -> np.ndarray:
        """Return a copy of the canvas."""
        return self._canvas.copy()

    # ─────────────────────────────────────────────────────────────
    # Save
    # ─────────────────────────────────────────────────────────────
    def save(self, directory: str = "saved_drawings") -> str:
        """
        Save the current canvas to a PNG file.

        Parameters
        ----------
        directory : str
            Folder to save into (created automatically if absent).

        Returns
        -------
        str
            Full path of the saved file.
        """
        os.makedirs(directory, exist_ok=True)
        filename = f"drawing_{int(time.time())}.png"
        path     = os.path.join(directory, filename)
        cv2.imwrite(path, self._canvas)
        return path

    def save_with_background(
        self,
        background: np.ndarray,
        directory: str = "saved_drawings",
    ) -> str:
        """
        Save the canvas composited onto *background* (the camera frame).

        Parameters
        ----------
        background : np.ndarray
            BGR image of the same size as the canvas.
        directory : str
            Output folder.

        Returns
        -------
        str
            Full path of the saved file.
        """
        mask     = cv2.cvtColor(self._canvas, cv2.COLOR_BGR2GRAY)
        _, mask  = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
        bg       = cv2.bitwise_and(background, background, mask=cv2.bitwise_not(mask))
        composite = cv2.add(bg, self._canvas)

        os.makedirs(directory, exist_ok=True)
        filename = f"drawing_bg_{int(time.time())}.png"
        path     = os.path.join(directory, filename)
        cv2.imwrite(path, composite)
        return path
