# ChatGPT Prompt: Build Accurate 3D Model of TapFlow Project

Copy and paste the prompt below into ChatGPT (with GPT-4o or image generation capabilities):

---

## PROMPT:

Build an accurate, detailed, engineering-grade 3D model/render of the **TapFlow** water monitoring system. This is a **small-scale testing setup** (not a full house) — rooms should be compact mock-up boxes, not real rooms. The model must show exact component placements, sizes, plumbing paths, and electrical wiring routes. Use realistic materials and colors.

### PROJECT OVERVIEW

TapFlow is an RFID-based automatic water and electrical line control system with water flow anomaly detection. It uses 4 ESP32 microcontrollers communicating wirelessly via ESP-NOW, with a centralized main unit controlling solenoid valves and a web dashboard via Firebase.

---

### LAYOUT — TOP-DOWN VIEW

```
                    ┌──────────────┐
                    │  WATER TANK  │
                    │  (500-1000L) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  1" PIPE     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  REDUCER     │
                    │  1" → 1/2"   │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │    MAIN CONTROL ZONE    │
              │    (Main ESP32 Box)     │
              │                         │
              │  Solenoid 1 → Flow      │
              │  Sensor → Solenoid 2    │
              └────────────┬────────────┘
                           │
                    ┌──────▼───────┐
                    │ T-CONNECTOR  │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼────┐ ┌───────▼──────┐
     │  ROOM 1     │ │ ROOM 2  │ │   ROOM 3     │
     │ (Bathroom)  │ │(Kitchen)│ │  (Shower)    │
     └─────────────┘ └─────────┘ └──────────────┘
```

---

### COMPONENT DIMENSIONS (use these exact sizes)

#### Enclosures (IP67 Waterproof ABS Box)
- **Size:** 175mm × 125mm × 75mm (L × W × H)
- **Color:** Light gray / off-white ABS plastic
- **Quantity:** 4 (one per ESP32)
- **Cable glands:** PG9/PG11 on the sides for cable entry
- **Mounting:** M3 screws + standoffs inside

#### ESP32 Dev Board (on Expansion Board)
- **ESP32 Board:** 52mm × 28mm
- **Expansion Board:** 75mm × 55mm (with screw terminals on all 4 sides)
- **Position:** Centered inside enclosure, mounted on standoffs

#### Power Supply (S-60-12)
- **Size:** 100mm × 50mm × 30mm (metal cage)
- **Color:** Silver/aluminum metal
- **Position:** Inside enclosure, next to ESP32

#### Buck Converter (LM2596S)
- **Size:** 43mm × 21mm × 5mm (blue PCB module)
- **Position:** Inside enclosure, near ESP32

#### DC Power Jack Adapter
- **Size:** 38mm × 14mm × 13mm (black + green)
- **Position:** Connected between PSU screw terminals and expansion board DC jack

#### 2CH Relay Module (Main ESP32)
- **Size:** 50mm × 40mm × 18mm (blue relay modules on PCB)
- **Position:** Inside main enclosure, near ESP32

#### 1-ch Relay Module (Room ESP32s)
- **Size:** 35mm × 25mm × 15mm (blue relay on PCB)
- **Position:** Inside room enclosures

#### Fotek 40A SSR (Room ESP32s)
- **Size:** 58mm × 45mm × 32mm (red/black solid-state relay)
- **Position:** Inside room enclosures, near relay

#### MFRC522 RFID Reader
- **Size:** 40mm × 60mm (blue PCB with antenna traces)
- **Position:** Mounted on front face of room enclosure (antenna facing out)
- **Connection:** Ribbon cable going inside enclosure

#### YF-S201 Flow Sensor
- **Size:** 34mm diameter × 34mm long (brass body, 1/2" NPT threads)
- **Color:** Brass/gold body, black plastic top with 3 wires
- **Position:** In-line with PPE pipe (screwed into pipe fittings)

#### Solenoid Valve 1/2" NC
- **Size:** 40mm × 30mm × 50mm (brass body, black coil on top)
- **Color:** Brass body, black coil housing
- **Wires:** 2 wires (red + black) going to relay
- **Position:** In-line with PPE pipe, inside main control zone

#### Check Valve 1/2" Brass
- **Size:** 30mm × 20mm diameter (brass body with arrow marking)
- **Color:** Brass/gold
- **Position:** In-line with PPE pipe, after flow sensor in each room

#### PPE Pipe
- **Diameter:** 1/2" (12.7mm outer diameter)
- **Color:** Light green / teal (typical PPR/PPE color)
- **Fittings:** Tees, elbows, couplers — all 1/2" PPR

#### Water Tank
- **Size:** Small test tank, approximately 30cm × 30cm × 60cm (for testing)
- **Color:** Blue or white plastic
- **Position:** At the top/start of the plumbing line

---

### PLUMBING PATH (show with green PPE pipes)

1. **Water Tank** → 1" pipe exit
2. **Reducer fitting** (1" to 1/2")
3. **1/2" PPE pipe** → **Solenoid Valve 1** (main enclosure)
4. **1/2" PPE pipe** → **Flow Sensor** (main enclosure, between solenoids)
5. **1/2" PPE pipe** → **Solenoid Valve 2** (main enclosure)
6. **1/2" PPE pipe** → **T-Connector** (splits into 3)
7. **Branch 1** → **Check Valve** → **Room 1 Flow Sensor** → **Room 1 Faucet**
8. **Branch 2** → **Check Valve** → **Room 2 Flow Sensor** → **Room 2 Faucet**
9. **Branch 3** → **Check Valve** → **Room 3 Flow Sensor** → **Room 3 Faucet**

All pipe joints are heat-fused (PPR welding) — show smooth joints, no clamps.

---

### ELECTRICAL WIRING (show with colored wires)

#### Wire Color Code:
- **Red** = VCC / Power positive (5V or 12V)
- **Black** = GND
- **Yellow** = Signal / Data
- **Green** = SPI (MOSI/MISO/SCK)
- **White** = 220V AC (for SSR output)

#### Room ESP32 Wiring (×3 — same for each):
- MFRC522 → SPI bus (5 wires: SDA, SCK, MOSI, MISO, RST) + power (2 wires)
- Flow Sensor → 3 wires (Red=5V, Black=GND, Yellow=GPIO26)
- SSR → 2 wires input (Red=GPIO27, Black=GND) + 220V output (white wires)
- Relay → 3 wires input (Red=5V, Black=GND, White=GPIO25) + 2 wires output to solenoid
- Power → DC jack from PSU

#### Main ESP32 Wiring:
- Flow Sensor → 3 wires (Red=5V, Black=GND, Yellow=GPIO34)
- 2CH Relay → 3 wires input (Red=5V, Black=GND, White=GPIO19/IN1, Blue=GPIO18/IN2) + 4 wires output (COM1/COM2 to solenoids, NO1/NO2 to PSU)
- Reset Button → 2 wires (Black=GND, Red=GPIO27)
- Power → DC jack from PSU

---

### ROOM DESIGN (Small Test Mock-ups)

Each room is a **small open-top box** (not a full room) — just enough to show the concept:

- **Size:** 40cm × 30cm × 25cm (W × D × H)
- **Material:** Clear acrylic or white foam board
- **Contents:**
  - Room ESP32 enclosure (mounted on back wall)
  - RFID reader (mounted on front face, user-facing)
  - Flow sensor (in plumbing line, visible through clear wall)
  - Small faucet/valve fixture (to simulate water usage)
  - LED indicator (on enclosure, shows room status)

---

### MAIN CONTROL ZONE (Larger Box)

The main control zone is slightly larger to hold all centralized components:

- **Size:** 60cm × 40cm × 30cm (W × D × H)
- **Material:** Clear acrylic or white foam board
- **Contents:**
  - Main ESP32 enclosure (center)
  - 2CH relay module (near ESP32)
  - 2× solenoid valves (in plumbing line, visible)
  - Flow sensor (between solenoids, visible)
  - 12V PSU + buck converter (inside enclosure)
  - All plumbing connections visible through clear walls

---

### VISUAL STYLE

- **Realistic materials:** Metal for solenoids/PSU, plastic for enclosures, brass for valves/sensors
- **Color coding:** 
  - Green pipes (PPE/PPR)
  - Brass fittings and valves
  - Gray enclosures
  - Blue PCBs (ESP32, relay modules)
  - Red/black wires for power
  - Yellow wires for signals
- **Labels:** Add text labels for key components (ESP32, RFID, Flow Sensor, Solenoid, etc.)
- **Exploded view option:** Show enclosure lid lifted to reveal internal components
- **Cross-section view:** Show one enclosure cutaway to reveal internal layout

---

### RENDERING REQUIREMENTS

1. **Isometric view** — 3/4 angle showing all components and plumbing paths
2. **Top-down view** — Layout of all 4 boxes + plumbing connections
3. **Front view** — Room boxes showing RFID readers and fixtures
4. **Detail view** — Main control zone showing solenoid + flow sensor + relay arrangement
5. **Wire routing** — Show wires going through cable glands into enclosures
6. **Plumbing joints** — Show heat-fused PPR joints (smooth, no clamps)
7. **Scale reference** — Include a 10cm scale bar for size reference

---

### WHAT TO SHOW IN THE RENDER

- [ ] Water tank at the top
- [ ] 1" pipe with reducer fitting
- [ ] Main control zone box with all components visible
- [ ] Dual solenoid valves in series
- [ ] Flow sensor between solenoids
- [ ] T-connector splitting to3 rooms
- [ ] 3 room boxes with RFID readers on front
- [ ] Flow sensors in each room's plumbing
- [ ] Check valves after each room's flow sensor
- [ ] Small faucets/fixtures in each room
- [ ] PPE pipes connecting everything (green)
- [ ] Wire paths from enclosures to components
- [ ] Cable glands on enclosure walls
- [ ] Labels for all major components

---

### DO NOT SHOW

- No full-size rooms — these are small test mock-ups only
- No furniture or decorations — purely technical/engineering model
- No people — just the hardware setup
- No realistic bathroom/kitchen — just labeled boxes

---

Generate this as a detailed, realistic 3D render suitable for a research paper or thesis presentation. The model should be clear enough for someone to understand the complete system layout, component placement, plumbing connections, and electrical wiring at a glance.
