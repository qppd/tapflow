# Setup Guide — Step-by-Step from Zero to Working System

> **Target audience:** Students / researchers building a water monitoring project  
> **Estimated time:** 2–3 weeks (part-time)  
> **Prerequisites:** Basic electronics, basic programming

---

## Table of Contents

1. [Phase 1: Parts & Tools](#phase-1-parts--tools)
2. [Phase 2: Software Installation](#phase-2-software-installation)
3. [Phase 3: Hardware Assembly](#phase-3-hardware-assembly)
4. [Phase 4: ESP32 Firmware Upload](#phase-4-esp32-firmware-upload)
5. [Phase 5: Sensor Calibration](#phase-5-sensor-calibration)
6. [Phase 6: Firebase + Next.js Setup](#phase-6-firebase--nextjs-setup)
7. [Phase 7: Testing the Full System](#phase-7-testing-the-full-system)
8. [Phase 8: Enclosure & Deployment](#phase-8-enclosure--deployment)

---

## Phase 1: Parts & Tools

### Required Parts

Check [BOM.md](./bom.md) for complete list with Shopee/Lazada links. Minimum essentials:

| Item | Qty | Estimated Cost (₱) |
|------|-----|-------------------|
| ESP32 38-pin Dev Board | 4 | ₱1,800 |
| ESP32 38-pin Expansion Board | 4 | ₱720 |
| YF-S201 Flow Sensor | 3 | ₱540 |
| SSR Relay Module | 1 | ₱100 |
| Check Valve 1/2" | 3 | ₱360 |
| Perf board + soldering | 4 sets | ₱460 |
| USB Micro Data Cable | 1 | ₱100 |
| **Minimum Total** | | **~₱4,080** |

### Required Tools

- Soldering iron + solder (for permanent setup)
- Multimeter (for checking connections)
- Wire stripper / cutter
- Small flathead screwdriver
- Hot glue gun (for mounting sensors)

### Software You Need

| Software | Purpose | Download |
|----------|---------|----------|
| **Arduino IDE 2.x** | ESP32 build, upload, Serial Monitor | [arduino.cc](https://www.arduino.cc/en/software) |
| **Python 3.11+** | Backend | [python.org](https://www.python.org/) |
| **Git** | Version control | [git-scm.com](https://git-scm.com/) |
| **Google Chrome / Firefox** | Dashboard access | — |
| **Firebase Account** | Cloud database + auth | [firebase.google.com](https://firebase.google.com/) |

---

## Phase 2: Software Installation

### Step 2.1: Install Arduino IDE

1. Download Arduino IDE 2.x from [arduino.cc](https://www.arduino.cc/en/software)
2. Install and open Arduino IDE
3. Add ESP32 board support:
   - File -> Preferences -> Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools -> Board -> Boards Manager -> search **ESP32** -> install **ESP32 Arduino**
4. Install required libraries via Library Manager (Tools -> Manage Libraries):
   - `ArduinoJson` by Benoit Blanchon (v7+)

> **Note:** No Firebase-ESP-Client needed — we use plain USB Serial with ArduinoJson.

### Step 2.2: Install Python

1. Download Python 3.11+ from python.org
2. **Important:** Check **"Add Python to PATH"** during installation
3. Verify:
   ```bash
   python --version
   # Should show: Python 3.11.x or higher
   ```

### Step 2.3: Clone the Project

```bash
# Open terminal (Command Prompt or Git Bash)
git clone https://github.com/qppd/wmldad.git
cd wmldad
```



## Phase 3: Hardware Assembly

### Step 3.1: Prepare the Expansion Board

The ESP32 expansion board makes wiring much easier. It provides:
- Labeled screw terminals for each GPIO pin
- Power rails (5V and 3.3V)
- Reset and BOOT buttons

### Step 3.2: Wire Room ESP32s (×3)

Each room ESP32 gets 1 YF-S201 flow sensor on GPIO 26:

```
YF-S201 Sensor          Room ESP32 Expansion Board
┌──────────────┐
│  Red   ──────┼────── 5V (VIN pin)
│  Black ──────┼────── GND
│  Yellow ─────┼────── GPIO 26
└──────────────┘
```

**Note:** The YF-S201 Hall-effect sensor outputs a digital pulse signal. No external pull-up resistor or capacitor needed — connect signal wire directly to GPIO.

| Room ESP32 | Room | Flow Sensor | GPIO |
|------------|------|-------------|------|
| #1 | Bathroom | YF-S201 | GPIO 26 |
| #2 | Kitchen | YF-S201 | GPIO 26 |
| #3 | Shower | YF-S201 | GPIO 26 |

### Step 3.3: Wire MFRC522 RFID Reader (per room)

Each room ESP32 gets an MFRC522 RFID reader via SPI:

```
MFRC522 RFID             Room ESP32 Expansion Board
┌──────────────┐
│  SDA  ──────┼────── GPIO 5
│  SCK  ──────┼────── GPIO 18
│  MOSI ──────┼────── GPIO 23
│  MISO ──────┼────── GPIO 19
│  RST  ──────┼────── GPIO 27
│  3.3V ──────┼────── 3.3V
│  GND  ──────┼────── GND
└──────────────┘
```

### Step 3.4: Wire Fotek 40A SSR (per room — room power)

```
Fotek 40A SSR            Room ESP32 Expansion Board
┌──────────────┐
│  CTRL ──────┼────── GPIO 25
│  VCC  ──────┼────── 5V
│  GND  ──────┼────── GND
│  OUT+ ──────┼────── Room electrical line (live)
│  OUT- ──────┼────── Neutral
└──────────────┘
```
> SSR controls room power — HIGH when RFID tap valid, LOW when session ends.

### Step 3.5: Wire 1-ch Relay + Solenoid Valve (per room — solenoid control)

```
1-ch Relay 10A           Room ESP32 Expansion Board
┌──────────────┐
│  IN   ──────┼────── GPIO 13
│  VCC  ──────┼────── 5V
│  GND  ──────┼────── GND
│  OUT+ ──────┼────── Solenoid Valve 12V NC (+)
│  OUT- ──────┼────── 12V PSU (-)
└──────────────┘

Solenoid Valve 12V NC:
│  Wire (+) ──┼────── Relay OUT+
│  Wire (-) ──┼────── 12V PSU (-)
```
> **Note:** Solenoid valves are NC (normally closed). Relay HIGH = water flows. Relay LOW = shutoff.
> 
> **Smart Solenoid Control:** The solenoid relay is ONLY energized when the flow sensor detects water usage. When no flow for N seconds, relay turns OFF (solenoid closes) to prevent overheating. Turns back ON when flow resumes.
>
> **Session Flow:** RFID tap valid → SSR ON + Solenoid ON → Flow detected → Solenoid stays ON → No flow for N sec → Solenoid OFF (heating protection) → Flow resumes → Solenoid ON → Session timeout → SSR OFF.

### Step 3.5: Wire Main ESP32

Main ESP32 connects to WiFi and Firebase directly (no SSR — each room handles its own):

```
USB Micro-B ──────────── USB Port (power + debug)
```

### Step 3.6: Plumbing Setup

For each room:
1. Install flow sensor in-line with **PPE pipe** (heat-fused joints)
2. Add check valve after sensor (arrow = flow direction)
3. Connect to fixture (bidet, kitchen faucet, shower)

**For testing:**
- Fill a 20L container with water
- Connect pump or gravity-feed through each room sensor
- Open/close valves to simulate usage

---

## Phase 4: ESP32 Firmware Upload

### Step 4.1: Configure Firmware

1. Open `src/config.example.h` in any text editor
2. Create `src/config.h` (copy the example)
3. Fill in your credentials:

```cpp
// === Device Identity ===
#define DEVICE_ID        "wmldad-room1"   // or wmldad-room2, wmldad-room3, wmldad-main
#define FIRMWARE_VERSION "v4.0.0-espnow"
#define ROOM_ID          1                // 1=bathroom, 2=kitchen, 3=shower (room ESP32s only)

// === WiFi (for ESP-NOW + OTA + NTP) ===
#define WIFI_SSID        "YOUR_WIFI_NAME"
#define WIFI_PASSWORD    "YOUR_WIFI_PASSWORD"

// === Sensor Calibration (PPL = Pulses Per Liter) ===
// UPDATE AFTER BUCKET TEST!
#define PPL_SENSOR       450

// === Sensor Pin ===
#define PIN_SENSOR       26              // All room ESP32s use GPIO 26

// === Main ESP32 Peer (for ESP-NOW) ===
// Update with your main ESP32's MAC address
#define MAIN_ESP_MAC     {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}

// === SSR Relay Pin (per room — controls solenoid) ===
#define PIN_SSR          25            // HIGH = solenoid ON (water flows), LOW = shutoff

// === Timing ===
#define SEND_INTERVAL_MS 5000            // ESP-NOW send every 5 sec
```

### Step 4.2: Upload Firmware

1. Connect ESP32 via USB cable
2. In Arduino IDE, select your board:
   - **Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module**
3. Select the correct port:
   - **Tools -> Port -> COMx** (check Windows Device Manager for the COM port)
4. Click **Sketch -> Verify/Compile** (Ctrl+R) to check for errors
5. Click **Sketch -> Upload** (Ctrl+U) to flash the ESP32
6. If upload fails:
   - Hold **BOOT** button on ESP32
   - Press **EN** (reset) while holding BOOT
   - Release EN, then release BOOT
   - Click Upload again

### Step 4.3: Monitor Serial Output

1. Open **Tools -> Serial Monitor** (Ctrl+Shift+M)
2. Set baud rate to **921600** (bottom-right of Serial Monitor window)
3. You should see:
   ```
   // Room ESP32 Serial Monitor:
   {"status":"ready","device_id":"wmldad-room1","firmware":"v4.0.0-espnow"}
   {"room_id":1,"ts":123456,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456,"leak_alert":false}
   
   // Main ESP32 Serial Monitor (receives from all rooms):
   {"status":"ready","device_id":"wmldad-main","firmware":"v4.0.0-espnow"}
   {"rooms":[{"room_id":1,"flow_rate_lpm":2.34,"volume_ml":456},{"room_id":2,"flow_rate_lpm":0.0,"volume_ml":0},{"room_id":3,"flow_rate_lpm":1.12,"volume_ml":210}]}
   ```

---

## Phase 5: Sensor Calibration

> Detailed procedure: [Calibration Guide](./esp32-firmware-complete-guide.md#sensor-calibration-bucket-test)

### Quick Calibration (Bucket Test)

1. **Prepare:** Get a 5L graduated container
2. **Connect:** Run water from faucet through the inlet sensor into the container
3. **Open:** Turn on faucet at medium flow
4. **Collect:** Exactly 5 liters
5. **Read:** Get pulse count from Serial Monitor (watch `pulses` field)
6. **Calculate:**
   ```
   Actual PPL = Total Pulse Count ÷ 5
   ```
7. **Update:** Change `PPL_SENSOR` in `config.h`
8. **Repeat** for each sensor (move sensor to each fixture line)

---

## Phase 6: Firebase + Next.js Setup

### Step 6.1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project (e.g., `wmldad-water-monitor`)
3. Enable **Realtime Database** → Create database → Start in test mode
4. Enable **Authentication** → Sign-in method → Enable Email/Password + Google
5. Go to Project Settings → General → Copy **Web API Key** and **Database URL**
6. Add these to Main ESP32's `config.h` (see Step 6.3)

### Step 6.2: Configure Main ESP32 for Firebase

In the main ESP32's `config.h`, add:

```cpp
#define FIREBASE_API_KEY "YOUR_FIREBASE_API_KEY"
#define FIREBASE_DATABASE_URL "https://your-project.firebaseio.com"
```

The main ESP32 uses [mobizt Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) to connect to Firebase via WiFi. Install via Arduino Library Manager: search **Firebase ESP32 Client** by **mobizt**.

### Step 6.3: Deploy Next.js App

```bash
# On your computer:
git clone https://github.com/qppd/wmldad-web.git
cd wmldad-web
npm install
npm run dev  # Test locally at localhost:3000

# Deploy to Vercel:
npx vercel deploy
```

The Next.js app connects to Firebase RTDB for real-time data and Firebase Auth for user login.

### Step 6.4: Configure Firebase for Next.js

Create `lib/firebase.ts` in the Next.js project:

```typescript
import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
export const db = getDatabase(app);
export const auth = getAuth(app);
```

> See [system-architecture.md](./system-architecture.md) and [stacks.md](./stacks.md) for architecture details.

---

## Phase 7: Testing the Full System

### Test 1: ESP32 → USB Serial
1. Turn water on through a fixture
2. Open Serial Monitor (921600 baud) on your computer
3. JSON data should stream every 5 seconds
4. Verify flow rate changes when you open/close faucets

### Test 2: ESP32 → Firebase → Next.js Dashboard
1. Power on Main ESP32 — connects to WiFi + Firebase automatically
2. Open the Next.js dashboard on Vercel (or localhost:3000)
3. Log in via Firebase Auth
4. Should see live room data from Firebase RTDB
5. Check Main ESP32 Serial Monitor for Firebase connection status

### Test 3: Leak Detection
1. Simulate a **minor leak**: partially open a valve to produce 0.1–0.5 L/min
2. Wait 30+ seconds
3. Check if an alert appears on the dashboard
4. Check logs for detection

### Test 4: Command Flow
1. From dashboard, send a command (e.g., "calibrate")
2. ESP32 should respond via Serial
3. Check Serial Monitor for acknowledgment

### Test 5: Offline Mode
1. Disconnect WiFi on Main ESP32
2. ESP32 should continue logging to SPIFFS (LED patterns show local alerts)
3. Reconnect USB → data should appear on dashboard

---

## Phase 8: Enclosure & Deployment

### Permanent Wiring
1. Solder components to perf board (instead of breadboard)
2. Mount expansion board inside ABS enclosure
3. Use cable glands for water sensor cables
4. Label all wires

### Final Calibration
1. Install sensors in actual plumbing
2. Perform bucket test on each sensor
3. Update PPL values in `config.h`, re-upload firmware
4. Verify total consumption matches water bill

### Monitoring
1. Set up dashboard as home page on touchscreen
2. Configure in-app alerts (via dashboard /api/alerts)
3. Set up periodic health checks
4. Check system health periodically

---

## Quick Reference: Common Commands

```bash
# Arduino IDE: Verify/Compile
#   Sketch -> Verify/Compile  (Ctrl+R)

# Arduino IDE: Upload to ESP32
#   Sketch -> Upload  (Ctrl+U)

# Arduino IDE: Serial Monitor
#   Tools -> Serial Monitor  (Ctrl+Shift+M)  @ 921600 baud

# Main ESP32: Connects to WiFi + Firebase automatically on boot
# No bridge needed — ESP32 talks to Firebase directly via mobizt SDK

# Next.js: Run locally
cd wmldad-web
npm run dev
```

---

## Wiring Resources

### Interactive Wiring Diagram (Cirkit Designer)
**🔗 [View Interactive Wiring Diagram](https://app.cirkitdesigner.com/project/b0b4579e-313d-4faa-9cd1-f955daa204a5)**

### Static Wiring Diagram (PNG)
![Wiring Diagram](../wiring/wmldad.png)

### Wiring Source File
