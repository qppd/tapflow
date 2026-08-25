# Setup Guide — Step-by-Step from Zero to Working System

> **Target audience:** College students / researchers building a water monitoring project
> **Estimated time:** 2–3 weeks (part-time)
> **Prerequisites:** Basic electronics knowledge, basic programming (C++ helpful but not required)

---

## Table of Contents

1. [Phase 1: Parts & Tools](#phase-1-parts--tools)
2. [Phase 2: Software Installation](#phase-2-software-installation)
3. [Phase 3: Waterline (Plumbing) Setup](#phase-3-waterline-plumbing-setup)
4. [Phase 4: Hardware Wiring](#phase-4-hardware-wiring)
5. [Phase 5: ESP32 Firmware Upload](#phase-5-esp32-firmware-upload)
6. [Phase 6: Sensor Calibration](#phase-6-sensor-calibration)
7. [Phase 7: Firebase + Next.js Setup](#phase-7-firebase--nextjs-setup)
8. [Phase 8: Testing the Full System](#phase-8-testing-the-full-system)
9. [Phase 9: Enclosure & Deployment](#phase-9-enclosure--deployment)

---

## Phase 1: Parts & Tools

### Required Parts

Check [BOM.md](./bom.md) for complete list with Shopee/Lazada links and prices. Here's a quick summary:

| Category | Item | Qty | Why You Need It |
|----------|------|-----|-----------------|
| **Microcontrollers** | ESP32 38-Pin Dev Board | 4 | 3 for rooms + 1 main |
| | ESP32 38-Pin Expansion Board | 4 | Makes wiring easier (screw terminals) |
| **RFID** | MFRC522 RFID Reader | 3 | 1 per room — tap card to log usage |
| | Mifare Classic 1K Cards | 3+ | User access cards |
| **Sensors** | YF-S201 Flow Sensor | 4 | 3 rooms (leak detection) + 1 main (metering) |
| **Relays** | 2CH Relay with Optocoupler | 1 | Main ESP32 controls 2 solenoid valves |
| | 1-ch Relay 10A | 3 | 1 per room — controls solenoid valve |
| | Fotek 40A SSR | 3 | 1 per room — controls room power (lights/fan) |
| **Valves** | Solenoid Valve 1/2" NC | 5 | 2 main + 3 room |
| | Check Valve 1/2" Brass | 3 | Prevents backflow |
| **Plumbing** | PPE Pipe 1/2" + Fittings | 1 set | Connects everything |
| | PPR Welding Machine | 1 | Heat-fuses PPE joints |
| **Power** | 12V 5A Switching PSU | 4 | 1 per ESP32 |
| | LM2596S Buck Converter | 4 | Steps down 12V → 5V for ESP32 |
| | DC Power Jack Adapter | 4 | Connects PSU to expansion board |
| | USB Micro Cable | 4 | For programming + backup power |
| **Enclosure** | Waterproof ABS Box IP67 | 4 | 1 per ESP32 |

### Required Tools

- Soldering iron + solder (for permanent connections)
- Multimeter (for checking voltage and continuity)
- Wire stripper / cutter
- Small flathead screwdriver (for screw terminals)
- Hot glue gun (for mounting sensors)

### Software You Need

| Software | Purpose | Download |
|----------|---------|----------|
| **Arduino IDE 2.x** | Build and upload ESP32 firmware | [arduino.cc](https://www.arduino.cc/en/software) |
| **Git** | Download project files | [git-scm.com](https://git-scm.com/) |
| **Google Chrome / Firefox** | Access the dashboard | — |
| **Firebase Account** | Cloud database + user login | [firebase.google.com](https://firebase.google.com/) |

> **Note:** No Python needed! The ESP32 talks directly to Firebase via WiFi.

---

## Phase 2: Software Installation

### Step 2.1: Install Arduino IDE

1. Download Arduino IDE 2.x from [arduino.cc](https://www.arduino.cc/en/software)
2. Install and open Arduino IDE
3. **Add ESP32 board support:**
   - Go to **File → Preferences**
   - Find "Additional Board Manager URLs"
   - Paste this URL:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Click **OK**
4. **Install ESP32 boards:**
   - Go to **Tools → Board → Boards Manager**
   - Search **ESP32**
   - Install **esp32 by Espressif Systems**
5. **Install required libraries:**
   - Go to **Tools → Manage Libraries**
   - Search and install:
     - **ArduinoJson** by Benoit Blanchon (v7+)
     - **Firebase ESP32 Client** by mobizt (for main ESP32)

### Step 2.2: Clone the Project

```bash
# Open terminal (Command Prompt on Windows, Terminal on Mac/Linux)
git clone https://github.com/qppd/wmldad.git
cd wmldad
```

---

## Phase 3: Waterline (Plumbing) Setup

> **Do this first before wiring!** It's easier to plan plumbing before connecting electronics.

### Water Flow Structure

```
Water Tank (500-1000L)
    │
    ▼
Fittings → 1" Pipe
    │
    ▼
Reducer Fittings (1" → 1/2")
    │
    ▼
╔═══════════════════════════════════════════════════╗
║  MAIN CONTROL ZONE (inside main enclosure)       ║
║                                                   ║
║  Solenoid Valve 1 ──► Flow Sensor ──► Solenoid 2 ║
╚═══════════════════════════════════════════════════╝
    │
    ▼
T-Connector → 1/2" PPE Pipe to Each Room
    ├──→ Room 1 (Bathroom)
    ├──→ Room 2 (Kitchen)
    └──→ Room 3 (Shower)
```

### Step 3.1: Install Main Plumbing

1. Connect water tank output to **1" pipe** using fittings
2. Use **reducer fittings** to go from 1" to 1/2"
3. Install **Solenoid Valve 1** (12V NC) — first shutoff
4. Install **Flow Sensor** (calibrated) — measures total household usage
5. Install **Solenoid Valve 2** (12V NC) — second shutoff (redundancy)
6. Install **T-connector** to split into3 lines
7. Run **1/2" PPE pipe** to each room

> **Why two solenoid valves?** Safety! If one valve fails stuck open, the other can still shut off water.

### Step 3.2: Install Room Plumbing

For each room:
1. Connect **check valve** (arrow pointing toward fixture)
2. Connect **flow sensor** (for leak detection)
3. Connect to fixture (faucet, shower, bidet)

### Step 3.3: Heat-Fuse PPE Joints

1. Heat up PPR welding machine
2. Heat both pipe and fitting for 5-10 seconds
3. Push together and hold for 30 seconds
4. Let cool before testing

---

## Phase 4: Hardware Wiring

### Room ESP32 Wiring (×3 — same for each room)

Each room ESP32 gets: **RFID + Flow Sensor + SSR + Relay + Solenoid**

```
Room ESP32 38-Pin Expansion Board
┌─────────────────────────────────────────────────────┐
│                                                     │
│  SPI Bus (MFRC522 RFID):                           │
│  [5]  ──────┬── MFRC522 SDA (NSS)                  │
│  [18] ──────┬── MFRC522 SCK                        │
│  [23] ──────┬── MFRC522 MOSI                       │
│  [19] ──────┬── MFRC522 MISO                       │
│  [21] ──────┬── MFRC522 RST                        │
│  3V   ──────┬── MFRC522 3.3V                       │
│  GND  ──────┬── MFRC522 GND                        │
│                                                     │
│  Flow Sensor (leak detection):                     │
│  [26] ──────┬── YF-S201 Signal (Yellow)            │
│  5V   ──────┬── YF-S201 VCC (Red)                  │
│  GND  ──────┬── YF-S201 GND (Black)                │
│                                                     │
│  SSR (Room Power — lights, fan, appliances):       │
│  [27] ──────┬── Fotek 40A SSR Input +              │
│  GND  ──────┬── Fotek 40A SSR Input -              │
│  SSR OUT1 ──┬── 220V line                          │
│  SSR OUT2 ──┬── Appliance 1st wire                 │
│  Appliance 2nd wire ── 220V line                   │
│                                                     │
│  Relay (Solenoid Valve):                           │
│  [25] ──────┬── 1-ch Relay IN                      │
│  5V   ──────┬── Relay VCC                          │
│  GND  ──────┬── Relay GND                          │
│  Relay COM ──┬── Solenoid +                        │
│  Relay NO  ──┬── PSU + (12V)                       │
│  Solenoid - ── PSU - (directly)                    │
│                                                     │
│  Power: 12V jack input (from switching PSU)        │
└─────────────────────────────────────────────────────┘
```

**Connection Summary Table:**

| Component | GPIO Pin | Function |
|-----------|----------|----------|
| MFRC522 SDA | GPIO 5 | RFID SPI data |
| MFRC522 SCK | GPIO 18 | RFID SPI clock |
| MFRC522 MOSI | GPIO 23 | RFID SPI master out |
| MFRC522 MISO | GPIO 19 | RFID SPI master in |
| MFRC522 RST | GPIO 21 | RFID reset |
| Flow Sensor | GPIO 26 | Leak detection pulses |
| Fotek 40A SSR | GPIO 27 | Room power control |
| 1-ch Relay | GPIO 25 | Solenoid valve control |

### Main ESP32 Wiring

Main ESP32 gets: **Flow Sensor + 2CH Relay + 2 Solenoids + Reset Button**

```
Main ESP32 38-Pin Expansion Board
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Flow Sensor (calibrated — accurate metering):     │
│  [34] ──────┬── YF-S201 Signal (Yellow)            │
│  5V   ──────┬── YF-S201 VCC (Red)                  │
│  GND  ──────┬── YF-S201 GND (Black)                │
│                                                     │
│  2CH Relay (Solenoid Valves 1 & 2):                │
│  5V   ──────┬── Relay VCC                           │
│  GND  ──────┬── Relay GND                           │
│  [19] ──────┬── Relay IN1 (Solenoid 1)              │
│  [18] ──────┬── Relay IN2 (Solenoid 2)              │
│  COM1 ──────┬── Solenoid 1 +                        │
│  COM2 ──────┬── Solenoid 2 +                        │
│  NO1  ──────┬── PSU + (12V)                         │
│  NO2  ──────┬── PSU + (12V)                         │
│  Solenoid 1- ── PSU - (directly)                    │
│  Solenoid 2- ── PSU - (directly)                    │
│                                                     │
│  Reset Button (WiFi creds reset):                  │
│  [27] ──────┬── Arcade Button Pin 2                 │
│  GND  ──────┬── Arcade Button Pin 1                 │
│                                                     │
│  WiFi + ESP-NOW RX (receives from room ESP32s)     │
│  [2]  ──────┬── Built-in LED (status)               │
│                                                     │
│  Power: 12V jack input (from switching PSU)        │
└─────────────────────────────────────────────────────┘
```

**Connection Summary Table:**

| Component | GPIO Pin | Function |
|-----------|----------|----------|
| Flow Sensor | GPIO 34 | Calibrated metering |
| 2CH Relay IN1 | GPIO 19 | Solenoid 1 control |
| 2CH Relay IN2 | GPIO 18 | Solenoid 2 control |
| Reset Button | GPIO 27 | Press to reset WiFi creds |
| Built-in LED | GPIO 2 | Status indication |

### Power Wiring

Each ESP32 gets its own power supply:

```
220V AC Outlet
    │
    ▼
12V 5A Switching PSU (S-60-12)
    │
    ├──► DC Jack Adapter (5.5×2.1mm) ──► Expansion Board Jack (12V input)
    │
    └──► (Main only) 12V+ to 2CH Relay NO1/NO2 for solenoids
```

> **Important:** The expansion board accepts 6.5–16V via the DC jack. The PSU outputs 12V, which is perfect. The buck converter on the board steps it down to 5V for the ESP32.

---

## Phase 5: ESP32 Firmware Upload

### Step 5.1: Configure Firmware

1. Open `src/config.example.h` in a text editor
2. Copy it to `src/config.h`
3. Edit `src/config.h` with your settings:

```cpp
// === Device Identity ===
// Room ESP32s:
#define DEVICE_ID        "tapflow-room1"   // or room2, room3
#define ROOM_ID          1                // 1=bathroom, 2=kitchen, 3=shower
#define IS_MAIN          false

// Main ESP32:
// #define DEVICE_ID    "tapflow-main"
// #define IS_MAIN      true

// === WiFi ===
#define WIFI_SSID        "YOUR_WIFI_NAME"
#define WIFI_PASSWORD    "YOUR_WIFI_PASSWORD"

// === Sensor Calibration ===
// UPDATE AFTER BUCKET TEST (Phase 6)!
#define PPL_SENSOR       450              // Pulses Per Liter

// === Pin Assignments ===
// Room ESP32:
#define PIN_SENSOR       26              // Flow sensor signal
#define PIN_SSR          27              // SSR (room power)
#define PIN_RELAY        25              // Relay (solenoid)

// Main ESP32:
// #define PIN_SENSOR    34              // Calibrated flow sensor
// #define PIN_RELAY1    19              // 2CH Relay IN1 (solenoid 1)
// #define PIN_RELAY2    18              // 2CH Relay IN2 (solenoid 2)
// #define PIN_RESET     27              // Reset button

// === ESP-NOW Peer ===
// Main ESP32's MAC address (get from Serial Monitor)
#define MAIN_ESP_MAC     {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}

// === Firebase (main ESP32 only) ===
#define FIREBASE_API_KEY "YOUR_FIREBASE_API_KEY"
#define FIREBASE_DATABASE_URL "https://your-project.firebaseio.com"
```

### Step 5.2: Upload Firmware

1. Connect ESP32 to computer via USB cable
2. In Arduino IDE:
   - **Tools → Board → ESP32 Arduino → ESP32 Dev Module**
   - **Tools → Port → COMx** (check Device Manager)
3. Click **Sketch → Verify/Compile** (Ctrl+R)
4. Click **Sketch → Upload** (Ctrl+U)

**If upload fails:**
1. Hold **BOOT** button on ESP32
2. Press **EN** (reset) while holding BOOT
3. Release EN, then release BOOT
4. Click Upload again

### Step 5.3: Get MAC Address

1. Upload the firmware
2. Open **Tools → Serial Monitor** (Ctrl+Shift+M)
3. Set baud rate to **921600**
4. Look for MAC address in the output
5. Copy it to `config.h` on other ESP32s

---

## Phase 6: Sensor Calibration

> **Only calibrate the main flow sensor!** Room flow sensors are for leak detection only.

### Bucket Test Procedure

1. **Get a 5L container** (graduated measuring cup works)
2. **Connect** the main flow sensor in-line with a faucet
3. **Run water** at medium flow into the container
4. **Collect exactly 5 liters**
5. **Read** the pulse count from Serial Monitor
6. **Calculate:**
   ```
   PPL = Total Pulses ÷ 5
   ```
7. **Update** `PPL_SENSOR` in `config.h`
8. **Re-upload** firmware
9. **Repeat** if accuracy is off

---

## Phase 7: Firebase + Next.js Setup

### Step 7.1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Create a project** (e.g., `tapflow-water-monitor`)
3. Enable **Realtime Database**:
   - Go to Build → Realtime Database → Create Database
   - Start in **test mode**
4. Enable **Authentication**:
   - Go to Build → Authentication → Sign-in method
   - Enable **Email/Password** and **Google**
5. Get your credentials:
   - Go to Project Settings → General
   - Copy **Web API Key** and **Database URL**
6. Add to main ESP32's `config.h`

### Step 7.2: Deploy Next.js Dashboard

```bash
# Clone the web dashboard
git clone https://github.com/qppd/wmldad-web.git
cd wmldad-web

# Install dependencies
npm install

# Run locally (for testing)
npm run dev
# Open http://localhost:3000

# Deploy to Vercel (for production)
npx vercel deploy
```

---

## Phase 8: Testing the Full System

### Test 1: Room ESP32 Powers On
1. Plug in 12V PSU to room ESP32
2. LED should blink
3. Open Serial Monitor (921600 baud)
4. Should see JSON status message

### Test 2: RFID Works
1. Tap a Mifare card on the RFID reader
2. Serial Monitor should show card ID
3. LED should change pattern

### Test 3: Flow Sensor Detects Water
1. Turn on faucet
2. Serial Monitor should show increasing pulse count
3. Flow rate should appear

### Test 4: Main ESP32 Receives Data
1. Power on main ESP32
2. All 3 room ESP32s should send data via ESP-NOW
3. Main ESP32 Serial Monitor shows aggregated data

### Test 5: Solenoid Valves Work
1. From Serial Monitor, send command to open solenoid
2. Should hear click from relay
3. Water should flow
4. Send close command → water stops

### Test 6: Firebase Connection
1. Main ESP32 connects to WiFi automatically
2. Data appears in Firebase Console
3. Next.js dashboard shows live data

### Test 7: Leak Detection
1. Simulate leak (small flow without RFID tap)
2. Room ESP32 sends leak alert via ESP-NOW
3. Main ESP32 receives alert
4. Dashboard shows leak warning

---

## Phase 9: Enclosure & Deployment

### Step 9.1: Permanent Wiring

1. **Solder** connections to perf board (instead of breadboard)
2. **Mount** expansion board inside IP67 enclosure
3. **Use cable glands** for waterproof cable entry
4. **Label** all wires (room number, function)
5. **Secure** wires with cable ties

### Step 9.2: Mount Enclosures

1. Mount each room enclosure near the room's plumbing
2. Mount main enclosure near the main waterline
3. Ensure cables can reach all components
4. Use double-sided tape or screws

### Step 9.3: Final Testing

1. Turn on water supply
2. Check for leaks at all connections
3. Test RFID in each room
4. Verify flow readings on dashboard
5. Test solenoid shutoff from dashboard
6. Leave system running for 24 hours

---

## Quick Reference

### Arduino IDE Shortcuts

| Action | Shortcut |
|--------|----------|
| Verify/Compile | Ctrl+R |
| Upload | Ctrl+U |
| Serial Monitor | Ctrl+Shift+M |
| Save | Ctrl+S |

### Serial Monitor Settings

- **Baud Rate:** 921600
- **Line Ending:** Newline

### GPIO Pin Reference

| ESP32 | Room Functions | Main Functions |
|-------|----------------|----------------|
| GPIO 2 | Built-in LED | Built-in LED |
| GPIO 5 | MFRC522 SDA | — |
| GPIO 18 | MFRC522 SCK | 2CH Relay IN2 |
| GPIO 19 | MFRC522 MISO | 2CH Relay IN1 |
| GPIO 21 | MFRC522 RST | — |
| GPIO 23 | MFRC522 MOSI | — |
| GPIO 25 | 1-ch Relay IN | — |
| GPIO 26 | Flow Sensor | — |
| GPIO 27 | Fotek SSR IN | Reset Button |
| GPIO 34 | — | Flow Sensor (calibrated) |

---

## Wiring Resources

### Interactive Wiring Diagram (Cirkit Designer)
**🔗 [View Interactive Wiring Diagram](https://app.cirkitdesigner.com/project/b0b4579e-313d-4faa-9cd1-f955daa204a5)**

### Static Wiring Diagram (PNG)
![Wiring Diagram](../wiring/smartrooms.png)

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| ESP32 won't power on | Wrong power cable | Use **data cable**, not charge-only |
| No Serial output | Wrong baud rate | Set to **921600** in Serial Monitor |
| Upload fails | ESP32 not in flash mode | Hold BOOT, press EN, release both |
| RFID not reading | Wrong wiring | Check SPI pins: SDA→5, SCK→18, MOSI→23, MISO→19 |
| Flow sensor no pulses | Wrong GPIO | Signal wire must go to **GPIO 26** (room) or **GPIO 34** (main) |
| Solenoid not opening | Relay not firing | Check relay IN pin and 12V PSU connection |
| WiFi won't connect | Wrong credentials | Double-check SSID and password in config.h |
| Firebase not receiving | API key wrong | Verify FIREBASE_API_KEY in config.h |

---

## Need Help?

1. Check [troubleshooting.md](./troubleshooting.md) for detailed fixes
2. Check [esp32-firmware-complete-guide.md](./esp32-firmware-complete-guide.md) for firmware details
3. Open a GitHub Issue with:
   - Serial Monitor output (last 50 lines)
   - Your `config.h` (remove passwords!)
   - Photo of your wiring
