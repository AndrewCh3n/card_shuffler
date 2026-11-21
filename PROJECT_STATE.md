# Project State — Programmable Card Shuffler & Sorter

> **1-Page Live Snapshot:** Read this file (plus [`AGENTS.md`](AGENTS.md)) at the start of any session — Main Project Chat, Per-Issue Focus Chat, or Q&A — to sync on where the project stands right now.

- **Last Updated:** `2026-11-21`
- **Current Phase:** **Phase 0 — Setup & Sourcing** *(8 `ready-now` issues unblocked today with on-hand hardware)*
- **Budget Ceiling:** `$150` *(excluding filament & on-hand Pi 4B / Arduino Nano)*

---

## 1. Shared Workspace Links

| Resource | Link | Purpose |
| :--- | :--- | :--- |
| **Google Drive Project Folder** | [Card Shuffler (Drive)](https://drive.google.com/drive/folders/1OZ12Imh7Rae0uHsw9xqHqIBVIOwP_aX1) | Top-level Drive folder for all human-editable project files |
| **Live BOM & Inventory Master** | [Parts, Lab Scouting & Learning Tracker](https://docs.google.com/spreadsheets/d/1MSAsWFvpI-4053Ha5YDHNZjiihVYTBqtmWjEtyQ3ilA/edit) | Live inventory (`On Hand` / `Scout in Lab` / `Buy Later`), lab quick list, learning glossary |
| **Workbench Notes & Scratchpad** | [Running Notes & Scratchpad](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit) | Fast field notes, caliper measurements, lab finds (check newest entries on top) |
| **Bench Test Media** | [Bench Tests & Media (Drive)](https://drive.google.com/drive/folders/12iZSgKtl43777iYu8vOVGCT-oZCNFP-f) | Photos, slow-mo drop videos, and test card images |
| **Datasheets & References** | [Datasheets & References (Drive)](https://drive.google.com/drive/folders/1dQ_bGhUrDYy7ffanITZEXH1IStnv-I3b) | Component pinouts, driver docs, mechanical drawings |
| **Task Breakdown & Roadmap** | [All Issues (#2–#16)](https://github.com/AndrewCh3n/card_shuffler/issues) • [`ready-now` Queue](https://github.com/AndrewCh3n/card_shuffler/issues?q=is%3Aopen+label%3Aready-now) • [Milestones](https://github.com/AndrewCh3n/card_shuffler/milestones) | Module → Task → Subtask execution board across Phases 0–4 |
| **OnShape CAD Workspace** | *TBD — add link during Issue [#6](https://github.com/AndrewCh3n/card_shuffler/issues/6)* | Parametric models for Bench Tests A/B & Modules 1–5 |

---

## 2. Locked-In Baseline Specs

| Subsystem | Current Locked Spec | Reference Doc |
| :--- | :--- | :--- |
| **Target Deck** | Standard Bicycle Poker (`63.5 × 88.9 × 0.29 mm`), 52 cards + optional 2 Jokers (`54` slots), face-down | [`README.md`](README.md) |
| **Sorting Architecture** | Single-pass vertical linear slotted elevator (`54` slots, `2.0 mm` pitch, `106 mm` travel, `~150 × 215 × 265 mm` tower) | [`docs/cad_spec.md`](docs/cad_spec.md) |
| **Unloading** | Expanding side-comb gravity drop *(gated on Bench Test A [#7](https://github.com/AndrewCh3n/card_shuffler/issues/7); fallback: one-by-one ejector sweep)* | [`docs/cad_spec.md`](docs/cad_spec.md) |
| **Compute & Vision** | Raspberry Pi 4B 4 GB *(on hand)* + Pi Camera Module 3 (`65–75 mm` focal distance) + Arduino Nano/Uno (`115200` USB serial) | [`docs/architecture.md`](docs/architecture.md), [`docs/vision_setup.md`](docs/vision_setup.md) |
| **Power Architecture** | `15V 3A` (`45W+`) USB-C PD trigger + dual isolated `5V 3A` bucks (`5.1V` Pi 4B rail, `5.0V` servo/sensors/LED rail) | [`docs/architecture.md`](docs/architecture.md) |

---

## 3. BOM & Inventory Snapshot

*Synced from Google Sheet `Parts_Tracker` (`2026-11-21`):*

| Status Bucket | Count | Notes |
| :--- | :---: | :--- |
| **On Hand** | `9` | Pi 4B (4 GB), Arduino Nano/Uno, 3D printer + filament, Bicycle deck, soldering iron, breadboards, jumpers |
| **Scout in Lab** | `13` | See Tab 2 (`Lab_Scouting_Quick_List`) in Google Sheet — tracked in [#5](https://github.com/AndrewCh3n/card_shuffler/issues/5) |
| **Buy Later (Stage 1)** | `5` | Zero-risk parts (MicroSD, Pi Cam v3, heatsink, silicone O-rings, feeler gauge/shim) — tracked in [#5](https://github.com/AndrewCh3n/card_shuffler/issues/5) |
| **Buy Later (Stage 2)** | `6` | Motion & power parts — **gated on Bench Test A ([#7](https://github.com/AndrewCh3n/card_shuffler/issues/7)) passing** |
| **Estimated Remaining Cost** | **`~$100`** | `$129` max if lab-scouted items must be purchased (under `$150` ceiling) |

---

## 4. Active Task Breakdown (15 Open Issues: `8` Ready Now, `7` Waiting on Parts)

### Ready Now (Unblocked Today with On-Hand Hardware)
| Issue | Phase | Module | Task |
| :---: | :--- | :--- | :--- |
| [#2](https://github.com/AndrewCh3n/card_shuffler/issues/2) | Phase 0 | `module:vision` | `[Vision 1.1]` Run Live Webcam Card Vision Studio on Windows PC |
| [#3](https://github.com/AndrewCh3n/card_shuffler/issues/3) | Phase 0 | `module:vision` | `[Vision 1.2]` Calibrate BACK + 5 Test Bicycle Cards with Cardboard L-Jig |
| [#4](https://github.com/AndrewCh3n/card_shuffler/issues/4) | Phase 0 | `module:electronics` | `[Electronics 3.1]` Flash `shuffler_controller.ino` to Arduino Nano/Uno & Verify Serial Commands |
| [#5](https://github.com/AndrewCh3n/card_shuffler/issues/5) | Phase 0 | Sourcing / BOM | `[Sourcing 0.1]` Finalize Lab Scouting & Order Stage 1 Parts (MicroSD, Pi Cam v3, O-Rings, Shim) |
| [#6](https://github.com/AndrewCh3n/card_shuffler/issues/6) | Phase 1 | `module:mechanics` | `[Mechanics 2.1]` Create OnShape Variable Studio & Print Bench Test A (Expanding Comb Drop) |
| [#7](https://github.com/AndrewCh3n/card_shuffler/issues/7) | Phase 1 | `module:mechanics` | `[Mechanics 2.2]` Run 10× Manual Gravity-Drop Test & Lock In Unload Mechanism *(Stage 2 gate)* |
| [#8](https://github.com/AndrewCh3n/card_shuffler/issues/8) | Phase 1 | `module:electronics` | `[Electronics 3.2]` Breadboard-Test On-Hand Lab Parts (Servo, Limit Switch, IR Sensors, LEDs) |
| [#10](https://github.com/AndrewCh3n/card_shuffler/issues/10) | Phase 2 | `module:vision` | `[Vision 1.3]` Full 52-Card (+ Jokers) Webcam Calibration & Accuracy Audit |

### Waiting on Parts (Unlock After Stage 1 / Stage 2 Orders)
- **Phase 1:** [#9](https://github.com/AndrewCh3n/card_shuffler/issues/9) `[Mechanics 2.3]` Bench Test B — Single-Card Feeder & Separator
- **Phase 2:** [#11](https://github.com/AndrewCh3n/card_shuffler/issues/11) `[Vision 1.4]` Build Optical Scan Tunnel & Calibrate Pi Camera Module 3 in Darkbox
- **Phase 3:** [#12](https://github.com/AndrewCh3n/card_shuffler/issues/12) `[Electronics 3.3]` Dual 5V Buck Power Tree & TMC2209s • [#13](https://github.com/AndrewCh3n/card_shuffler/issues/13) `[Mechanics 2.4]` Module 3 Motorized Linear Elevator • [#14](https://github.com/AndrewCh3n/card_shuffler/issues/14) `[Pi 4.1]` Flash Pi OS Lite & Run `setup_pi.sh` • [#15](https://github.com/AndrewCh3n/card_shuffler/issues/15) `[Pi 4.2]` End-to-End 52-Card Sort & Fault-Recovery Verification
- **Phase 4:** [#16](https://github.com/AndrewCh3n/card_shuffler/issues/16) `[Packaging 5.1]` Shared Baseplate, Vented Pi 4B Bay & Magnetic-Access Outer Shell

---

## 5. Open Decisions

- **Unload Mechanism Gate ([#7](https://github.com/AndrewCh3n/card_shuffler/issues/7)):** Confirm expanding-comb gravity drop vs. one-by-one ejector sweep after **Bench Test A** (before ordering Stage 2 motion hardware).
- **Arduino Nano USB Connector ([#5](https://github.com/AndrewCh3n/card_shuffler/issues/5)):** Confirm Mini-USB vs. USB-C data cable match for lab Nano(s).
- **OnShape Link ([#6](https://github.com/AndrewCh3n/card_shuffler/issues/6)):** Add OnShape project URL to Section 1 once the Variable Studio is created.
