"""
demo_mouse_control.py — control your REAL mouse with hand gestures.

This is the bridge between hand tracking and ANY existing software
(CRM, browser, PowerPoint, Excel...): your hand becomes the mouse.

  * Move your index finger  -> move the cursor
  * PINCH (thumb + index)   -> press left mouse button
  * Hold the pinch and move -> DRAG (select text, drag a deal card in
                               your CRM, move a file...)
  * Release the pinch       -> release the button (a quick pinch = click)
  * SWIPE left / right with an open hand -> next / previous
                               (sends arrow keys — great for slides)

Requires: pip install pyautogui   (plus opencv-python and mediapipe)

Run:  python demo_mouse_control.py   (press Q in the camera window to quit)

SAFETY: pyautogui's failsafe is ON — slam your real mouse into the
top-left corner of the screen to abort instantly.
"""

import cv2
import mediapipe as mp
import platform

import pyautogui

from gestures import GestureTracker

CAMERA_INDEX = 0
FLIP_CAMERA = True

# Use the middle portion of the camera frame as the "touchpad" so you can
# reach screen edges without stretching your arm to the frame edges.
FRAME_MARGIN = 0.2  # 20% margin on each side

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # don't sleep between pyautogui calls

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def to_screen(px, py, frame_w, frame_h, screen_w, screen_h):
    """Map a frame pixel inside the margin box to full-screen coordinates."""
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
    mouse_down = False

    print("Hand mouse started. Pinch = click / hold to drag. Q to quit.")

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

            sx, sy = to_screen(px, py, w, h, screen_w, screen_h)
            pyautogui.moveTo(sx, sy)

            for ev in events:
                if ev.name == "PINCH_START" and not mouse_down:
                    pyautogui.mouseDown()
                    mouse_down = True
                elif ev.name == "PINCH_END" and mouse_down:
                    pyautogui.mouseUp()
                    mouse_down = False
                elif ev.name == "SWIPE_RIGHT":
                    pyautogui.press("right")  # next slide
                elif ev.name == "SWIPE_LEFT":
                    pyautogui.press("left")   # previous slide

            color = (0, 255, 255) if state.pinching else (0, 0, 255)
            cv2.circle(frame, (px, py), 10, color, -1)
            status = "DRAGGING" if mouse_down else "moving"
            cv2.putText(frame, f"{status}  fingers up: {state.fingers_up}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        elif mouse_down:
            # Hand left the frame while dragging -> release the button
            pyautogui.mouseUp()
            mouse_down = False

        # Draw the active "touchpad" region
        cv2.rectangle(frame,
                      (int(FRAME_MARGIN * w), int(FRAME_MARGIN * h)),
                      (int((1 - FRAME_MARGIN) * w), int((1 - FRAME_MARGIN) * h)),
                      (255, 255, 0), 1)

        cv2.imshow("Hand Mouse", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break

    if mouse_down:
        pyautogui.mouseUp()
    hands.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
