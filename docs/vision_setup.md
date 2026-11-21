# Webcam Card-Identification Setup Guide (Raspberry Pi 4B or Laptop)

This guide gets your **USB webcam** recognizing real **Bicycle Poker cards** in ~5 minutes — **no 3D printing, no motors, and no coding required!**

Everything runs inside the **Vision / Camera** tab of the Web UI so you can adjust the box and test live from your phone or laptop browser.

---

## Step 1: Set Up a Simple Desk Jig (30 Seconds!)

Before touching code, consistency is 90% of reliable card vision:
1. Prop or tape your **USB webcam** pointing straight down (or straight up through a small gap) about **`8–12 cm`** from a flat desk surface.
2. Tape two strips of cardboard/LEGO/index-card into an **L-shaped corner stop** on the desk under the camera so you can slide any card snugly into the exact same corner every time.
3. Keep room lighting steady (a simple desk lamp off to the side at `~45°` works great — avoid shining a bright bulb straight down onto glossy cards, which creates white glare).

---

## Step 2: Install Dependencies

### Option A — On your Raspberry Pi 4 Model B (Recommended)
Plug your USB webcam into any USB port on your Pi 4B, open a terminal (or SSH into your Pi), clone/pull this repo, and run:

```bash
cd card_shuffler
bash software/scripts/setup_pi.sh
```

*(Uses precompiled Raspberry Pi OS OpenCV so it finishes in ~30 seconds instead of compiling from source!)*

### Option B — Quick Test on Your Windows / Mac / Linux Laptop First
If you want to test on your laptop before setting up the Pi 4B:

```bash
cd card_shuffler/software
python3 -m venv .venv
# Mac/Linux: source .venv/bin/activate
# Windows:   .venv\Scripts\activate
pip install -r requirements.txt opencv-python-headless numpy
```

---

## Step 3: Launch the Web UI

```bash
bash software/scripts/run_web.sh
```
*(Or on Windows: `cd software && uvicorn shuffler.web_app:app --host 0.0.0.0 --port 8000`)*

The terminal will print the exact URL to open on your **phone or laptop browser** (e.g., `http://192.168.1.42:8000` or `http://localhost:8000`).

---

## Step 4: Align the Box & Capture 5 Test Cards First

Don't capture all 52 cards right away — prove it works on **5 cards** in 60 seconds first!

1. Open the browser UI and tap the **Vision / Camera** tab.
2. Leave **Source** = `USB Webcam` (`Index = 0`) and tap **Start Camera**.
   - *If your laptop has a built-in webcam, change `Webcam Index` to `1` to use the external USB webcam.*
3. Slide a Bicycle card face-up against your L-corner stop so the **top-left rank + suit corner** is visible on screen.
4. Drag the **Box X / Box Y / Box Width / Box Height** sliders until:
   - The **inner yellow box** tightly frames the **rank + suit index** (e.g. `A♠` or `10♥`).
   - The **outer green box** gives a tiny bit of breathing room around it (our matcher automatically searches inside the green box to handle small hand/mechanical position shifts!).
5. Capture just **5–6 starter templates** to test:
   - Select **`BACK (Face-Up)`**, place a card showing its Bicycle back pattern, tap **Capture**.
   - Select **`A♠`**, **`A♥`**, **`K♣`**, **`10♦`**, **`7♠`** (or any 5 cards you pick), place each card snugly in the corner stop, and tap **Capture**.

---

## Step 5: Watch It Identify Cards Live!

1. Scroll down to **3. Test Card Identification Live**.
2. Check **Auto-Identify Live (every 0.8s)**.
3. Swap your 5 calibrated cards (plus the card back!) into the corner stop one by one — you should see big instant matches like **`A♠ (93% confidence • black ink)`**, **`A♥ (91% confidence • red ink)`**, and **`FACE-UP CARD`** when showing the back!
4. Once your 5-card test hits `>85%` consistently, grab your full Bicycle deck in New Deck Order and use **Capture & Next →** to breeze through all 52 cards in ~2 minutes!

---

## Troubleshooting Quick Checks
- **Image is blurry up close (`8–10 cm`):** Most cheap USB webcams have a little manual focus ring around the lens (or need to be pulled slightly farther back to `12–15 cm` until the card letters look sharp!). Once you upgrade to the autofocus **Pi Camera Module 3** later, it focuses razor-sharp down to `5 cm`.
- **Matches swap Red vs. Black or score `<70%`:** Make sure the **inner yellow box** doesn't include desk background outside the card edge, and try angling your lamp slightly to remove white glare on the card surface.
- **Switching to Pi Camera Module 3 later:** Just change **Source** from `USB Webcam` to `Pi Camera (CSI)` in the Vision tab — zero code changes required!
