# Programmable Playing Card Shuffler & Sorter

A standalone, single-pass, 3D-printed mechanical card shuffler capable of arranging a standard Bicycle Poker-size deck into **any predetermined order** (for magic routines / custom stacks) or a **true randomized shuffle**, controlled directly from your phone over Wi-Fi.

## Design Summary

| Parameter | Locked-In Spec |
| :--- | :--- |
| **Cards** | Standard unmodified Bicycle Poker size (`63.5 × 88.9 × 0.29 mm`), 52 cards + optional 2 Jokers (`54` slots) loaded face-down |
| **Sorting Architecture** | Single-pass **Vertical Linear Slotted Elevator** (54-slot comb, `2.0 mm` pitch, `~108 mm` travel) |
| **Unloading** | **Gravity-Drop Expanding Side Combs** (validated via zero-electronics bench test first; fallback: one-by-one ejector sweep) |
| **Form Factor** | Vertical desktop tower (`~150 × 220 mm` footprint, `~265 mm` tall) — cards stay flat throughout |
| **Compute & Vision** | **Raspberry Pi 4 Model B (4 GB)** *(on hand)* + **Pi Camera** (Python/OpenCV + Wi-Fi Web UI) paired with **Arduino Nano/Uno** (real-time C++ motion control) |
| **Control UX** | Phone-only Wi-Fi Web UI (no physical screen/buttons except power switch) with **Custom Stack Builder** & random shuffle |
| **Fault Detection** | Automatically pauses & alerts the phone UI on missing, duplicate, or accidentally face-up cards |
| **Power** | USB-C PD trigger board (`15V 3A` / `45W+` brick or power bank) + dual isolated `5V 3A` buck converters (dedicated `5.1V` rail for Pi 4, separate `5V` rail for servo/sensors) |
| **Budget & Fabrication** | Target `~$105–$128` (well under `$150` ceiling), OnShape CAD, `≥220×220 mm` 3D printer (PLA/PETG), M3 heat-set inserts |

> **Live Status & Workflow:** Check [`PROJECT_STATE.md`](PROJECT_STATE.md) for current phase, Drive links, and `ready-now` tasks ([GitHub Issues `#2`–`#16`](https://github.com/AndrewCh3n/card_shuffler/issues)), and follow [`AGENTS.md`](AGENTS.md) for shared GitHub + Google Workspace ground rules.

## Repository Layout

```text
card_shuffler/
├── AGENTS.md                    # Shared GitHub + Google Workspace ground rules & chat workflow
├── PROJECT_STATE.md             # 1-page live status dashboard, Drive links, BOM snapshot & ready-now issues
├── docs/
│   ├── architecture.md          # System architecture, state machine, serial protocol & wiring pinout
│   ├── bom.md                   # Engineering Bill of Materials spec & staged ordering rationale
│   ├── build_log.md             # Append-only engineering build, print tolerance & bench-test log
│   ├── cad_spec.md              # OnShape parametric variables, tolerances, module dimensions & bench-test plan
│   └── vision_setup.md          # Step-by-step USB webcam / Pi Camera card-recognition setup guide
├── cad/                         # Exported OnShape STEP/STL files & revision logs
├── firmware/
│   └── shuffler_controller/     # Arduino Nano/Uno real-time stepper, servo & sensor firmware
└── software/
    ├── shuffler/                # Python deck planner, vision pipeline, Arduino bridge, controller & phone Web UI
    ├── scripts/                 # Pi setup (setup_pi.sh), web launcher (run_web.sh), & CLI simulator
    └── tests/                   # Automated unit & API tests
```

## Quick Start

**Option 1 — Live USB Webcam Card Identification (Raspberry Pi 4B):**
See [`docs/vision_setup.md`](docs/vision_setup.md), or run:
```bash
bash software/scripts/setup_pi.sh
bash software/scripts/run_web.sh
# Open the printed URL in your phone/laptop browser -> Tab 3: "Vision / Camera"
```

**Option 2 — Zero-Hardware Simulation & Tests (Any Computer):**
```bash
cd software
python3 -m unittest discover -s tests -v
python3 scripts/simulate_sort.py --mode random
uvicorn shuffler.web_app:app --host 0.0.0.0 --port 8000 --reload
```

## Build Roadmap

1. **Phase 0 (Now):** Review [`docs/architecture.md`](docs/architecture.md), [`docs/bom.md`](docs/bom.md), and [`docs/cad_spec.md`](docs/cad_spec.md). Order parts and test the software simulator & Custom Stack Builder UI.
2. **Phase 1 — Zero-Electronics Bench Tests (OnShape + 3D Printer):**
   - Print **Bench Test A:** Expanding Side-Comb Gravity Drop chute — verify 52 cards drop flat & cleanly into the output tray.
   - Print **Bench Test B:** Single-Card Feeder & Separator — tune roller grip, top weight, and metal separator gap for `<0.5%` double-feed rate.
3. **Phase 2 — Optical Scan Tunnel:** Mount the Pi Camera + diffused LEDs after the feeder exit; capture reference templates for your Bicycle deck and verify `52/52` recognition accuracy.
4. **Phase 3 — Full Mechatronic Integration:** Assemble the MGN12H rail + T8 leadscrew elevator, flash `firmware/shuffler_controller`, and run end-to-end automated sorts from the Raspberry Pi 4B.
5. **Phase 4 — Final Enclosure:** Wrap all modules in a clean, magnetic-access OnShape shell with cable management and acoustic rubber feet.
