# Shared Ground Rules & Multi-Agent Workflow (`AGENTS.md`)

This project runs on a **1 Parallel HQ + Short-Lived Topic Side Chats** model backed by two complementary sources of truth:

- **Google Workspace (`Card Shuffler/` folder):** Live human-editable inventory, lab scouting, rough workbench notes, bench-test photos/videos, and PDF datasheets.
- **GitHub (`AndrewCh3n/card_shuffler`):** Versioned engineering truth — architecture, CAD specs, Arduino firmware, Python vision/web software, finalized build log, and async handoff issues.

> **Core Rule:** No design decision, measurement, or parts change lives only in chat history. Every meaningful outcome must be written to Google Workspace or committed to GitHub so any fresh conversation starts with 100% current context.

---

## 1. Mandatory Startup Checklist (Run Before Any Task)

Every conversation — whether **Parallel HQ** (`/teamwork` / multi-subagent) or a **short-lived topic side chat** — must run this quick sync before making changes:

1. **Pull latest GitHub state:** Run `git pull --ff-only origin main` (or check the active branch/PRs).
2. **Read [`PROJECT_STATE.md`](PROJECT_STATE.md):** Confirm current build phase, locked-in specs, BOM snapshot, and active blockers.
3. **Check open GitHub Issues:** Filter by handoff labels (`needs-build`, `needs-bom`, `needs-pm`, `bench-test`, `decision`) to see pending cross-role work.
4. **Check Google Workspace updates:** Read the newest dated entries at the top of [Card Shuffler — Running Notes & Scratchpad](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit), and check [Card Shuffler — Parts, Lab Scouting & Learning Tracker](https://docs.google.com/spreadsheets/d/1MSAsWFvpI-4053Ha5YDHNZjiihVYTBqtmWjEtyQ3ilA/edit) whenever parts, specs, or costs are touched.

---

## 2. Single Source of Truth Map

| Surface / Artifact | Location | Owner / Best Used For | Sync Rule |
| :--- | :--- | :--- | :--- |
| **Live BOM, Inventory & Lab Scouting** | [Parts, Lab Scouting & Learning Tracker (Google Sheet)](https://docs.google.com/spreadsheets/d/1MSAsWFvpI-4053Ha5YDHNZjiihVYTBqtmWjEtyQ3ilA/edit) | **Logistics / BOM & Andrew** — live `On Hand` / `Scout in Lab` / `Buy Later` status, costs, lab list, learning notes | **Live master for inventory & budget.** Andrew can edit anytime directly in Sheets. |
| **Engineering BOM Spec** | [`docs/bom.md`](docs/bom.md) | **Builder / Parallel HQ** — versioned technical spec & staged ordering rationale | Periodic spec snapshot synced from engineering changes / Google Sheet. Do **not** track day-to-day inventory status independently here. |
| **Workbench Notes & Scratchpad** | [Running Notes & Scratchpad (Google Doc)](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit) | **Andrew (primary)** — fast phone/bench notes, caliper readings, lab finds, ideas | Agents read newest entries on top; promote confirmed specs/results to `docs/build_log.md` or `docs/cad_spec.md`. |
| **Bench Test Media** | [Bench Tests & Media (Drive Folder)](https://drive.google.com/drive/folders/12iZSgKtl43777iYu8vOVGCT-oZCNFP-f) | **Andrew / Builder** — photos, slow-mo drop videos, camera test frames | Keeps large binary media out of GitHub; reference filenames from `docs/build_log.md`. |
| **Datasheets & References** | [Datasheets & References (Drive Folder)](https://drive.google.com/drive/folders/1dQ_bGhUrDYy7ffanITZEXH1IStnv-I3b) | **All roles** — component pinouts, TMC2209 / PD trigger sheets, mechanical drawings | Reference links from `docs/architecture.md` or `docs/cad_spec.md` when needed. |
| **Live Project Snapshot** | [`PROJECT_STATE.md`](PROJECT_STATE.md) | **All roles** — 1-page current phase, blockers, BOM counts, links | Update whenever phase, major specs, or blockers change. |
| **Build & Test Log** | [`docs/build_log.md`](docs/build_log.md) | **Builder** — append-only record of how modules were printed, wired, tuned, and tested | Log every completed bench test, print tolerance change, and hardware iteration. |
| **Specs, CAD, Firmware, Software** | [`docs/`](docs/), [`cad/`](cad/), [`firmware/`](firmware/), [`software/`](software/) | **Builder** — source code, Arduino sketch, OnShape exports, architecture & CAD specs | Use feature branches + PRs for non-trivial changes. |
| **Async Handoff Queue & Phases** | [GitHub Issues](https://github.com/AndrewCh3n/card_shuffler/issues) & [Milestones](https://github.com/AndrewCh3n/card_shuffler/milestones) | **Planning / Parallel HQ / All roles** — conflict-free cross-role task queue | Create or comment on labeled issues instead of relying on chat memory. |

---

## 3. Handoff Labels & Phase Milestones

Use GitHub Issues as the conflict-free message bus between side chats and Parallel HQ:

- **`needs-build`** — Engineering, CAD, firmware, wiring, or software build work required.
- **`needs-bom`** — Parts spec changed, part found in lab, or Google Sheet BOM update needed.
- **`needs-pm`** — Roadmap, milestone, `PROJECT_STATE.md`, or task breakdown update needed.
- **`bench-test`** — Physical 3D print or bench-test verification task (e.g., Bench Test A / B).
- **`decision`** — Architectural or mechanical trade-off that needs Andrew's call before locking in.

Assign issues to the matching phase milestone (`Phase 0` through `Phase 4`).

---

## 4. Conflict Prevention & Branch Hygiene

- **One active writer per surface:** Avoid running a Parallel HQ sync sweep on the exact same files or Google Sheet tabs while actively editing them in a side chat.
- **Branch + PR by default:** Side chats and agents should push repo edits to descriptive feature branches (e.g., `build/bench-test-a`, `docs/sync-bom-spec`) and open a PR into `main`, unless Andrew explicitly asks to commit directly to `main`.
- **Archive finished side chats:** Once a topic side chat merges/pushes its output and files any follow-up GitHub issues, close/archive it so future work always starts clean from the latest repo + Drive state.

---

## 5. Wrap-Up Checklist (Before Ending Any Session)

1. Commit and push all code, CAD exports, or doc changes (no unpushed decisions left in local VM state).
2. Update [`PROJECT_STATE.md`](PROJECT_STATE.md) if the active phase, BOM summary, or open decisions changed.
3. Append any physical build/test findings to [`docs/build_log.md`](docs/build_log.md).
4. Open or update a GitHub Issue with `needs-bom`, `needs-build`, or `needs-pm` if another workstream needs to follow up.
