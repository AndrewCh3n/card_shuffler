# Shared Ground Rules & Multi-Agent Workflow (`AGENTS.md`)

This project runs on a **1 Main Project Chat + Optional Per-Issue Focus Chats + Read-Only Q&A Chat** model backed by two complementary sources of truth:

- **Google Workspace (`Card Shuffler/` folder):** Live human-editable inventory, lab scouting, rough workbench notes, bench-test photos/videos, and PDF datasheets.
- **GitHub (`AndrewCh3n/card_shuffler`):** Versioned engineering truth — architecture, CAD specs, Arduino firmware, Python vision/web software, finalized build log, and structured **Module → Task → Subtask** GitHub Issues (`#2`–`#16`).

> **Core Rule:** No design decision, measurement, or parts change lives only in chat history. Every meaningful outcome must be written to Google Workspace or committed to GitHub so any fresh conversation starts with 100% current context.

---

## 1. Chat Roles & Ownership Boundaries (Zero Collisions)

| Chat Type | Purpose | Allowed Writes | Lifecycle |
| :--- | :--- | :--- | :--- |
| **Main Project Chat** *(Single Coordinator)* | Project-wide planning, merging PRs, syncing GitHub ↔ Google Drive, BOM updates, milestone/issue triage | `PROJECT_STATE.md`, `AGENTS.md`, `docs/build_log.md`, Google Drive/BOM Sheet, merging PRs, managing Issues/Milestones | Persistent (1 main thread) |
| **Per-Issue Focus Chat** *(Optional Parallel Work)* | Deep execution on **one specific GitHub Issue** (e.g., `#2`, `#4`, `#6`) | Only that issue's code/CAD/docs on branch `issue-<N>-<slug>`, PR (`Closes #N`), and comments/checklists on `#N`. **Do not** directly edit `PROJECT_STATE.md`, `AGENTS.md`, or the BOM Sheet (leave a note / `needs-bom` label for the Main Chat on merge). | Short-lived — archive as soon as the issue closes |
| **Q&A Chat** *(Quick Help)* | Explanations, debugging concepts, brainstorming, learning specs | **Read-only** (no edits to GitHub or Google Drive) | Any time / throwaway |

### Quick Starter Prompt for a Per-Issue Focus Chat
> *"Read `AGENTS.md`, `PROJECT_STATE.md`, and GitHub Issue `#N`, check the top of Drive `Running Notes & Scratchpad`, then let's work through Issue `#N` on branch `issue-N-...`."*

---

## 2. Mandatory Startup Checklist (Run Before Any Task)

Every session that edits code, CAD, docs, or tracking must run this quick sync before making changes:

1. **Pull latest GitHub state:** Run `git pull --ff-only origin main` and check open PRs.
2. **Read [`PROJECT_STATE.md`](PROJECT_STATE.md):** Confirm current build phase, locked-in specs, BOM snapshot, and active `ready-now` tasks.
3. **Check relevant GitHub Issues:** Inspect your target issue (`gh issue view <N>`) or filter open issues by readiness (`ready-now` / `waiting-on-parts`), module (`module:*`), or handoff labels.
4. **Check Google Workspace updates:** Read the newest dated entries at the top of [Card Shuffler — Running Notes & Scratchpad](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit), and check [Card Shuffler — Parts, Lab Scouting & Learning Tracker](https://docs.google.com/spreadsheets/d/1MSAsWFvpI-4053Ha5YDHNZjiihVYTBqtmWjEtyQ3ilA/edit) whenever parts, specs, or costs are touched.

---

## 3. Single Source of Truth Map

| Surface / Artifact | Location | Owner / Best Used For | Sync Rule |
| :--- | :--- | :--- | :--- |
| **Live BOM, Inventory & Lab Scouting** | [Parts, Lab Scouting & Learning Tracker (Google Sheet)](https://docs.google.com/spreadsheets/d/1MSAsWFvpI-4053Ha5YDHNZjiihVYTBqtmWjEtyQ3ilA/edit) | **Andrew & Main Chat** — live `On Hand` / `Scout in Lab` / `Buy Later` status, costs, lab list, learning notes | **Live master for inventory & budget.** Andrew can edit anytime directly in Sheets. |
| **Engineering BOM Spec** | [`docs/bom.md`](docs/bom.md) | **Main Chat / Builder** — versioned technical spec & staged ordering rationale | Periodic spec snapshot synced from engineering changes / Google Sheet. Do **not** track day-to-day inventory status independently here. |
| **Workbench Notes & Scratchpad** | [Running Notes & Scratchpad (Google Doc)](https://docs.google.com/document/d/1QMkdtJQ6tlluLkjEzu9P6Miww5D13ENVj85SN9NHgsI/edit) | **Andrew (primary)** — fast phone/bench notes, caliper readings, lab finds, ideas | Agents read newest entries on top; Main Chat promotes confirmed specs/results to `docs/build_log.md` or `docs/cad_spec.md`. |
| **Bench Test Media** | [Bench Tests & Media (Drive Folder)](https://drive.google.com/drive/folders/12iZSgKtl43777iYu8vOVGCT-oZCNFP-f) | **Andrew / Issue Chats** — photos, slow-mo drop videos, camera test frames | Keeps large binary media out of GitHub; reference filenames from `docs/build_log.md` or the GitHub Issue. |
| **Datasheets & References** | [Datasheets & References (Drive Folder)](https://drive.google.com/drive/folders/1dQ_bGhUrDYy7ffanITZEXH1IStnv-I3b) | **All sessions** — component pinouts, TMC2209 / PD trigger sheets, mechanical drawings | Reference links from `docs/architecture.md` or `docs/cad_spec.md` when needed. |
| **Live Project Snapshot** | [`PROJECT_STATE.md`](PROJECT_STATE.md) | **Main Chat** — 1-page current phase, blockers, BOM counts, `ready-now` issue queue, links | Update whenever phase, BOM summary, or completed milestones change. |
| **Build & Test Log** | [`docs/build_log.md`](docs/build_log.md) | **Main Chat / Issue PRs** — append-only record of how modules were printed, wired, tuned, and tested | Log every completed bench test, print tolerance change, and hardware iteration. |
| **Specs, CAD, Firmware, Software** | [`docs/`](docs/), [`cad/`](cad/), [`firmware/`](firmware/), [`software/`](software/) | **Main Chat & Per-Issue Chats** — source code, Arduino sketch, OnShape exports, architecture & CAD specs | Feature branches (`issue-<N>-<slug>`) + PRs into `main`. |
| **Module → Task → Subtask Tracker** | [GitHub Issues](https://github.com/AndrewCh3n/card_shuffler/issues) & [Milestones](https://github.com/AndrewCh3n/card_shuffler/milestones) | **Main Chat & Per-Issue Chats** — Phase Milestones + Module labels + Issue checklists | Single live task tracker. Check off `- [ ]` subtasks directly on the issue as steps complete. |

---

## 4. GitHub Taxonomy (Phases, Modules, Readiness & Handoffs)

- **Phases (Milestones):** `Phase 0: Setup & Sourcing` → `Phase 1: Bench Tests A & B` → `Phase 2: Optical Scan Tunnel` → `Phase 3: Mechatronic Integration` → `Phase 4: Final Enclosure`
- **Modules (`module:*`):**
  - `module:mechanics` — OnShape CAD, 3D printing, and mechanical bench tests
  - `module:vision` — Computer vision & card corner recognition
  - `module:electronics` — Arduino firmware, sensors, wiring, and power
  - `module:pi-integration` — Raspberry Pi 4B setup and full-system integration
  - `module:packaging` — Shared baseplate, electronics bay, and final enclosure
- **Readiness:**
  - `ready-now` — Unblocked today with on-hand hardware (no waiting on parts)
  - `waiting-on-parts` — Blocked until MicroSD card or Stage 1 / Stage 2 parts arrive
- **Work Type / Handoffs:**
  - `needs-build` — Engineering, CAD, firmware, wiring, or software build work
  - `needs-bom` — Parts spec changed, part found in lab, or Google Sheet BOM update needed
  - `needs-pm` — Roadmap, milestone, `PROJECT_STATE.md`, or task breakdown update needed
  - `bench-test` — Physical 3D print or bench-test verification task
  - `decision` — Architectural or mechanical trade-off needing Andrew's call before locking in

---

## 5. Wrap-Up Checklist (Before Ending Any Session)

- **If in a Per-Issue Focus Chat:**
  1. Commit and push changes to `issue-<N>-<slug>` and open a PR referencing `Closes #N` (or `Refs #N`).
  2. Check off completed `- [ ]` subtasks and comment measurements/results directly on Issue `#N`.
  3. Add a `needs-bom` or `needs-pm` comment/label if parts or downstream plans changed, then archive the chat once closed.
- **If in the Main Project Chat:**
  1. Merge reviewed PRs and update [`PROJECT_STATE.md`](PROJECT_STATE.md) / [`docs/build_log.md`](docs/build_log.md).
  2. Sync any inventory changes with the Google Sheet BOM and flip newly unblocked issues from `waiting-on-parts` to `ready-now`.
