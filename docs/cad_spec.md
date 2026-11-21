# OnShape Parametric CAD Specification & Bench-Test Plan

This blueprint gives you every dimension, clearance, print orientation, and modular mounting interface needed to start modeling in OnShape cleanly — designed for a **`≥220 × 220 mm` bed**, **`0.4 mm` nozzle**, **`0.2 mm` layer height**, **PLA or PETG**, and **M3 heat-set brass inserts**.

---

## 1. OnShape Global Variables (`Variable Studio`)

Create a single **Variable Studio** in OnShape and reference these variables across all Part Studios so tuning a tolerance takes 5 seconds:

| Variable | Value | Purpose / Rationale |
| :--- | :---: | :--- |
| `#card_w` | `63.5 mm` | Standard Bicycle Poker card width (short edge, across channel) |
| `#card_l` | `88.9 mm` | Standard Bicycle Poker card length (long edge, feed axis) |
| `#card_t` | `0.29 mm` | Typical Bicycle Poker thickness (`0.27–0.31 mm` worn/new range) |
| `#ch_clear_w` | `1.5 mm` | Side-to-side channel clearance (`#card_w + #ch_clear_w = 65.0 mm`) |
| `#ch_clear_l` | `2.1 mm` | Front-to-back chute clearance (`#card_l + #ch_clear_l = 91.0 mm`) |
| `#slot_count` | `54` | 52 standard cards + 2 Jokers |
| `#fin_t` | `0.8 mm` | Comb ledge thickness (`2 × 0.4 mm` nozzle perimeters — crisp, rigid) |
| `#slot_gap` | `1.2 mm` | Clear vertical opening per card (`~4× #card_t`, forgiving entry!) |
| `#slot_pitch` | `2.0 mm` | `#fin_t + #slot_gap` (`800` stepper microsteps on T8×8 leadscrew) |
| `#comb_h` | `110.0 mm` | `(#slot_count × #slot_pitch) + 2.0 mm` end caps |
| `#ledge_depth` | `5.0 mm` | How far each comb fin reaches under left & right card edges (leaves `53.5 mm` center span — zero sag!) |
| `#comb_throw` | `6.5 mm` | Outward travel per side when servo opens the combs (`#ledge_depth + 1.5 mm` clearance) |
| `#sep_gap` | `0.43 mm` | Target single-card separator gap (`1.5× #card_t`, well below `2× #card_t = 0.58 mm`) |
| `#m3_insert_d` | `4.6 mm` | Hole diameter for `M3 × 5 × 4 mm` brass heat-set inserts (`depth = 5.5 mm`) |
| `#m3_clear_d` | `3.4 mm` | Clearance through-hole for M3 bolts |
| `#fit_loose` | `0.30 mm` | Clearance for sliding 3D-printed parts |
| `#fit_snug` | `0.15 mm` | Clearance for press/alignment bosses |

---

## 2. Overall Tower Packaging Envelope

- **Footprint:** `~155 mm (W) × 225 mm (D)` (comfortably fits on a `220 × 220 mm` bed if baseplate is split or `215 mm` deep — let's target **`150 mm (W) × 215 mm (D)`** so the entire baseplate prints as **one single piece** on a `220 × 220 mm` bed!)
- **Height:** `~265 mm (H)`
- **Card Path (Side View — Left to Right, Staying Flat):**

```text
          ┌─────────────────────────┐
          │  Module 1: Input Hopper │  (Gravity weight block on top of deck)
          │  [===== 52 Cards =====] │
          │  (O) Roller  |<-0.43mm  │  (Feeder stepper + adjustable shim gate)
          └──────────────┴──────────┤
                         ▼          │
               ┌────────────────────┴────┐
               │ Module 2: Scan Tunnel   │  (Flat card slides over bottom glass/open
               │  [Diffused White LEDs]  │   window; Pi Cam below looks UP at corner)
               │      ▲ Pi Cam (65mm)    │
               └────────────────────┬────┘
                                    │ Card enters at fixed feed plane (Z = ~135 mm)
                                    ▼
                         ┌────────────────────┐
                         │ Module 3: 54-Slot  │  ◄── MGN12H rail + T8×8 leadscrew
                         │  Expanding Comb    │      travels 106 mm vertically
                         │  (110 mm tall)     │      so any slot 0..53 aligns with
                         └────────────────────┘      the feed plane!
                                    │
                                    ▼ (At end of sort: combs open 6.5 mm/side)
                         ┌────────────────────┐
                         │  Output Tray (Z=0) │  ◄── Snug 65 × 91 mm catcher drawer
                         └────────────────────┘
```

---

## 3. Module-by-Module Mechanical Dimensions

### Bench Test A (Print First! Zero Electronics): Expanding-Comb Gravity Drop
Before modeling rails, motors, or an enclosure, print a **manual desktop test rig** to validate the riskiest assumption: *do 52 spaced-out cards drop straight and flat into the output tray without flipping or jamming?*

- **Parts to model in OnShape:**
  1. **Left & Right 54-Slot Combs (2×):**
     - Spine length = `#comb_h` (`110 mm`), depth = `#card_l + 4 mm` (`93 mm`), spine thickness = `4.0 mm`.
     - 54 horizontal fins protruding inward `#ledge_depth` (`5.0 mm`), thickness `#fin_t` (`0.8 mm`), pitch `#slot_pitch` (`2.0 mm`).
     - **Critical Lead-In Chamfer:** Add a `0.35 mm × 45°` chamfer on the **card-entry front edge** of every fin so incoming cards self-guide into the `1.2 mm` gap instead of hitting a flat wall.
     - **Print Orientation:** Print **lying flat on its outer spine** (fins standing straight UP along Z). Zero overhangs, glass-smooth fin faces, ultra-accurate `2.0 mm` pitch!
  2. **Snug Drop Chute / Chimney (1×):**
     - Inner dimensions: `(#card_w + 1.5 mm) × (#card_l + 2.0 mm)` = **`65.0 × 91.0 mm`**.
     - Cut side windows along left and right walls where the two comb rails poke inward by `5.0 mm`, and retract outward by `6.5 mm` (leaving `1.5 mm` behind the inner chute wall when open so zero fin tips protrude!).
     - **Air Relief Vents:** Cut `4 × 15 mm` vertical air vents near the bottom corners of the chute so trapped air escapes symmetrically as the 52-card column compresses downward (prevents the top cards from "floating" or tilting on an air cushion!).
  3. **Simple Output Catcher Base (1×):**
     - Snug `65.0 × 91.0 mm` floor with finger-scoop cutouts on front and back so you can lift the finished deck out easily.
- **Pass Criteria:** Manually slide 52 cards into the slots, pull the two combs outward simultaneously by hand (`~6.5 mm` each side), and verify **10 out of 10 drops** settle completely flat and in exact order.
  - *If cards tilt or catch:* First check chute clearance (try tightening to `64.5 × 90.5 mm`) and air vents; if it still isn't `10/10` reliable, switch Module 3 to the **One-by-One Ejector Sweep** before ordering the MG90S comb linkage.

---

### Module 1: Single-Card Feeder & Separator (Bench Test B)
Getting **1 and only 1 card** out reliably is the #1 mechanical craft challenge in any card machine.

- **Input Hopper Cavity:** `65.0 mm (W) × 91.0 mm (L) × 30.0 mm (H)` (easily holds 54 cards = `15.7 mm` + a `10 mm` weighted follower block).
- **Weighted Follower Block:** 3D-printed `62 × 86 × 10 mm` block with pockets to glue in ~`60–80 g` of pennies, steel washers, or M8 nuts. Keeps consistent downward pressure even down to the final 2 cards!
- **Drive Roller:**
  - `24–28 mm` OD 3D-printed hub mounted directly onto the **NEMA 17 Pancake** `5 mm` D-shaft (with an M3 set-screw or flat-spot clamp).
  - Wrap 2× **soft silicone O-rings** (`24 × 3 mm` or `25 × 3 mm`) spaced `~28 mm` apart symmetrically near the card centerline (avoiding the corner index zone so roller dust never marks the index!).
  - Protrude the silicone tires **`1.2 mm`** through slots in the hopper floor, positioned **`~25 mm` back from the exit gate**.
- **Adjustable Single-Card Separator Gate (Crucial!):**
  - Do **not** rely on a raw 3D-printed `0.45 mm` slot — printer Z tolerances (`±0.15 mm`) will either jam 1 card (`0.29 mm`) or pass 2 cards (`0.58 mm`).
  - Instead, clamp a straight strip of **stainless feeler-gauge / brass shim (`0.20–0.30 mm` thick)** onto a slotted vertical adjustment bracket using **2× M3 screws into heat-set inserts**.
  - Set the gap between the bottom floor and shim knife-edge using a **`0.40 mm` or `0.45 mm` feeler gauge** (just slip the gauge under the blade and tighten the M3 screws!).
  - Optional upgrade if slippery new cards still double-feed: glue a tiny `10 × 15 mm` patch of soft silicone/rubber pad directly under the gate opposite a counter-friction pinch point (inkjet-printer retard pad).
- **Pinch-Roller Exit Pair (Right Past the Gate):**
  - Once the leading edge of a single card passes the separator gate, a secondary silicone pinch roller (driven by the same feeder shaft via a simple printed gear/GT2 mini-belt, or a spring-loaded `625ZZ` idler pressing down on a second silicone wheel) takes over to push the card smoothly through the scan tunnel and all the way into the elevator comb!
  - **Center-to-center spacing** between the hopper roller and exit pinch roller must be **`< 75 mm`** (shorter than `#card_l = 88.9 mm`) so the card is *always* positively driven and never gets stranded between rollers!
- **Hopper-Empty IR Sensor (`D12`):** Mount TCRT5000 underneath a `12 × 8 mm` window in the hopper floor (`~15 mm` behind the drive roller).
- **Pass Criteria:** Run 5 full decks (260 cards) — both a brand-new Bicycle deck and a worn deck — targeting **0 double-feeds and 0 jams**.

---

### Module 2: Optical Scan Tunnel
- **Card Channel:** Flat, low-friction guide floor `65.0 mm` wide × `~95 mm` long, ceiling height `~3.0 mm` above floor (keeps cards dead flat at a constant focal distance from the camera!).
  - **Card-Safe Floor:** Print the floor face-down on a smooth PEI sheet (or tape a strip of smooth `0.5 mm` PETG/clear polycarbonate sheet over it) so cards glide silently with zero scuffing.
- **Corner Inspection Window:**
  - Cut a **`26 × 34 mm` rectangular window** in the floor under the **leading-left corner** of the card (where the top-left rank + suit index sits on Bicycle Poker cards: index spans roughly `3–14 mm` from left edge and `4–24 mm` from leading edge).
  - Add a tiny `0.8 mm` subtle chamfer on the window's far edge so a card corner can *never* dip into the hole and catch! (Or cover the window flush with a `1.0 mm` anti-reflective microscope glass slide / clear acrylic piece.)
- **Camera & Lighting Darkbox (Under the Floor):**
  - Mount **Pi Camera Module 3** pointing straight UP at the corner window at a focal distance of **`65–75 mm`** (Module 3 autofocuses crisply down to `50 mm`, filling the frame with the corner index!).
  - Surround the chamber with opaque **matte-black PLA walls** so room lighting has zero effect on recognition.
  - Mount two short strips of **5V neutral-white COB LEDs** at `~45°` angles on either side of the camera lens (never straight behind the lens — avoids specular glare off glossy Bicycle card varnish!) behind a `0.8 mm` white PLA diffuser strip.
- **IR Sensors:**
  - **`SCAN_ENTRY_SENS` (`A0`):** Positioned so it triggers precisely when the card's leading edge is centered over the `26 × 34 mm` window.
  - **`SLOT_EXIT_SENS` (`A1`):** Positioned `~5 mm` before the tunnel exit into the elevator comb to confirm the card's trailing edge clears cleanly into the slot.

---

### Module 3: Vertical Linear Elevator & Expanding-Comb Carriage
- **Linear Motion Spine:**
  - Mount the **`250 mm` MGN12H linear rail** vertically onto a rigid `8 mm` thick printed (or aluminum-extrusion-backed) rear spine bolted to the baseplate.
  - Mount the **NEMA 17 (40 mm) stepper** at the bottom of the spine, coupled via a `5 → 8 mm` flexible coupler to the **`250 mm` T8×8 leadscrew**, with the top end stabilized by a `608ZZ` bearing pocket.
  - Bolt the **elevator carriage bracket** to the MGN12H block (`4× M3 × 8 mm`) and the T8 anti-backlash POM nut (`4× M3 × 10 mm`).
- **Expanding Comb Linkage (Mounted on Carriage):**
  - Left and right comb rails slide outward horizontally (`6.5 mm` per side) on two short horizontal printed dovetail / `4 mm` steel dowel guides (or simple symmetric **parallelogram swing arms** — parallelogram arms have zero sliding friction and print trivially!).
  - A single **MG90S micro servo** mounted on the back of the carriage drives a small symmetrical dual-link bellcrank (`2× 15 mm` link rods) to pull both comb rails outward identically (`CLOSED = 20°`, `OPEN = 110°`).
  - *Alternative fallback:* If Bench Test A favors one-by-one unload, omit the servo linkage and make the 54-slot comb a single rigid U-shaped piece.
- **Homing Switch (`D8`):** Mount the KW11 microswitch at the bottom of the spine so the carriage trips it at `physical_slot = 0` (`z = 0.0 mm`). Set the vertical height of Module 1 + 2 so the card exit plane aligns precisely with `slot 0` when the elevator is at `z = 106.0 mm` (highest travel) and aligns with `slot 53` when the elevator is at `z = 0.0 mm` (wait — verify direction!):
  - **Check Z Coordinate Kinematics!**
    - Let the fixed **card-feed exit plane** be at height `Z_feed = 135 mm` above the baseplate.
    - When the elevator is at its **lowest** position (bottom home switch, `Z_carriage = 0 mm`), the **highest** comb slot (`slot 53`, at top of comb = `+106 mm` above slot 0) aligns with `Z_feed`! Wait: check the output tray clearance too!
    - Output tray height = `~25 mm` above baseplate.
    - When elevator is at **bottom home (`Z_carriage = 0`)**:
      - `slot 0` sits right above the output tray at `Z = 27 mm` (`2 mm` clearance above tray lip — **minimum possible drop distance when unloading!**).
      - `slot 53` sits at `Z = 27 + 106 = 133 mm` → align **`Z_feed = 133 mm`**!
    - To align **`slot s`** (`0..53`) with `Z_feed = 133 mm`, the elevator moves UP by:
      $$\Delta Z(s) = (53 - s) \times 2.0\text{ mm}$$
      - `s = 53` (topmost slot) → `ΔZ = 0.0 mm` (bottom home — already aligned with feed plane!)
      - `s = 0` (bottommost slot) → `ΔZ = 106.0 mm` (carriage rises `106 mm`, bringing slot 0 up to `Z_feed = 133 mm`; top of comb reaches `133 + 106 = 239 mm` — comfortably inside a **`~265 mm`** tower!).
    - **BONUS:** When unloading at the end of the sort, moving to `ΔZ = 0 mm` (bottom home!) automatically places `slot 0` just **`2 mm` above the output tray floor**, keeping the drop height as short and gentle as humanly possible!
    - *This exact kinematic formula (`target_mm = (53 - slot) * 2.0`) is reflected directly in `firmware/shuffler_controller/shuffler_controller.ino`!*

---

### Module 4 & 5: Baseplate, Electronics Bay & Enclosure
- **Shared Baseplate (`150 × 215 × 6 mm`):** Prints flat on a `220 × 220 mm` bed. Embeds an M3 heat-set insert grid so Modules 1, 2, 3, and the electronics tray bolt down rigidly and can be swapped independently.
- **Electronics Bay (Sized for Raspberry Pi 4 Model B):**
  - Tucked neatly beneath Module 1 & Module 2 (`~140 mm W × 105 mm D`, with `~49 mm` vertical headroom beneath the camera darkbox at `Z = 58 mm`).
  - **Raspberry Pi 4B Mounting Footprint:** **`85 × 56 mm`** board, **`~20 mm`** tall (leave `30 mm` vertical clearance for passive aluminum heatsinks + CSI ribbon bend radius), **`58 × 49 mm` `M2.5` mounting hole pattern** on `5 mm` printed standoffs.
  - **Port Clearance:** Orient the Pi 4B so its full-size **USB-A ports face inward** toward the Arduino Nano perfboard (`50 × 70 mm`) with `~25 mm` plug clearance for a short USB-A data cable, and keep the **micro-HDMI / Ethernet / SD card edge** accessible from a side/rear service cutout for easy debugging.
  - **Cooling Ventilation:** Add louvered passive air vents along the bottom and upper rear walls of the electronics bay (natural chimney convection keeps a Pi 4B with stick-on aluminum heatsinks well under thermal throttling during CV workloads, with zero fan noise!).
  - **Power Components:** Mount the USB-C PD trigger (recessed rear USB-C port), main rocker switch, and **two isolated `5V 3A` buck converters** on dedicated standoffs next to the perfboard.
- **Tool-less Jam Access:** Attach the top cover over the feeder/scan tunnel and the front panel of the elevator chute using **`6 × 3 mm` neodymium magnets** so any bent card can be cleared in 2 seconds without tools.
- **Exterior Styling:** Matte-black PLA/PETG outer shell with zero exposed buttons or screens (only the rear USB-C port + power switch and front output deck slot).

---

## 4. Recommended OnShape Build & Print Order

1. **Print 1 — Bench Test A (`bench_test_a_comb_drop`):** 2× 54-slot combs + vented drop chimney + tray base (~4–5 hrs print, `~$2` filament). Manually load & drop 52 cards 10 times.
2. **Print 2 — Bench Test B (`bench_test_b_feeder`):** Hopper + weighted block + silicone-O-ring hub + adjustable metal shim gate. Bench-test feeding 260 cards cleanly with the NEMA 17 pancake + Arduino Nano.
3. **Print 3 — Module 2 (`module_2_scan_tunnel`):** Attach darkbox + Pi Camera Module 3 + diffused LEDs right after feeder exit. Run `software/scripts/calibrate_vision.py` (Phase 2) to verify `52/52` recognition accuracy.
4. **Print 4 — Module 3 (`module_3_elevator`):** Bolt MGN12H rail + T8 leadscrew + motorized expanding comb onto the shared baseplate and run full end-to-end automated sorts!
5. **Print 5 — Module 5 (`module_5_enclosure`):** Wrap finalized internals in the sleek magnetic-access housing.
