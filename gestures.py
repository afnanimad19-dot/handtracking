"""
gestures.py — reusable gesture detection on top of MediaPipe hand landmarks.

This turns raw 21-point hand landmarks into high-level INPUT EVENTS you can
wire to any action (move a cursor, drag a card, swipe a page, trigger a
CRM shortcut, etc.):

    PINCH_START  -> thumb + index tips came together (like grabbing)
    PINCH_MOVE   -> hand moved while still pinching (use for DRAG)
    PINCH_END    -> pinch released (like a click or a "drop")
    SWIPE_LEFT / SWIPE_RIGHT -> fast horizontal flick with an open hand
    FIST         -> all fingers closed
    OPEN_PALM    -> all five fingers extended

Usage (see demo_virtual_objects.py and demo_mouse_control.py):

    tracker = GestureTracker()
    events, state = tracker.update(hand_landmarks, handedness_label, frame_w, frame_h)
    for ev in events:
        if ev.name == "PINCH_START": ...

Design notes:
  * Pinch distance is normalized by hand size (wrist -> middle-finger base),
    so detection works whether the hand is near or far from the camera.
  * Hysteresis (two thresholds) stops the pinch from flickering on/off.
  * Cursor position is exponentially smoothed to remove jitter.
"""

import math
import time
from dataclasses import dataclass, field

# Landmark indices (MediaPipe hand model)
WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

# Pinch hysteresis: start when normalized distance drops below PINCH_ON,
# release only when it rises above PINCH_OFF.
PINCH_ON = 0.32
PINCH_OFF = 0.45

# Swipe: open-hand horizontal speed (fraction of frame width per second)
SWIPE_SPEED = 1.6
SWIPE_COOLDOWN = 0.8  # seconds between swipes

SMOOTHING = 0.35  # 0 = frozen, 1 = raw (no smoothing)


@dataclass
class GestureEvent:
    name: str          # e.g. "PINCH_START"
    hand: str          # "Left" or "Right"
    x: int = 0         # pixel position (index fingertip / pinch midpoint)
    y: int = 0


@dataclass
class HandState:
    pinching: bool = False
    smooth_x: float = None
    smooth_y: float = None
    last_x: float = None
    last_t: float = None
    last_swipe_t: float = 0.0
    last_pinch_end_t: float = 0.0
    fingers_up: int = 0
    pose: str = ""     # "FIST", "OPEN_PALM", or ""


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def count_fingers_up(lm, handedness_label):
    """Same simple finger counting as hand_tracking.py."""
    up = 0
    for tip_id in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]:
        if lm[tip_id].y < lm[tip_id - 2].y:
            up += 1
    if handedness_label == "Right":
        if lm[THUMB_TIP].x < lm[THUMB_TIP - 1].x:
            up += 1
    else:
        if lm[THUMB_TIP].x > lm[THUMB_TIP - 1].x:
            up += 1
    return up


class GestureTracker:
    """Tracks gesture state per hand ("Left"/"Right") and emits events."""

    def __init__(self):
        self.hands = {"Left": HandState(), "Right": HandState()}

    def update(self, hand_landmarks, handedness_label, frame_w, frame_h):
        """Feed one hand's landmarks for the current frame.

        Returns (events, state):
          events -> list of GestureEvent fired this frame
          state  -> the HandState (smooth_x/smooth_y = smoothed cursor pixels)
        """
        lm = hand_landmarks.landmark
        st = self.hands[handedness_label]
        events = []
        now = time.time()

        # --- Normalized pinch distance (scale-invariant) ---
        hand_size = _dist(lm[WRIST], lm[MIDDLE_MCP])
        if hand_size < 1e-6:
            return events, st
        pinch_dist = _dist(lm[THUMB_TIP], lm[INDEX_TIP]) / hand_size

        # --- Cursor point: midpoint of thumb & index while pinching,
        #     index fingertip otherwise ---
        if st.pinching:
            cx = (lm[THUMB_TIP].x + lm[INDEX_TIP].x) / 2
            cy = (lm[THUMB_TIP].y + lm[INDEX_TIP].y) / 2
        else:
            cx, cy = lm[INDEX_TIP].x, lm[INDEX_TIP].y

        # --- Exponential smoothing ---
        if st.smooth_x is None:
            st.smooth_x, st.smooth_y = cx, cy
        else:
            st.smooth_x += SMOOTHING * (cx - st.smooth_x)
            st.smooth_y += SMOOTHING * (cy - st.smooth_y)
        px = int(st.smooth_x * frame_w)
        py = int(st.smooth_y * frame_h)

        # --- Finger count & static poses ---
        st.fingers_up = count_fingers_up(lm, handedness_label)
        new_pose = ""
        if st.fingers_up == 0 and not st.pinching:
            new_pose = "FIST"
        elif st.fingers_up == 5:
            new_pose = "OPEN_PALM"
        if new_pose and new_pose != st.pose:
            events.append(GestureEvent(new_pose, handedness_label, px, py))
        st.pose = new_pose

        # --- Pinch state machine with hysteresis ---
        if not st.pinching and pinch_dist < PINCH_ON:
            st.pinching = True
            events.append(GestureEvent("PINCH_START", handedness_label, px, py))
        elif st.pinching and pinch_dist > PINCH_OFF:
            st.pinching = False
            st.last_pinch_end_t = now
            events.append(GestureEvent("PINCH_END", handedness_label, px, py))
        elif st.pinching:
            events.append(GestureEvent("PINCH_MOVE", handedness_label, px, py))

        # --- Swipe detection (open hand moving fast horizontally) ---
        if st.last_x is not None and st.last_t is not None:
            dt = now - st.last_t
            if dt > 0:
                vx = (st.smooth_x - st.last_x) / dt  # frame-widths per second
                if (st.fingers_up >= 4 and not st.pinching
                        and abs(vx) > SWIPE_SPEED
                        and now - st.last_swipe_t > SWIPE_COOLDOWN
                        and now - st.last_pinch_end_t > SWIPE_COOLDOWN):
                    name = "SWIPE_RIGHT" if vx > 0 else "SWIPE_LEFT"
                    events.append(GestureEvent(name, handedness_label, px, py))
                    st.last_swipe_t = now
        st.last_x, st.last_t = st.smooth_x, now

        return events, st
