"""
utils/gesture_recognizer.py
============================
Maps hand landmark data to named gestures used by Air Canvas.

Supported gestures
------------------
draw    – Only the index finger is up.
          → Draw a line on the canvas.

move    – Index AND middle fingers are up, rest down.
          → Reposition without drawing (pen-lift).

clear   – All five fingers are open / spread.
          → Wipe the canvas completely.

none    – Any other configuration.
          → Idle; no action.
"""

from typing import List, Tuple
from utils.hand_tracker import HandTracker


# Re-use the type alias from hand_tracker
LandmarkList = List[Tuple[float, float, float]]


class GestureRecognizer:
    """
    Stateless gesture classifier.

    Uses the HandTracker.fingers_up() helper internally so that
    the landmark format matches exactly.
    """

    def __init__(self) -> None:
        # We use HandTracker only for its fingers_up() utility;
        # no camera / MediaPipe initialisation is done here.
        self._tracker = HandTracker.__new__(HandTracker)

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────
    def recognize(self, landmarks: LandmarkList) -> str:
        """
        Classify the hand pose described by *landmarks*.

        Parameters
        ----------
        landmarks : LandmarkList
            21 (x, y, z) normalised tuples from HandTracker.

        Returns
        -------
        str
            One of: 'draw', 'move', 'clear', 'none'
        """
        up = self._fingers_up(landmarks)
        # up = [Thumb, Index, Middle, Ring, Pinky]

        # ── Clear ─────────────────────────────────────────────
        # All four non-thumb fingers extended (thumb state ignored)
        if up[1] and up[2] and up[3] and up[4]:
            return "clear"

        # ── Move (pen-lift) ───────────────────────────────────
        # Index + Middle up, Ring + Pinky down
        if up[1] and up[2] and not up[3] and not up[4]:
            return "move"

        # ── Draw ──────────────────────────────────────────────
        # Only index finger up
        if up[1] and not up[2] and not up[3] and not up[4]:
            return "draw"

        return "none"

    # ─────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────
    def _fingers_up(self, landmarks: LandmarkList) -> List[bool]:
        """
        Determine which fingers are extended.

        Returns [Thumb, Index, Middle, Ring, Pinky] booleans.
        A finger is 'up' when its tip is above its MCP (knuckle) joint.
        The thumb uses the x-axis comparison (lateral movement).
        """
        # Landmark indices
        THUMB_TIP  = 4
        INDEX_TIP  = 8;  INDEX_MCP  = 5
        MIDDLE_TIP = 12; MIDDLE_MCP = 9
        RING_TIP   = 16; RING_MCP   = 13
        PINKY_TIP  = 20; PINKY_MCP  = 17

        up = [False] * 5

        # Thumb (x-axis, mirrored frame)
        up[0] = landmarks[THUMB_TIP][0] < landmarks[THUMB_TIP - 1][0]

        # Other four fingers (y-axis: smaller y = higher on screen)
        pairs = [
            (INDEX_TIP,  INDEX_MCP,  1),
            (MIDDLE_TIP, MIDDLE_MCP, 2),
            (RING_TIP,   RING_MCP,   3),
            (PINKY_TIP,  PINKY_MCP,  4),
        ]
        for tip, mcp, idx in pairs:
            up[idx] = landmarks[tip][1] < landmarks[mcp][1]

        return up
