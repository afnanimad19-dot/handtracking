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
    palm_hold_start: float = None
    palm_hold_fired: bool = False
    # Raw measurements exposed for the calibration wizard
    last_pinch_dist: float = 999.0
    last_vx: float = 0.0
    fingers_up: int = 0
    pose: str = ""     # "FIST", "OPEN_PALM", or ""


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


PINKY_MCP = 17


def count_fingers_up(lm, handedness_label):
    """Rotation-invariant finger counting.

    A finger is 'up' (extended) when its TIP is farther from the wrist than
    its PIP joint. Unlike comparing y coordinates, this works when the hand
    is tilted sideways — which happens naturally during swipes.
    """
    wrist = lm[WRIST]
    up = 0
    for tip_id in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]:
        if _dist(lm[tip_id], wrist) > _dist(lm[tip_id - 2], wrist):
            up += 1
    # Thumb: extended when its tip is farther from the pinky base than its
    # joint is (works for both hands, any rotation).
    if _dist(lm[THUMB_TIP], lm[PINKY_MCP]) > _dist(lm[THUMB_TIP - 1], lm[PINKY_MCP]):
        up += 1
    return up


PALM_HOLD_SECONDS = 2.0  # hold an open palm this long to fire PALM_HOLD


class GestureTracker:
    """Tracks gesture state per hand ("Left"/"Right") and emits events.

    Thresholds can be overridden per install (see presenter_app.py's
    calibration wizard): GestureTracker(pinch_on=0.3, swipe_speed=1.2)
    """

    def __init__(self, pinch_on=PINCH_ON, pinch_off=PINCH_OFF,
                 swipe_speed=SWIPE_SPEED):
        self.pinch_on = pinch_on
        self.pinch_off = pinch_off
        self.swipe_speed = swipe_speed
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
        st.last_pinch_dist = pinch_dist

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
        elif st.fingers_up >= 4:
            new_pose = "OPEN_PALM"
        if new_pose and new_pose != st.pose:
            events.append(GestureEvent(new_pose, handedness_label, px, py))
        st.pose = new_pose

        # --- PALM_HOLD: open palm held steady for PALM_HOLD_SECONDS ---
        if st.pose == "OPEN_PALM":
            if st.palm_hold_start is None:
                st.palm_hold_start = now
            elif (not st.palm_hold_fired
                    and now - st.palm_hold_start >= PALM_HOLD_SECONDS):
                events.append(GestureEvent("PALM_HOLD", handedness_label, px, py))
                st.palm_hold_fired = True
        else:
            st.palm_hold_start = None
            st.palm_hold_fired = False

        # --- Pinch state machine with hysteresis ---
        if not st.pinching and pinch_dist < self.pinch_on:
            st.pinching = True
            events.append(GestureEvent("PINCH_START", handedness_label, px, py))
        elif st.pinching and pinch_dist > self.pinch_off:
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
                st.last_vx = vx
                # No finger-count requirement: counting is unreliable at
                # distance/odd angles. A deliberate fast flick IS the signal.
                if (not st.pinching
                        and abs(vx) > self.swipe_speed
                        and now - st.last_swipe_t > SWIPE_COOLDOWN
                        and now - st.last_pinch_end_t > SWIPE_COOLDOWN):
                    name = "SWIPE_RIGHT" if vx > 0 else "SWIPE_LEFT"
                    events.append(GestureEvent(name, handedness_label, px, py))
                    st.last_swipe_t = now
        st.last_x, st.last_t = st.smooth_x, now

        return events, st
