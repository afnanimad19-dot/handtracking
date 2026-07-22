"""
presenter_app.py — the SELLABLE version of the hand-only presenter.

What it adds over demo_presenter.py:
  * Calibration wizard (run once per room/camera):  python presenter_app.py --calibrate
      - measures YOUR pinch and YOUR swipe speed in THIS lighting
      - saves thresholds to config.json
  * Loads config.json automatically on every run
  * On-screen gesture hint bar (clients trust what they can read)
  * PALM HOLD (open hand steady 2s) -> black screen toggle ('B' in PowerPoint)

Two clear modes, toggled by holding up TWO FINGERS (peace sign) for half a
second — a big indicator on screen shows which mode you're in:

  PEN OFF (default — navigate):
    open-hand swipe   next / previous slide
    point (1 finger)  pointer follows your finger
    pinch             does NOTHING (so you can't draw by accident)
  PEN ON (annotate):
    pinch + move      draw on the slide (PowerPoint: Ctrl+P once for pen mode)
    fist              erase drawings ('E')
    swiping           disabled (so you can't change slides mid-drawing)
  Both modes:
    palm hold 2s      black screen on/off ('B')

Run:
  python presenter_app.py --calibrate    # first time in a new room
  python presenter_app.py                # present

Press Q in the camera window to quit. pyautogui failsafe: slam the real
mouse into the top-left screen corner to abort.
"""

import argparse
import json
import os
import platform
import time

import cv2
import mediapipe as mp
import pyautogui

from gestures import GestureTracker, PINCH_ON, PINCH_OFF, SWIPE_SPEED

CAMERA_INDEX = 0
FLIP_CAMERA = True
FRAME_MARGIN = 0.2
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

HINTS_OFF = "SWIPE slides | POINT pointer | 2 FINGERS 0.5s = pen ON | PALM 2s black"
HINTS_ON = "PINCH draw | FIST erase | 2 FINGERS 0.5s = pen OFF | PALM 2s black"

PEN_TOGGLE_HOLD = 0.5   # seconds the two-finger pose must be held
PEN_TOGGLE_COOLDOWN = 1.5


def load_config():
    cfg = {"pinch_on": PINCH_ON, "pinch_off": PINCH_OFF, "swipe_speed": SWIPE_SPEED}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg.update(json.load(f))
            print(f"[config] loaded {CONFIG_FILE}: {cfg}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[config] could not read {CONFIG_FILE} ({e}); using defaults")
    else:
        print("[config] no config.json — using defaults. "
              "Run 'python presenter_app.py --calibrate' once per room.")
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"[config] saved {CONFIG_FILE}: {cfg}")


def open_camera():
    backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_INDEX, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
    return cap


def make_hands():
    return mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )


def banner(frame, lines):
    """Draw instruction lines on a dark strip at the top of the frame."""
    h, w = frame.shape[:2]
    strip_h = 30 + 28 * len(lines)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, strip_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (15, 30 + 28 * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)


def calibrate():
    """Guided wizard: measure the user's pinch and swipe, save config.json."""
    cap = open_camera()
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return
    hands = make_hands()
    tracker = GestureTracker()

    # Phase 1: pinch — collect distances while OPEN (fingers apart) and
    # while CLOSED (pinching) for ~4 seconds each.
    # Phase 2: swipe — record peak horizontal speeds of 3 swipes.
    phase = "open"
    phase_start = None
    open_samples, closed_samples, swipe_peaks = [], [], []
    current_peak = 0.0

    print("Calibration started. Follow the on-screen instructions.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_visible = bool(results.multi_hand_landmarks)
        if hand_visible:
            hand_landmarks = results.multi_hand_landmarks[0]
            label = results.multi_handedness[0].classification[0].label
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
            _, st = tracker.update(hand_landmarks, label, w, h)

            if phase_start is None:
                phase_start = time.time()
            elapsed = time.time() - phase_start

            if phase == "open":
                banner(frame, ["STEP 1/3: hold your hand OPEN, fingers apart",
                               f"measuring... {max(0, 4 - int(elapsed))}s"])
                if elapsed > 1:  # skip the first second (hand settling)
                    open_samples.append(st.last_pinch_dist)
                if elapsed >= 4:
                    phase, phase_start = "closed", None
            elif phase == "closed":
                banner(frame, ["STEP 2/3: PINCH and HOLD (thumb touching index)",
                               f"measuring... {max(0, 4 - int(elapsed))}s"])
                if elapsed > 1:
                    closed_samples.append(st.last_pinch_dist)
                if elapsed >= 4:
                    phase, phase_start = "swipe", None
            elif phase == "swipe":
                banner(frame, ["STEP 3/3: swipe your OPEN hand fast, left or right",
                               f"swipes recorded: {len(swipe_peaks)}/3"])
                speed = abs(st.last_vx)
                current_peak = max(current_peak, speed)
                # A swipe "ends" when the hand slows back down
                if current_peak > 0.6 and speed < 0.25:
                    swipe_peaks.append(current_peak)
                    current_peak = 0.0
                if len(swipe_peaks) >= 3:
                    break
        else:
            banner(frame, ["Show one hand to the camera to begin"])
            phase_start = None

        cv2.imshow("Calibration", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            print("Calibration cancelled.")
            hands.close(); cap.release(); cv2.destroyAllWindows()
            return

    hands.close(); cap.release(); cv2.destroyAllWindows()

    open_d = sorted(open_samples)[len(open_samples) // 2]      # median
    closed_d = sorted(closed_samples)[len(closed_samples) // 2]
    if closed_d >= open_d:
        print("[ERROR] Pinch was not smaller than open hand — bad lighting or "
              "camera angle. Try again facing the camera, better light.")
        return

    # Thresholds: ON at 1/3 of the way from closed to open, OFF at 2/3.
    span = open_d - closed_d
    if span < 0.15:
        print(f"[WARN] Pinch and open hand look too similar (span {span:.2f}). "
              "Calibration saved, but if pinch misbehaves: improve lighting, "
              "face the camera, and recalibrate.")

    # Clamp to sane ranges so a bad calibration can never lock the app
    # into permanent pinching (thresholds outside these bounds are noise).
    pinch_on = min(max(closed_d + 0.33 * span, 0.15), 0.45)
    pinch_off = min(max(closed_d + 0.66 * span, pinch_on + 0.12), 0.75)
    cfg = {
        "pinch_on": round(pinch_on, 3),
        "pinch_off": round(pinch_off, 3),
        # Trigger at 60% of the user's average swipe peak
        # 60% of the user's average swipe peak, clamped so the threshold
        # is always reachable in normal use
        "swipe_speed": round(min(max(0.6 * (sum(swipe_peaks) / len(swipe_peaks)),
                                     0.5), 1.8), 3),
    }
    save_config(cfg)
    print("Calibration done. Run 'python presenter_app.py' to present.")


def present(cfg):
    cap = open_camera()
    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Try changing CAMERA_INDEX (0, 1, or 2).")
        return
    hands = make_hands()
    tracker = GestureTracker(pinch_on=cfg["pinch_on"],
                             pinch_off=cfg["pinch_off"],
                             swipe_speed=cfg["swipe_speed"])
    screen_w, screen_h = pyautogui.size()
    drawing = False
    pen_mode = False
    two_finger_start = None
    last_pen_toggle = 0.0
    flash_msg, flash_until = "", 0.0

    print("Presenter running. Two fingers (peace sign) 0.5s toggles pen mode. Q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks and results.multi_handedness:
            hand_landmarks = results.multi_hand_landmarks[0]
            label = results.multi_handedness[0].classification[0].label
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
            events, state = tracker.update(hand_landmarks, label, w, h)
            px = int(state.smooth_x * w)
            py = int(state.smooth_y * h)

            if drawing or state.fingers_up <= 2:
                x0, x1 = FRAME_MARGIN * w, (1 - FRAME_MARGIN) * w
                y0, y1 = FRAME_MARGIN * h, (1 - FRAME_MARGIN) * h
                nx = min(max((px - x0) / (x1 - x0), 0.0), 1.0)
                ny = min(max((py - y0) / (y1 - y0), 0.0), 1.0)
                pyautogui.moveTo(int(nx * (screen_w - 1)), int(ny * (screen_h - 1)))

            # --- Pen mode toggle: two fingers (peace sign) held 0.5s ---
            now = time.time()
            if state.fingers_up == 2 and not state.pinching:
                if two_finger_start is None:
                    two_finger_start = now
                elif (now - two_finger_start >= PEN_TOGGLE_HOLD
                        and now - last_pen_toggle >= PEN_TOGGLE_COOLDOWN):
                    pen_mode = not pen_mode
                    last_pen_toggle = now
                    two_finger_start = None
                    if not pen_mode and drawing:  # releases a stuck marker
                        pyautogui.mouseUp(); drawing = False
                    flash_msg = "PEN ON - pinch to draw" if pen_mode else "PEN OFF - swipe to navigate"
                    flash_until = now + 1.5
            else:
                two_finger_start = None

            for ev in events:
                if ev.name == "PINCH_START" and not pen_mode:
                    flash_msg = "PEN is OFF - hold 2 fingers 0.5s to enable drawing"
                    flash_until = time.time() + 1.5
                elif ev.name == "PINCH_START" and pen_mode and not drawing:
                    pyautogui.mouseDown(); drawing = True
                elif ev.name == "PINCH_END" and drawing:
                    pyautogui.mouseUp(); drawing = False
                elif ev.name == "SWIPE_RIGHT" and not pen_mode:
                    pyautogui.press("right"); flash_msg = "NEXT slide"
                    flash_until = time.time() + 1
                elif ev.name == "SWIPE_LEFT" and not pen_mode:
                    pyautogui.press("left"); flash_msg = "PREVIOUS slide"
                    flash_until = time.time() + 1
                elif ev.name == "FIST" and pen_mode:
                    pyautogui.press("e"); flash_msg = "erase"
                    flash_until = time.time() + 1
                elif ev.name == "PALM_HOLD":
                    pyautogui.press("b"); flash_msg = "black screen"
                    flash_until = time.time() + 1

            # Cursor / pen visuals
            if pen_mode:
                # Dots on thumb tip and index tip; the white dot between
                # them is the pen point — touch the two dots together to ink.
                lm = hand_landmarks.landmark
                tx, ty = int(lm[4].x * w), int(lm[4].y * h)
                ix, iy = int(lm[8].x * w), int(lm[8].y * h)
                col = (0, 0, 255) if drawing else (0, 255, 255)
                cv2.circle(frame, (tx, ty), 9, col, -1)
                cv2.circle(frame, (ix, iy), 9, col, -1)
                cv2.line(frame, (tx, ty), (ix, iy), col, 2)
                cv2.circle(frame, ((tx + ix) // 2, (ty + iy) // 2), 5,
                           (255, 255, 255), -1)
            else:
                cv2.circle(frame, (px, py), 10, (0, 0, 255), -1)

            # Live readout: WHY a gesture does / doesn't fire
            speed = abs(state.last_vx)
            need = cfg["swipe_speed"]
            dbg = (f"fingers:{state.fingers_up}  "
                   f"speed:{speed:.2f}/{need:.2f}  "
                   f"pinch:{state.last_pinch_dist:.2f} "
                   f"(on<{cfg['pinch_on']:.2f} off>{cfg['pinch_off']:.2f})")
            cv2.putText(frame, dbg, (10, h - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 255, 0) if state.fingers_up >= 3 else (0, 180, 255), 2)
        elif drawing:
            pyautogui.mouseUp(); drawing = False

        # Big mode indicator + hints
        h_frame, w_frame = frame.shape[:2]
        mode_txt = "PEN ON" if pen_mode else "PEN OFF"
        mode_col = (0, 0, 255) if pen_mode else (0, 200, 0)
        lines = [HINTS_ON if pen_mode else HINTS_OFF]
        if time.time() < flash_until:
            lines.append(">> " + flash_msg)
        banner(frame, lines)
        cv2.rectangle(frame, (w_frame - 170, 10), (w_frame - 10, 55), mode_col, -1)
        cv2.putText(frame, mode_txt, (w_frame - 158, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Hand Presenter", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break

    if drawing:
        pyautogui.mouseUp()
    hands.close(); cap.release(); cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Hand-only presentation control")
    parser.add_argument("--calibrate", action="store_true",
                        help="run the calibration wizard and save config.json")
    args = parser.parse_args()
    if args.calibrate:
        calibrate()
    else:
        present(load_config())


if __name__ == "__main__":
    main()
