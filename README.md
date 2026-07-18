# Hand Tracking → Gesture Input

Webcam hand tracking (MediaPipe) turned into real input controls: **pinch,
drag & drop, swipe, fist, open palm** — plus research on business uses
(kiosks, healthcare, presentations, CRM). See **[RESEARCH.md](RESEARCH.md)**
for the full business research report.

## Files

| File | Purpose |
|---|---|
| `hand_tracking.py` | Base tracker: 21 hand landmarks + finger counting |
| `gestures.py` | Gesture engine: emits `PINCH_START/MOVE/END`, `SWIPE_LEFT/RIGHT`, `FIST`, `OPEN_PALM` events |
| `demo_virtual_objects.py` | Pinch to grab, drag and drop cards on screen (mini CRM board demo) |
| `demo_mouse_control.py` | Your hand controls the real mouse — click, drag, and swipe slides in any app |
| `demo_presenter.py` | Basic hand-only presentation control (swipe/point/draw/erase) |
| `presenter_app.py` | **The product**: presenter with calibration wizard (`--calibrate`), saved per-room config, gesture hint bar, black-screen gesture |

## Setup

```bash
pip install -r requirements.txt
```

Note: MediaPipe's `solutions.hands` API currently needs Python 3.8–3.12.

## Run

```bash
python hand_tracking.py          # basic tracking + finger counting
python demo_virtual_objects.py   # pinch / drag / drop objects on screen
python demo_mouse_control.py     # hand-controlled mouse (needs pyautogui)
```

Press **Q** to quit any demo. If the wrong camera opens, change
`CAMERA_INDEX` at the top of the script (0, 1, or 2).

## Gestures

- **Pinch** (thumb + index together) = click / grab
- **Hold pinch and move** = drag
- **Release pinch** = drop / click release
- **Open-hand fast swipe** = next / previous (arrow keys in mouse demo)
- **Fist** = reset (in the objects demo)

To build your own actions, import `GestureTracker` from `gestures.py` and
handle the events it returns — see the two demo files for examples.
