"""
utils/hand_tracker.py
=====================
Wraps MediaPipe Hands to detect hand landmarks.

Landmark indices (0-20):
    0  Wrist
    4  Thumb tip
    8  Index finger tip   ← primary drawing point
    12 Middle finger tip
    16 Ring finger tip
    20 Pinky tip

Each landmark is returned as a normalised (x, y, z) tuple
where x and y are in [0, 1] relative to the frame size.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Optional, Tuple


# Type alias: list of 21 (x, y, z) tuples
LandmarkList = List[Tuple[float, float, float]]


class HandTracker:
    """
    Detects hands in an RGB image and returns per-hand landmark lists.

    Parameters
    ----------
    max_hands : int
        Maximum number of hands to detect simultaneously.
    detection_confidence : float
        Minimum confidence for initial hand detection (0.0 – 1.0).
    tracking_confidence : float
        Minimum confidence to keep tracking between frames (0.0 – 1.0).
    draw_landmarks : bool
        If True, draws the MediaPipe skeleton on *frame* in-place.
    """

    # MediaPipe hand landmark indices
    WRIST           = 0
    THUMB_TIP       = 4
    INDEX_TIP       = 8
    MIDDLE_TIP      = 12
    RING_TIP        = 16
    PINKY_TIP       = 20

    # MCP (knuckle) joints – used for "finger up" detection
    INDEX_MCP       = 5
    MIDDLE_MCP      = 9
    RING_MCP        = 13
    PINKY_MCP       = 17

    def __init__(
        self,
        max_hands: int = 1,
        detection_confidence: float = 0.8,
        tracking_confidence:  float = 0.7,
        draw_landmarks: bool = True,
    ) -> None:
        self.draw_landmarks = draw_landmarks

        self._mp_hands   = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_styles  = mp.solutions.drawing_styles

        self.hands = self._mp_hands.Hands(
            static_image_mode        = False,
            max_num_hands            = max_hands,
            min_detection_confidence = detection_confidence,
            min_tracking_confidence  = tracking_confidence,
        )

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────
    def find_hands(
        self,
        frame_rgb: np.ndarray,
        frame_bgr: Optional[np.ndarray] = None,
    ) -> List[LandmarkList]:
        """
        Process a single frame and return landmark data.

        Parameters
        ----------
        frame_rgb : np.ndarray
            The frame in RGB format (required by MediaPipe).
        frame_bgr : np.ndarray, optional
            The original BGR frame; landmark skeleton is drawn here
            when *draw_landmarks* is True.

        Returns
        -------
        List[LandmarkList]
            One list per detected hand, each containing 21 (x, y, z)
            tuples with normalised coordinates.
        """
        results = self.hands.process(frame_rgb)

        all_hands: List[LandmarkList] = []

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                # Draw skeleton on the BGR frame if requested
                if self.draw_landmarks and frame_bgr is not None:
                    self._mp_drawing.draw_landmarks(
                        frame_bgr,
                        hand_lms,
                        self._mp_hands.HAND_CONNECTIONS,
                        self._mp_styles.get_default_hand_landmarks_style(),
                        self._mp_styles.get_default_hand_connections_style(),
                    )

                # Collect normalised (x, y, z) for each landmark
                landmarks: LandmarkList = []
                for lm in hand_lms.landmark:
                    landmarks.append((lm.x, lm.y, lm.z))

                all_hands.append(landmarks)

        return all_hands

    def get_finger_positions(
        self,
        landmarks: LandmarkList,
        frame_width:  int,
        frame_height: int,
    ) -> dict:
        """
        Convert normalised landmarks to pixel coordinates for the
        five fingertips and the wrist.

        Returns
        -------
        dict
            Keys: 'wrist', 'thumb', 'index', 'middle', 'ring', 'pinky'
            Values: (x_px, y_px) tuples.
        """
        def px(idx: int) -> Tuple[int, int]:
            x = int(landmarks[idx][0] * frame_width)
            y = int(landmarks[idx][1] * frame_height)
            return (x, y)

        return {
            "wrist":  px(self.WRIST),
            "thumb":  px(self.THUMB_TIP),
            "index":  px(self.INDEX_TIP),
            "middle": px(self.MIDDLE_TIP),
            "ring":   px(self.RING_TIP),
            "pinky":  px(self.PINKY_TIP),
        }

    def fingers_up(self, landmarks: LandmarkList) -> List[bool]:
        """
        Return a boolean list indicating which fingers are extended.

        Index mapping:
            [0] Thumb  [1] Index  [2] Middle  [3] Ring  [4] Pinky

        A finger is considered *up* when its tip is above (lower y value
        than) the corresponding MCP joint.  The thumb uses the x-axis
        because it moves laterally.
        """
        up = [False] * 5

        # Thumb – compare x coordinate (assumes mirrored frame)
        up[0] = landmarks[self.THUMB_TIP][0] < landmarks[self.THUMB_TIP - 1][0]

        # Four fingers – compare y coordinate
        pairs = [
            (self.INDEX_TIP,  self.INDEX_MCP),
            (self.MIDDLE_TIP, self.MIDDLE_MCP),
            (self.RING_TIP,   self.RING_MCP),
            (self.PINKY_TIP,  self.PINKY_MCP),
        ]
        for i, (tip, mcp) in enumerate(pairs, start=1):
            up[i] = landmarks[tip][1] < landmarks[mcp][1]

        return up

    def close(self) -> None:
        """Release MediaPipe resources."""
        self.hands.close()
