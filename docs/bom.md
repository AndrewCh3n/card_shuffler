# Bill of Materials (BOM)

**Target Budget Ceiling:** `$150` (excluding filament & your existing Raspberry Pi 4B + Arduino Nano/Uno)  
**Estimated Build Cost:** **`~$128`** (can be trimmed to **`~$104`** with optional savings below)

---

## 1. Compute & Vision (`~$33`)

| Qty | Component | Recommended Spec / Search Term | Est. Cost | Notes |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **Raspberry Pi 4 Model B (4 GB)** | Fresh board on hand! *(Identical footprint/CPU to 8 GB)* | `$0` *(on hand)* | Runs Python CV (`<10 ms`/card) + FastAPI Phone Web UI + Wi-Fi hotspot |
| 1 | **MicroSD Card (32 GB)** | Class 10 / A1 (SanDisk / Samsung) | `$6` *(or `$0` if on hand)* | Raspberry Pi OS Lite (64-bit) |
| 1 | **Raspberry Pi Camera Module 3** | Standard FOV (75°), **Autofocus** (focuses down to `5 cm`!) | `$25` | Includes standard **15-pin CSI ribbon** that plugs straight into Pi 4B! *Budget swap:* Manual-focus OV5647 Pi Cam (`~$10`, saves `$15`) |
| 1 | **Pi 4 Passive Aluminum Heatsink Kit** | Stick-on aluminum heatsinks (or Armor heatsink case top) | `$2` | Keeps Pi 4B cool inside the enclosed electronics bay without noisy fans |
| 1 | **Arduino Nano (or Uno)** | ATmega328P + short USB-A data cable | `$0` *(on hand)* | Plugs straight into Pi 4B USB-A port (no OTG adapter needed!) |

---

## 2. Motion, Linear Hardware & Actuators (`~$54`)

| Qty | Component | Recommended Spec / Search Term | Est. Cost | Notes |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **Elevator Stepper Motor** | NEMA 17, `42×42×40 mm`, `1.8°` (200 steps/rev), `~1.0–1.5A` | `$10` | Drives the 54-slot elevator carriage |
| 1 | **Feeder Stepper Motor** | NEMA 17 **Pancake**, `42×42×23 mm`, `1.8°`, `~0.8–1.0A` | `$9` | Compact, whisper-quiet, millimeter feed control + reverse unjam |
| 2 | **Silent Stepper Drivers** | **TMC2209 v1.2 / v1.3** stepstick w/ heatsink | `$9` | StealthChop2 = nearly silent; run at 16× microstepping (`MS1=MS2=HIGH`) |
| 1 | **Linear Rail + Carriage** | **MGN12H `250 mm`** linear guide rail + block | `$14` | Zero-wobble elevator alignment into `1.2 mm` card slot gaps |
| 1 | **Leadscrew Kit** | **T8×8** (`250 mm`, 2 mm pitch, 8 mm lead, 4-start) + **anti-backlash POM nut** + `5 mm → 8 mm` flexible coupler | `$9` | Gives exact integer `800 steps` per `2.0 mm` slot; smooth & backlash-free |
| 1 | **Micro Servo** | **MG90S** metal-gear micro servo (`180°`) | `$3` *(or `$0` if used servo fits)* | Drives the expanding side-comb release linkage (~6 mm throw/side) |

---

## 3. Card Feeder Grip, Separator & Bearings (`~$9`)

| Qty | Component | Recommended Spec / Search Term | Est. Cost | Notes |
| :---: | :--- | :--- | :---: | :--- |
| 4–6 | **Silicone O-Rings (Feeder Tires)** | `24 mm OD × 3 mm CS` (or `25×3 mm`) **soft silicone** (Shore 50A–60A) | `$3` | Stretch onto 3D-printed drive hub; high grip on Bicycle Air-Cushion finish without scuffing |
| 4 | **Small Ball Bearings** | `625ZZ` (`5×16×5 mm`) or `608ZZ` (`8×22×7 mm`) | `$3` | Supports feeder idler pinch shaft & leadscrew top end |
| 1 | **Feeler Gauge / Brass Shim Strip** | `0.15 mm–0.30 mm` stainless shim stock or cheap feeler-gauge blade | `$3` | Forms the crisp, adjustable `~0.43 mm` single-card separator knife-edge (much more consistent than raw 3D-printed plastic!) |

---

## 4. Sensors, Lighting & Electronics (`~$22`)

| Qty | Component | Recommended Spec / Search Term | Est. Cost | Notes |
| :---: | :--- | :--- | :---: | :--- |
| 3 | **IR Optical Card Sensors** | **TCRT5000** digital breakout module (w/ comparator trim pot) OR IR break-beam sensor | `$3` | Hopper-empty (`D12`), scan-staged (`A0`), slot-exit/jam (`A1`) |
| 1 | **Micro Limit Switch** | KW11-3Z / standard 3D-printer endstop microswitch | `$1` | Bottom elevator homing switch (`slot 0`) |
| 1 | **Scan Tunnel White LEDs** | Short piece of **5V neutral-white COB LED strip** (`4000K–5000K`, ~5 cm) + `2N2222` / `IRLML2502` transistor + `1 kΩ` resistor | `$3` | Diffused behind a thin `0.8 mm` white PLA sheet for glare-free index reading |
| 1 | **USB-C PD Trigger Board** | **ZY12PDN** or DIP-switch USB-C PD decoy (`15V`, up to `3A`–`5A`) | `$4` | Set to **`15V`** and pair with a **`45W–65W`** USB-C PD brick or power bank (headroom for Pi 4B + steppers!) |
| 2 | **5V 3A Buck Converters** | Mini560 `5V` or XL4015/MP1584 adjustable (`1×` set to `5.1V` for Pi 4B, `1×` set to `5.0V` for servo/sensors/LEDs) | `$6` | **Two isolated bucks** prevent MG90S servo spikes from ever browning out the Pi 4B! |
| 1 | **Misc Power & Wiring** | Rocker switch (SPST), `470 µF 25V` + `100 µF 10V` electrolytic caps, perfboard (`50×70 mm`), `20 AWG` (for Pi 4 power) & `22 AWG` wire, short USB-A data cable (Pi 4 → Arduino) | `$5` | Use thick `20 AWG` short leads between Buck #1 and Pi 4B to avoid undervoltage warnings |

---

## 5. Fasteners & Hardware (`~$10`)

| Qty | Component | Recommended Spec / Search Term | Est. Cost | Notes |
| :---: | :--- | :--- | :---: | :--- |
| 1 kit | **M3 Screws + Heat-Set Brass Inserts** | `M3 × 6, 8, 12, 16 mm` SHCS + `M3 × 5 × 4 mm` knurled heat-set inserts (+ `4× M2.5` screws for Pi 4B mounting holes) | `$8` | Modular sub-assemblies bolt cleanly to a shared baseplate |
| 4 | **Neodymium Magnets** | `6 × 3 mm` round magnets | `$2` | Tool-less magnetic jam-access door on enclosure |
| 4 | **Rubber Feet** | Adhesive silicone bump-ons (`10–12 mm`) | *(optional / `$1`)* | Isolates stepper hum from tabletops |

---

## 6. Cost Summary & Ordering Strategy

| Category | Estimated Cost |
| :--- | :---: |
| Compute & Vision (Pi 4B on hand + Pi Cam v3 + SD + heatsink) | `~$33` |
| Motion & Actuators (2× NEMA 17 + 2× TMC2209 + MGN12H + T8 + MG90S) | `~$54` |
| Feeder Grip, Bearings & Shim | `~$9` |
| Sensors, Lighting & USB-C PD Dual-Buck Power | `~$22` |
| M3/M2.5 Fasteners, Heat-Set Inserts & Magnets | `~$10` |
| **Total (Full Quality Spec)** | **`~$128`** |
| **Optional Budget Trim** *(OV5647 manual-focus cam `-$15`, reuse servo `-$3`, reuse SD card `-$6`)* | **`~$104`** |

### Recommended Staged Ordering Plan
1. **Order Immediately (zero-risk parts):** Pi Camera Module 3 (includes 15-pin ribbon for Pi 4B!), M3 screw/insert kit, silicone O-rings, `625ZZ` bearings, feeler-gauge shim strip. *(You can run Bench Test A right away with filament only, and start testing CV on your Pi 4B as soon as the camera arrives!)*
2. **Order After Bench Test A (Expanding Comb Drop) Passes:** MGN12H `250 mm` rail, T8×8 leadscrew kit, 2× NEMA 17 + 2× TMC2209, MG90S servo, sensors, USB-C PD trigger + 2× `5V 3A` buck converters. *(That way if you adjust comb pitch or switch from gravity-drop to one-by-one unload, your rail/leadscrew length is 100% locked in first!)*
