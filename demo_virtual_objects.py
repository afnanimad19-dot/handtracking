"""
demo_virtual_objects.py — pinch, DRAG and MOVE objects on screen with your hand.

This is the "grab things in the air" demo:
  * Colored cards float on the camera feed.
  * PINCH (thumb + index together) on top of a card to GRAB it.
  * Move your hand while pinching to DRAG it.
  * Release the pinch to DROP it.
  * SWIPE left/right with an open hand to change the background theme.
  * Make a FIST to reset the cards.

Think of the cards as CRM deal cards on a kanban board, products on a
shelf, or slides in a deck — the interaction is the same.

Run:  python demo_virtual_objects.py   (press Q to quit)
"""

import cv2
import mediapipe as mp
import platform

from gestures import GestureTracker

CAMERA_INDEX = 0
FLIP_CAMERA = True

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

CARD_W, CARD_H = 170, 90

THEMES = [(40, 40, 40), (60, 30, 10), (10, 40, 60)]


def make_cards():
    return [
        {"x": 60,  "y": 80,  "label": "Lead: Acme Co",   "color": (80, 170, 255)},
        {"x": 60,  "y": 200, "label": "Deal: $12,000",   "color": (120, 220, 120)},
        {"x": 60,  "y": 320, "label": "Task: Follow up", "color": (200, 140, 250)},
    ]


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
    cards = make_cards()
    grabbed = None      # index of the card being dragged
    grab_off = (0, 0)   # offset between pinch point and card corner
    theme = 0

    print("Pinch a card to grab it, move to drag, release to drop.")
    print("Open-hand swipe = change theme, fist = reset. Press Q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # Dim the camera image toward the theme color so cards stand out
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), THEMES[theme], -1)
        frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        cursor = None
        pinching = False

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                  results.multi_handedness):
                label = handedness.classification[0].label
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

                events, state = tracker.update(hand_landmarks, label, w, h)
                cursor = (int(state.smooth_x * w), int(state.smooth_y * h))
                pinching = state.pinching

                for ev in events:
                    if ev.name == "PINCH_START":
                        # Grab the topmost card under the pinch point
                        for i in range(len(cards) - 1, -1, -1):
                            c = cards[i]
                            if (c["x"] <= ev.x <= c["x"] + CARD_W
                                    and c["y"] <= ev.y <= c["y"] + CARD_H):
                                grabbed = i
                                grab_off = (ev.x - c["x"], ev.y - c["y"])
                                cards.append(cards.pop(i))  # bring to front
                                grabbed = len(cards) - 1
                                break
                    elif ev.name == "PINCH_MOVE" and grabbed is not None:
                        cards[grabbed]["x"] = ev.x - grab_off[0]
                        cards[grabbed]["y"] = ev.y - grab_off[1]
                    elif ev.name == "PINCH_END":
                        grabbed = None
                    elif ev.name in ("SWIPE_LEFT", "SWIPE_RIGHT"):
                        theme = (theme + (1 if ev.name == "SWIPE_RIGHT" else -1)) % len(THEMES)
                    elif ev.name == "FIST":
                        cards = make_cards()
                        grabbed = None

        # Draw the cards
        for i, c in enumerate(cards):
            x, y = int(c["x"]), int(c["y"])
            is_held = (grabbed == i)
            border = (255, 255, 255) if is_held else (0, 0, 0)
            cv2.rectangle(frame, (x, y), (x + CARD_W, y + CARD_H), c["color"], -1)
            cv2.rectangle(frame, (x, y), (x + CARD_W, y + CARD_H), border, 3 if is_held else 1)
            cv2.putText(frame, c["label"], (x + 10, y + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # Draw the hand cursor
        if cursor:
            cv2.circle(frame, cursor, 12, (0, 255, 255) if pinching else (0, 0, 255), -1)

        cv2.putText(frame, "Pinch=grab  Move=drag  Release=drop  Swipe=theme  Fist=reset",
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Virtual Objects - Hand Control", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break

    hands.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
