# Project State — Programmable Card Shuffler & Sorter

> **1-Page Live Snapshot:** Read this file (plus [`AGENTS.md`](AGENTS.md)) at the start of every chat session to sync on where the project stands right now.

- **Last Updated:** `2026-11-21`
- **Current Phase:** **Phase 0 — Setup & Sourcing** *(preparing for Phase 1 zero-electronics bench tests)*
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
| **GitHub Issues & Milestones** | [Issues](https://github.com/AndrewCh3n/card_shuffler/issues) • [Milestones](https://github.com/AndrewCh3n/card_shuffler/milestones) | Cross-role handoff queue (`needs-build`, `needs-bom`, `needs-pm`, `bench-test`, `decision`) |
| **OnShape CAD Workspace** | *TBD — add link once Variable Studio is created* | Parametric models for Bench Tests A/B & Modules 1–5 |

---

## 2. Locked-In Baseline Specs

| Subsystem | Current Locked Spec | Reference Doc |
| :--- | :--- | :--- |
| **Target Deck** | Standard Bicycle Poker (`63.5 × 88.9 × 0.29 mm`), 52 cards + optional 2 Jokers (`54` slots), face-down | [`README.md`](README.md) |
| **Sorting Architecture** | Single-pass vertical linear slotted elevator (`54` slots, `2.0 mm` pitch, `106 mm` travel, `~150 × 215 × 265 mm` tower) | [`docs/cad_spec.md`](docs/cad_spec.md) |
| **Unloading** | Expanding side-comb gravity drop *(gated on Bench Test A; fallback: one-by-one ejector sweep)* | [`docs/cad_spec.md`](docs/cad_spec.md) |
| **Compute & Vision** | Raspberry Pi 4B 4 GB *(on hand)* + Pi Camera Module 3 (`65–75 mm` focal distance) + Arduino Nano/Uno (`115200` USB serial) | [`docs/architecture.md`](docs/architecture.md), [`docs/vision_setup.md`](docs/vision_setup.md) |
| **Power Architecture** | `15V 3A` (`45W+`) USB-C PD trigger + dual isolated `5V 3A` bucks (`5.1V` Pi 4B rail, `5.0V` servo/sensors/LED rail) | [`docs/architecture.md`](docs/architecture.md) |

---

## 3. BOM & Inventory Snapshot

*Synced from Google Sheet `Parts_Tracker` (`2026-11-21`):*

| Status Bucket | Count | Notes |
| :--- | :---: | :--- |
| **On Hand** | `9` | Includes Pi 4B (4 GB), Arduino Nano/Uno, 3D printer + filament, Bicycle deck, soldering iron, breadboards, jumpers |
| **Scout in Lab** | `13` | See Tab 2 (`Lab_Scouting_Quick_List`) in Google Sheet |
| **Buy Later (Stage 1)** | `5` | Zero-risk parts (Pi Cam v3, M3 screws/inserts, silicone O-rings, bearings, feeler gauge/shim) |
| **Buy Later (Stage 2)** | `6` | Motion & power parts — **gated on Bench Test A passing** |
| **Estimated Remaining Cost** | **`~$100`** | `$129` max if lab-scouted items must be purchased (under `$150` ceiling) |

---

## 4. What Is Already Built in the Repo

- [x] System architecture, state machine, Pi↔Arduino serial protocol, power tree, and pinout ([`docs/architecture.md`](docs/architecture.md))
- [x] Engineering BOM specification and staged ordering plan ([`docs/bom.md`](docs/bom.md))
- [x] OnShape Variable Studio parameters, packaging envelope, and Bench Test A/B blueprints ([`docs/cad_spec.md`](docs/cad_spec.md))
- [x] Vision / webcam setup guide ([`docs/vision_setup.md`](docs/vision_setup.md))
- [x] Arduino real-time controller sketch ([`firmware/shuffler_controller/shuffler_controller.ino`](firmware/shuffler_controller/shuffler_controller.ino))
- [x] Python deck planner, OpenCV vision pipeline, serial bridge, phone Web UI, simulator, and unit tests ([`software/shuffler/`](software/shuffler/), [`software/tests/`](software/tests/))
- [x] Shared multi-agent workflow contract & Google Drive organization ([`AGENTS.md`](AGENTS.md))

---

## 5. Immediate Next Steps & Open Decisions

### Next Up (Phase 0 → Phase 1)
1. **Lab Scouting:** Check lab bins against Tab 2 (`Lab_Scouting_Quick_List`) in the Google Sheet and flip found items to `On Hand`.
2. **Stage 1 Parts Order:** Order zero-risk parts once lab scouting confirms what isn't free in lab.
3. **Bench Test A (OnShape + 3D Print):** Model and print the manual 54-slot expanding-comb gravity-drop rig (`cad/bench_test_a_comb_drop/`) and verify **10/10 flat drops** with 52 cards.
4. **Software / Vision Dry Run:** Verify unit tests (`python3 -m unittest`), simulator, and live Pi 4B camera setup.

### Open Decisions
- **Unload Mechanism Gate:** Confirm expanding-comb gravity drop vs. one-by-one ejector sweep after **Bench Test A** (before ordering Stage 2 motion hardware).
- **Arduino Nano USB Connector:** Confirm Mini-USB vs. USB-C data cable match when grabbing Nano(s) in lab.
- **OnShape Link:** Add OnShape project URL to Section 1 once the Variable Studio and Bench Test A Part Studio are created.
