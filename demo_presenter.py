"""
demo_presenter.py — run a presentation with ONLY your hand. No mouse, no clicker.

Gestures (works with PowerPoint, Google Slides, Keynote, PDF viewers):

  OPEN-HAND SWIPE right / left  -> next / previous slide (arrow keys)
  POINT (index finger only)     -> on-screen pointer follows your finger
  PINCH and hold + move         -> draw/annotate on the slide
                                   (in PowerPoint slideshow press Ctrl+P once
                                    to enter pen mode; then pinch-drawing inks)
  FIST                          -> erase drawings (sends 'E' — PowerPoint's
                                   "erase ink on slide" key)

Tips for PowerPoint slideshow mode:
  Ctrl+P = pen mode   Ctrl+L = laser pointer   B = black screen   Esc = exit

Run:  python demo_presenter.py   (press Q in the camera window to quit)

SAFETY: pyautogui failsafe is ON — slam the real mouse into the top-left
screen corner to abort instantly.
"""

import cv2
import mediapipe as mp
import platform

import pyautogui

from gestures import GestureTracker

CAMERA_INDEX = 0
FLIP_CAMERA = True
FRAME_MARGIN = 0.2  # middle 60% of the frame maps to the full screen

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def to_screen(px, py, frame_w, frame_h, screen_w, screen_h):
    x0, x1 = FRAME_MARGIN * frame_w, (1 - FRAME_MARGIN) * frame_w
    y0, y1 = FRAME_MARGIN * frame_h, (1 - FRAME_MARGIN) * frame_h
    nx = min(max((px - x0) / (x1 - x0), 0.0), 1.0)
    ny = min(max((py - y0) / (y1 - y0), 0.0), 1.0)
    return int(nx * (screen_w - 1)), int(ny * (screen_h - 1))


def main():
    backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_INDEX, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Try changing CAMERA_INDEX (0, 1, or 2).")
        return

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    tracker = GestureTracker()
    screen_w, screen_h = pyautogui.size()
    drawing = False

    print(__doc__)

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        mode = "waiting for hand"

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

            # Pointer follows the finger while pointing (1-2 fingers up)
            # or while drawing — but stays still during open-palm swipes.
            if drawing or state.fingers_up <= 2:
                sx, sy = to_screen(px, py, w, h, screen_w, screen_h)
                pyautogui.moveTo(sx, sy)
                mode = "drawing" if drawing else "pointing"
            else:
                mode = "open hand (swipe ready)"

            for ev in events:
                if ev.name == "PINCH_START" and not drawing:
                    pyautogui.mouseDown()
                    drawing = True
                elif ev.name == "PINCH_END" and drawing:
                    pyautogui.mouseUp()
                    drawing = False
                elif ev.name == "SWIPE_RIGHT":
                    pyautogui.press("right")
                    mode = "NEXT slide"
                elif ev.name == "SWIPE_LEFT":
                    pyautogui.press("left")
                    mode = "PREVIOUS slide"
                elif ev.name == "FIST":
                    pyautogui.press("e")  # erase ink (PowerPoint slideshow)
                    mode = "erase drawings"

            color = (0, 255, 255) if drawing else (0, 0, 255)
            cv2.circle(frame, (px, py), 10, color, -1)
        elif drawing:
            pyautogui.mouseUp()
            drawing = False

        cv2.rectangle(frame,
                      (int(FRAME_MARGIN * w), int(FRAME_MARGIN * h)),
                      (int((1 - FRAME_MARGIN) * w), int((1 - FRAME_MARGIN) * h)),
                      (255, 255, 0), 1)
        cv2.putText(frame, f"mode: {mode}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Swipe=slides  Point=pointer  Pinch=draw  Fist=erase  Q=quit",
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Hand Presenter", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break

    if drawing:
        pyautogui.mouseUp()
    hands.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
