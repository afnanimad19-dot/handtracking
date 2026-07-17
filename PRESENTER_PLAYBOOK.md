# Presenter Product — Step-by-Step Playbook (Build → Test → Sell)

*The first product to launch NOW: hand-only presentation & showroom control.
No mouse, no clicker — swipe slides, point at things, draw on slides, all in
the air. Plus: what holograms actually are and how our tech connects to them
(see [HOLOGRAMS.md](HOLOGRAMS.md)).*

---

## The feature set (v1)

Already working in this repo (`demo_presenter.py`):

| Gesture | Action |
|---|---|
| Open-hand swipe right/left | Next / previous slide |
| Point with index finger | On-screen pointer follows your finger |
| Pinch + move | Draw / annotate on the slide (PowerPoint pen mode) |
| Fist | Erase drawings |

Features to add next (each is a small addition to `gestures.py` / the demo):

1. **Hold open palm 2s** → black screen (`B` key) — "pause and look at me"
2. **Two-finger pinch-zoom** → zoom into slide detail (PowerPoint `Ctrl+ +`
   or slideshow zoom) — great for showrooms showing product photos
3. **Thumbs up** → start slideshow / confirm (needs MediaPipe Gesture
   Recognizer's built-in Thumb_Up class)
4. **On-screen gesture hint bar** → small overlay showing available gestures
   (sells trust in live demos)
5. **Calibration screen** → 30-second setup wizard: stand here, wave, done.
   This is what turns a demo into a product.
6. **Showroom "attract mode"** → when nobody's presenting, auto-loop content;
   wave to take control. That's the showroom/kiosk crossover.

## Step-by-step: build → implement → sell

### Week 1 — Make it rock-solid for YOU
1. `pip install -r requirements.txt`, run `python demo_presenter.py` with a
   real PowerPoint in slideshow mode. Ctrl+P for pen mode, then rehearse.
2. Tune the numbers at the top of `gestures.py` for your camera and lighting
   (`SWIPE_SPEED` if swipes misfire, `PINCH_ON/OFF` if pinch is jumpy).
3. Rehearse a 3-minute demo deck until every gesture lands 10/10 times.
   Reliability IS the product.

### Week 2 — Package it
4. Add the calibration wizard + gesture hint overlay (features 4–5 above).
5. Bundle into one double-click app (`pyinstaller --onefile demo_presenter.py`)
   so a client never sees Python.
6. Record a 60-second vertical video: you presenting hands-only. This video
   does your selling on WhatsApp/Instagram/LinkedIn.

### Week 3 — First real installs (free pilots)
7. Your dental clients: waiting-room TV in attract mode + the dentist using
   hand-swipe for patient-education slides (gloves stay on — that's the hook).
8. One local event venue / real-estate office / showroom: install for one
   event in exchange for a testimonial video.

### Week 4+ — Charge money
9. Offer: setup + calibration + custom gestures + support.
   Pricing shapes that work for this market:
   - One-time install: $300–800 per room (webcam included)
   - Event package: $200–500 per event day, you attend and operate
   - Showroom subscription: $50–150/month for content updates + support
10. Every install feeds the bigger roadmap: same gesture engine powers the
    CRM wall-board, the kiosk, and later the Jarvis screen — you're selling
    the same core five different ways.

## Sales pitch (one paragraph, memorize it)

"Your presenter never touches a laptop. They walk, talk, and move slides
with a wave — point at the screen and it highlights, pinch the air and it
draws. It works with the PowerPoint you already have, needs one webcam, and
takes 30 minutes to install. Want me to run your next meeting with it?"
