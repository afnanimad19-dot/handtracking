import cv2
import mediapipe as mp
import platform

# ---------- CONFIG ----------
CAMERA_INDEX = 0     # 0 = first camera (Iriun). Try 1 or 2 if the wrong camera opens.
FLIP_CAMERA  = True  # Mirror the image (selfie view)
MAX_HANDS    = 2
# ----------------------------

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles  = mp.solutions.drawing_styles

# Landmark index numbers for the 5 fingertips (MediaPipe's hand model)
FINGERTIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}


def count_fingers_up(hand_landmarks, handedness_label):
    """Very simple finger-counting: returns how many fingers are extended."""
    lm = hand_landmarks.landmark
    up = 0

    # Four fingers: tip is higher (smaller y) than the joint below it = finger up
    for tip_id in [8, 12, 16, 20]:
        if lm[tip_id].y < lm[tip_id - 2].y:
            up += 1

    # Thumb: compare left/right (x) depending on which hand it is
    if handedness_label == "Right":
        if lm[4].x < lm[3].x:
            up += 1
    else:
        if lm[4].x > lm[3].x:
            up += 1

    return up


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
        max_num_hands=MAX_HANDS,
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    print("Hand tracking started. Press Q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        h, w = frame.shape[:2]

        # MediaPipe needs RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                   results.multi_handedness):
                label = handedness.classification[0].label  # "Left" or "Right"

                # Draw the skeleton on screen
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

                # Example: get the index fingertip position in pixels
                tip = hand_landmarks.landmark[FINGERTIPS["index"]]
                tip_x, tip_y = int(tip.x * w), int(tip.y * h)

                fingers = count_fingers_up(hand_landmarks, label)

                # Show info on screen
                cv2.putText(frame, f"{label} hand | fingers up: {fingers}",
                            (10, 30 if label == "Left" else 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.circle(frame, (tip_x, tip_y), 8, (0, 0, 255), -1)

                # ==========================================================
                #  ADD YOUR OWN LOGIC HERE
                #  You have, for each hand:
                #    - label        -> "Left" or "Right"
                #    - fingers      -> number of fingers held up (0-5)
                #    - tip_x, tip_y -> index fingertip position in pixels
                #    - hand_landmarks.landmark[i] -> any of the 21 points
                #      (each has .x, .y from 0..1, and .z for depth)
                #  Example idea: if fingers == 0: print("Fist!")
                # ==========================================================
                print(f"{label}: {fingers} fingers up, index tip at ({tip_x},{tip_y})")

        cv2.imshow("Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
            break

    hands.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    main()
