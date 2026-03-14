"""
utils/toolbar.py
=================
Renders and manages the top-of-screen toolbar.

Layout (left → right)
----------------------
 [CLEAR]  [Color1] [Color2] ... [ColorN]  [ERASER]  [Size−] [Size+]

Each item is a rectangular hit-zone.  When the index fingertip enters
a zone the corresponding action is activated.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Any

from utils.config import Config


class ToolbarItem:
    """Represents a single clickable button in the toolbar."""

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        label: str,
        color: Tuple[int, int, int],
        tool:  str = "pen",
        brush_size: int = 8,
    ) -> None:
        self.x          = x
        self.y          = y
        self.w          = w
        self.h          = h
        self.label      = label
        self.color      = color      # BGR
        self.tool       = tool
        self.brush_size = brush_size

    def contains(self, px: int, py: int) -> bool:
        """Return True if pixel (px, py) falls inside this button."""
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


class Toolbar:
    """
    Top-of-frame toolbar with colour swatches, eraser, and brush-size
    controls.

    Parameters
    ----------
    width  : int  Full frame width.
    height : int  Height of the toolbar band in pixels.
    """

    def __init__(self, width: int = 1280, height: int = 80) -> None:
        self.width  = width
        self.height = height
        self.config = Config()

        # Active state
        self._selected_color:      Tuple[int, int, int] = self.config.COLORS[0][0]
        self._selected_tool:       str = "pen"
        self._selected_brush_size: int = self.config.DEFAULT_BRUSH_SIZE

        self.items: List[ToolbarItem] = []
        self._build_items()

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────
    def _build_items(self) -> None:
        """Construct all toolbar buttons based on config colours."""
        pad    = 10
        btn_h  = self.height - 2 * pad
        btn_w  = btn_h              # square swatches
        gap    = 8
        cursor = pad

        # ── Clear button ─────────────────────────────────────────
        self.items.append(ToolbarItem(
            x=cursor, y=pad, w=btn_w + 10, h=btn_h,
            label="CLEAR",
            color=(50, 50, 50),
            tool="clear",
        ))
        cursor += btn_w + 10 + gap

        # ── Colour swatches ───────────────────────────────────────
        for (bgr, label) in self.config.COLORS:
            self.items.append(ToolbarItem(
                x=cursor, y=pad, w=btn_w, h=btn_h,
                label=label,
                color=bgr,
                tool="pen",
                brush_size=self._selected_brush_size,
            ))
            cursor += btn_w + gap

        # ── Eraser ───────────────────────────────────────────────
        self.items.append(ToolbarItem(
            x=cursor, y=pad, w=btn_w + 10, h=btn_h,
            label="ERASER",
            color=(180, 180, 180),
            tool="eraser",
        ))
        cursor += btn_w + 10 + gap

        # ── Brush size – ─────────────────────────────────────────
        self.items.append(ToolbarItem(
            x=cursor, y=pad, w=30, h=btn_h,
            label="-",
            color=(70, 70, 130),
            tool="size_down",
        ))
        cursor += 30 + gap

        # ── Brush size + ─────────────────────────────────────────
        self.items.append(ToolbarItem(
            x=cursor, y=pad, w=30, h=btn_h,
            label="+",
            color=(70, 130, 70),
            tool="size_up",
        ))

    # ─────────────────────────────────────────────────────────────
    # Interaction
    # ─────────────────────────────────────────────────────────────
    def handle_selection(self, x: int, y: int) -> None:
        """
        Called when the index fingertip is inside the toolbar band.
        Updates the active colour / tool depending on which button is hit.
        """
        for item in self.items:
            if item.contains(x, y):
                if item.tool == "clear":
                    pass                      # handled by main loop
                elif item.tool == "pen":
                    self._selected_color = item.color
                    self._selected_tool  = "pen"
                elif item.tool == "eraser":
                    self._selected_tool  = "eraser"
                elif item.tool == "size_down":
                    self._selected_brush_size = max(2, self._selected_brush_size - 2)
                elif item.tool == "size_up":
                    self._selected_brush_size = min(50, self._selected_brush_size + 2)
                break

    def get_selected(self) -> Dict[str, Any]:
        """Return a dict describing the currently active tool state."""
        return {
            "color":      self._selected_color,
            "tool":       self._selected_tool,
            "brush_size": self._selected_brush_size,
        }

    # ─────────────────────────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────────────────────────
    def render(self, frame: np.ndarray) -> None:
        """
        Draw the toolbar onto *frame* in-place.

        Draws a dark background strip, then each button with a label
        and a highlight ring for the currently active colour / tool.
        """
        # Background strip
        cv2.rectangle(
            frame,
            (0, 0), (self.width, self.height),
            (30, 30, 30),
            -1,
        )
        # Bottom border line
        cv2.line(
            frame,
            (0, self.height), (self.width, self.height),
            (80, 80, 80), 2,
        )

        for item in self.items:
            self._render_item(frame, item)

        # Brush size display (top-right)
        size_label = f"Brush: {self._selected_brush_size}px"
        cv2.putText(
            frame, size_label,
            (self.width - 160, self.height - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (200, 200, 200), 1, cv2.LINE_AA,
        )

    def _render_item(self, frame: np.ndarray, item: ToolbarItem) -> None:
        """Render a single toolbar button."""
        # Fill
        cv2.rectangle(
            frame,
            (item.x, item.y),
            (item.x + item.w, item.y + item.h),
            item.color,
            -1,
        )

        # Border
        border_color = (200, 200, 200)
        thickness    = 1

        # Highlight the active colour swatch
        if item.tool == "pen" and item.color == self._selected_color:
            border_color = (255, 255, 255)
            thickness    = 3
        elif item.tool == self._selected_tool and item.tool in ("eraser",):
            border_color = (255, 255, 0)
            thickness    = 3

        cv2.rectangle(
            frame,
            (item.x, item.y),
            (item.x + item.w, item.y + item.h),
            border_color,
            thickness,
        )

        # Label text (skip for colour swatches — colour is self-explanatory)
        if item.tool not in ("pen",):
            text_color = (255, 255, 255) if item.tool != "eraser" else (30, 30, 30)
            font_scale = 0.42 if len(item.label) > 3 else 0.55
            text_size, _ = cv2.getTextSize(
                item.label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
            )
            tx = item.x + (item.w - text_size[0]) // 2
            ty = item.y + (item.h + text_size[1]) // 2
            cv2.putText(
                frame, item.label,
                (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                text_color,
                1, cv2.LINE_AA,
            )
