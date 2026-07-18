"""
check_camera.py — find which camera index is your phone (Iriun) vs laptop cam.

Shows each camera it can open, one at a time, with its index number drawn on
the image. Press N for the next camera, Q to quit.

Use the index that shows your PHONE's picture as CAMERA_INDEX in
presenter_app.py / the demos.
"""

import cv2

MAX_INDEX = 5


def main():
    found = []
    for idx in range(MAX_INDEX):
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            cap.release()
            continue
        found.append(idx)
        print(f"[camera {idx}] opened — showing preview. N = next camera, Q = quit.")
        while True:
            ok, frame = cap.read()
            if not ok:
                print(f"[camera {idx}] opened but gives no image (in use elsewhere?)")
                break
            cv2.putText(frame, f"CAMERA_INDEX = {idx}   (N=next, Q=quit)",
                        (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.imshow("Camera check", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('n'), ord('N')):
                break
            if key in (ord('q'), ord('Q'), 27):
                cap.release()
                cv2.destroyAllWindows()
                print(f"Cameras found at indexes: {found}")
                return
        cap.release()
    cv2.destroyAllWindows()
    if not found:
        print("No cameras found. Is Iriun running on BOTH phone and PC, same Wi-Fi?")
    else:
        print(f"Cameras found at indexes: {found}")


if __name__ == "__main__":
    main()
