# Engineering Build & Test Log

This append-only log tracks **how the card shuffler is actually built, printed, wired, tuned, and tested** — including print tolerances, caliper measurements, bench-test pass rates, and design revisions.

> **Workflow Note:** Drop quick, rough observations into [Card Shuffler — Running Notes & Scratchpad (Google Doc)](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit) while at the workbench, and upload photos/videos to [Bench Tests & Media (Drive)](https://drive.google.com/drive/folders/12iZSgKtl43777iYu8vOVGCT-oZCNFP-f). Promote verified results and engineering decisions here so they stay versioned alongside the specs and code.

---

## Entry Template (Copy for New Entries — Newest First)

```markdown
## YYYY-MM-DD — [Module / Bench Test Title]

- **Phase / Module:** Phase X — Module / Bench Test name
- **Related Issue / PR:** #__ (or N/A)
- **What Was Built or Tested:**
  - Concise summary of printed parts, wiring, firmware, or test rig setup.
- **Measured Results & Tolerances:**
  - Key dimensions, pass/fail counts (e.g., 10/10 drops, 0/260 double-feeds), filament/nozzle settings, voltage readings.
- **Decisions & Spec Impact:**
  - Any updates needed to `docs/cad_spec.md`, `docs/architecture.md`, firmware constants, or Google Sheet BOM.
- **Media & Follow-Ups:**
  - Filenames in Drive `Bench Tests & Media/` and any GitHub issues opened (`needs-bom`, `needs-build`, `needs-pm`).
```

---

## 2026-11-21 — Baseline Architecture, Code & Multi-Agent Build Workflow Established

- **Phase / Module:** Phase 0 — Setup & Sourcing
- **Related Commit:** `e36df7b` (*Initial card shuffler architecture, BOM, CAD spec, Arduino firmware, vision studio, and web UI*)
- **What Was Built or Tested:**
  - Locked in baseline single-pass 54-slot vertical linear elevator architecture (`2.0 mm` slot pitch, `1.2 mm` clear slot gap, `0.8 mm` comb fin thickness, `106 mm` vertical travel).
  - Checked in initial Arduino motion controller (`firmware/shuffler_controller/shuffler_controller.ino`) and Python deck planner, OpenCV vision studio, serial bridge, FastAPI phone Web UI, simulator, and unit tests (`software/`).
  - Organized dedicated Google Drive workspace (`Card Shuffler/` containing the live `Parts, Lab Scouting & Learning Tracker` Sheet, `Running Notes & Scratchpad` Doc, `Bench Tests & Media/`, and `Datasheets & References/`).
  - Established shared multi-agent ground rules (`AGENTS.md`), live dashboard (`PROJECT_STATE.md`), handoff labels (`needs-build`, `needs-bom`, `needs-pm`, `bench-test`, `decision`), and Phase 0–4 milestones.
- **Measured Results & Tolerances:**
  - No physical prints or hardware tests executed yet; baseline target card spec is standard Bicycle Poker (`63.5 × 88.9 × 0.29 mm`) — verify actual deck thickness with calipers prior to Bench Test B separator shim tuning.
- **Decisions & Spec Impact:**
  - **BOM Master Rule:** Google Sheet `Parts_Tracker` is the live inventory/cost master (`9` On Hand, `13` Scout in Lab, `5` Stage-1 buys, `6` Stage-2 buys; `~$100` est. buy-later vs. `$150` ceiling). `docs/bom.md` remains the engineering spec summary.
  - **Stage 2 Ordering Gate:** Hold Stage 2 linear-motion & power hardware orders until **Bench Test A** confirms expanding-comb drop geometry (`10/10` flat 52-card drops).
- **Media & Follow-Ups:**
  - Next physical build milestone: Model & print **Bench Test A (`bench_test_a_comb_drop`)** per [`docs/cad_spec.md`](cad_spec.md).
