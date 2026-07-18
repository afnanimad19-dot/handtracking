# Setup Guide — Test the Hand Presenter on YOUR PC (with a phone camera)

*Everything here is free. No PowerPoint needed — the repo includes
`test_slides.html`, a browser slide deck that responds to the exact same
keys PowerPoint uses, including drawing, erasing, and black screen.*

---

## Step 0 — What you need
- Windows PC (works on Mac/Linux too)
- Your phone with the **Iriun Webcam** app (the one you already used), or any
  webcam
- Python **3.10–3.12** (MediaPipe does not support 3.13 yet)

## Step 1 — Install Python (once)
1. Download Python 3.12 from https://www.python.org/downloads/
2. During install, tick **"Add python.exe to PATH"** — this checkbox matters.
3. Verify: open Command Prompt, run `python --version` → should say 3.12.x

## Step 2 — Get the code
Either `git clone` your repo and switch to the branch
`claude/hand-tracking-business-research-5nvhjc`, or download it as a ZIP from
GitHub (Code → Download ZIP) and extract to e.g. `F:\hand-tracking`.

Then in Command Prompt:
```
cd F:\hand-tracking
pip install -r requirements.txt
```
(This installs opencv-python, mediapipe, pyautogui. Takes a few minutes.)

## Step 3 — Connect the phone camera (Iriun)
1. Open **Iriun Webcam** on the phone AND the Iriun desktop app on the PC.
2. Both devices on the **same Wi-Fi** → the phone video appears on the PC.
3. Find which camera index the phone is:
   ```
   python check_camera.py
   ```
   Press **N** to cycle cameras. Note the index that shows your PHONE's
   picture. If it isn't 0, edit `CAMERA_INDEX = 0` at the top of
   `presenter_app.py` to that number.
4. **Phone placement:** prop the phone up facing you, roughly chest height,
   1–2 meters away, with decent light on your hand (light in FRONT of you,
   not behind — a window behind you will ruin tracking).

## Step 4 — Calibrate (once per room)
```
python presenter_app.py --calibrate
```
Follow the 3 steps on screen: hold hand open → hold a pinch → 3 fast swipes.
It saves `config.json` automatically.

## Step 5 — Test with the built-in slide deck
1. Double-click **`test_slides.html`** (opens in your browser).
2. Click once anywhere on the page (so it receives key presses),
   then press **F11** for fullscreen.
3. In Command Prompt:
   ```
   python presenter_app.py
   ```
4. Now test, in this order:
   - **Swipe** open hand right → next slide
   - Slide 1: **point** with your index finger — cursor follows it onto A, B, C
   - Slide 2: **pinch and move** — draw a circle around the buggy code line;
     **fist** — your circle is erased
   - Slide 3: pinch-write your name on the grid
   - **Open palm 2s** — screen goes black; again — it comes back
   - **Q** in the camera window quits

## Step 6 — When you DO present for real
- PowerPoint: start slideshow, press **Ctrl+P** once (pen mode) so
  pinch-drawing inks on slides; **Ctrl+L** gives a laser pointer instead.
- Google Slides / PDF fullscreen: swiping and pointing work as-is
  (arrow keys + cursor). Drawing depends on the app's own pen feature.

## Troubleshooting
| Problem | Fix |
|---|---|
| `pip` not recognized | Reinstall Python with "Add to PATH" ticked |
| mediapipe install fails | Your Python is 3.13+ — install 3.12 |
| Wrong camera opens | Run `check_camera.py`, set `CAMERA_INDEX` |
| Pinch flickers / won't trigger | Re-run `--calibrate` in current lighting |
| Swipes fire by accident | Re-calibrate with faster deliberate swipes (raises the threshold) |
| Cursor jittery | More light on your hand; keep hand inside the yellow box |
| Keys don't reach the browser | Click the slide page once before presenting |
| Everything went crazy | Slam real mouse to top-left corner = emergency stop |
