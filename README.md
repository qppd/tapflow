# TapFlow — RFID-Based Automatic Water and Electrical Line Control with Water Flow Anomaly Detection

> **A Research Project** — Smart water monitoring system that detects leaks and per-room consumption using ESP32 mesh (ESP-NOW), RFID usage tracking, centralized solenoid valve control, and a Next.js web dashboard on Vercel with Firebase Realtime Database + Authentication.

---

## System Overview

```
Room 1 ESP32 ──┐
Room 2 ESP32 ──┼── ESP-NOW ──▶ Main ESP32 ──WiFi──▶ Firebase RTDB
Room 3 ESP32 ──┘            (centralized)              │
     │                      ├── 2× Relay + Solenoid    ▼
     ├── RFID Reader        ├── Calibrated Flow Sensor  Next.js on Vercel
     └── Flow Sensor        │   (GPIO 34)               (Web Dashboard)
       (leak detection)     └── WiFi to Firebase
```

- **3 Room ESP32s** — each has RFID reader (MFRC522) and flow sensor (YF-S201, uncalibrated, leak detection only). Sends readings via ESP-NOW.
- **1 Main ESP32 (centralized)** — receives ESP-NOW data from all rooms, controls 2 solenoid valves via relays, reads calibrated flow sensor (GPIO 34), pushes to Firebase RTDB via WiFi using [mobizt Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client). Placed before the rooms for centralized control.
- **Firebase** — Realtime Database (data storage) + Authentication (user login)
- **Next.js on Vercel** — web dashboard, real-time monitoring, leak alerts, usage logging per person


---

## Developer Quick-Start: Step-by-Step Process

Follow these steps **in order**. Each step links to the detailed guide.

### Phase 1: Prepare (Do First)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 1 | **Buy parts** — Order from BOM (Makerlab Electronics on Shopee/Lazada) | [BOM.md](./docs/bom.md) | 1–2 weeks shipping |
| 2 | **Clone project repo** | [setup.md](./docs/setup.md) | 5 min |

> ⚠️ **Do Step 1–2 in parallel.** Hardware shipping takes longest.

---

### Phase 2: Hardware Assembly

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 3 | **Wire 3× Room ESP32** — Each gets MFRC522 RFID + YF-S201 flow sensor (leak detection) | [block-diagram.md](./docs/block-diagram.md) | 1 hr |
| 4 | **Wire Main ESP32** — 2× relay (solenoid valves) + calibrated flow sensor + WiFi to Firebase | [block-diagram.md](./docs/block-diagram.md) | 1 hr |
| 5 | **Plumbing** — Install sensors in-line with check valves (arrow = flow direction) | [setup.md](./docs/setup.md) | 2–4 hrs |
| 6 | **Enclosure** — Mount ESP32s in IP67 boxes with cable glands | [block-diagram.md](./docs/block-diagram.md) | 1 hr |

---

### Phase 3: ESP32 Firmware

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 7 | **Install Arduino IDE 2.x** (Windows/macOS/Linux) | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 15 min |
| 8 | **Add ESP32 board support** — Board Manager URL + install `esp32 by Espressif Systems` | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 10 min |
| 9 | **Install libraries** — `ArduinoJson` (JSON) + `MFRC522` (RFID) + `Firebase-ESP-Client` by mobizt + ESP-NOW (built-in) | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 10 | **Configure `config.h`** — Device ID, room number, sensor pin, PPL calibration, peer MAC | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 10 min |
| 11 | **Upload room firmware** to all 3 room ESP32s | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 12 | **Upload main firmware** to main ESP32 | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 13 | **Verify** — Serial Monitor (921600): room ESP32s send data, main ESP32 receives via ESP-NOW | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |

---

### Phase 4: Sensor Calibration

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 14 | **Bucket test each sensor** — 5L measured, calculate PPL, update `config.h` | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md#sensor-calibration-bucket-test) | 30 min/sensor |

> 🎯 Target: < 3% error per sensor. Uncalibrated sensors = false leaks / missed leaks.

---

### Phase 5: Web Dashboard (Next.js + Firebase)

| Step | Action | Guide | Est. Time |
|------|--------|-------|-----------|
| 15 | **Create Firebase project** — Enable RTDB + Authentication | [setup.md](./docs/setup.md) | 10 min |
| 16 | **Configure Main ESP32** — Add Firebase API key + DB URL to `config.h` | [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | 5 min |
| 17 | **Deploy Next.js app** — `vercel deploy`, connect to Firebase | [setup.md](./docs/setup.md) | 10 min |
| 18 | **Power on Main ESP32** — Connects to WiFi → Firebase automatically | — | 2 min |

---

## Essential Guides Only (Bookmark These)

| Guide | Purpose |
|-------|---------|
| [BOM.md](./docs/bom.md) | Parts list with Shopee links, prices |
| [block-diagram.md](./docs/block-diagram.md) | Pinout, wiring, ESP-NOW topology, enclosure layout |
| [setup.md](./docs/setup.md) | Full phased walkthrough (reference) |
| [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | **Complete ESP32 firmware** (room + main, ESP-NOW, ArduinoJson, relay control) |
| [troubleshooting.md](./docs/troubleshooting.md) | Serial commands, LED codes, common fixes |
| [anomaly-detection-guide.md](./docs/anomaly-detection-guide.md) | **Anomaly detection** — algorithms, ESP32 modules, Firebase structure |
| [leak-detection-advanced-guide.md](./docs/leak-detection-advanced-guide.md) | **Leak detection** — 6 rules + mass balance + pulse analysis |
| [module-integration-guide.md](./docs/module-integration-guide.md) | **Module integration** — how all ESP32 modules wire together |
| [web-dashboard-alerts-guide.md](./docs/web-dashboard-alerts-guide.md) | **Web dashboard** — Next.js UI for anomaly/leak detection |

---

### Phase 6: Anomaly + Leak Detection System

| Step | Action | Guide | Est. Time |
|------|--------|-------|----------|
| 19 | **Implement anomaly detection** — Rate-of-change, baseline deviation, burst detection on room ESP32s | [anomaly-detection-guide.md](./docs/anomaly-detection-guide.md) | 2 hrs |
| 20 | **Implement leak detection** — 6 core rules + mass balance + post-shutoff verification | [leak-detection-advanced-guide.md](./docs/leak-detection-advanced-guide.md) | 2 hrs |
| 21 | **Integrate modules** — Wire detection modules into ESP32 main loops, ESP-NOW payload, Firebase push | [module-integration-guide.md](./docs/module-integration-guide.md) | 2 hrs |
| 22 | **Build dashboard alerts** — Real-time alert feed, severity badges, threshold config, trend charts | [web-dashboard-alerts-guide.md](./docs/web-dashboard-alerts-guide.md) | 3 hrs |
| 23 | **Validate** — Test all 6 leak rules, anomaly detection, false positive reduction, Firebase sync | All detection guides | 2 hrs |

> **Detection order:** anomaly-detection-guide → leak-detection-advanced-guide → module-integration-guide → web-dashboard-alerts-guide

---

## Hardware Summary

| Component | Qty | Key Spec |
|-----------|-----|----------|
| ESP32 38-pin Dev Module | 4 | 3 room + 1 main, CP2102/CH340 USB-UART |
| ESP32 Expansion Board | 4 | Screw terminals for each ESP32 |
| MFRC522 RFID Reader | 3 | SPI, 1 per room — usage tracking |
| RFID Cards/Tags | 3+ | Mifare Classic 1K — one per user |
| YF-S201 Flow Sensor | 4 | 3 rooms (leak detection, uncalibrated) + 1 main (calibrated) |
| 2CH Relay with Optocoupler | 1 | Main ESP32 controls 2 solenoids |
| 1-ch Relay 10A | 3 | 1 per room — controls solenoid valve |
| Fotek 40A SSR | 3 | 1 per room — controls room power (lights/fan) |
| Solenoid Valve 1/2" | 5 | NC (normally closed), 12V DC, 2 main + 3 room |
| Check Valve 1/2" | 3 | Brass, prevent backflow |
| PPE Pipe + Fittings | 1 set | 1/2" Polypropylene, heat-fused joints |
| 12V 5A PSU + LM2596S buck | 4 | 220V → 12V → 5V, 1 per ESP32 |
| DC Power Jack Adapter | 4 | 5.5×2.1mm, connects PSU to expansion board |
| IP67 ABS Enclosure | 4 | 175×125×75mm, one per ESP32 |

---

## 3D Models

Fusion 360 source files and fixture renders are in the [`models/`](./models/) folder:

| File | Description |
|------|-------------|
| [`TapFlow.f3d`](./models/TapFlow.f3d) | Fusion 360 source file (editable) |
| [`tapflow_view_1.png`](./models/tapflow_view_1.png) | Fixture view 1 |
| [`tapflow_view_2.png`](./models/tapflow_view_2.png) | Fixture view 2 |
| [`tapflow_view_3.png`](./models/tapflow_view_3.png) | Fixture view 3 |
| [`tapflow_view_4.png`](./models/tapflow_view_4.png) | Fixture view 4 |
| [`tapflow_view_5.png`](./models/tapflow_view_5.png) | Fixture view 5 |
| [`tapflow_view_6.png`](./models/tapflow_view_6.png) | Fixture view 6 |
| [`tapflow_view_7.png`](./models/tapflow_view_7.png) | Fixture view 7 |
| [`tapflow_view_8.png`](./models/tapflow_view_8.png) | Fixture view 8 |

> Open `TapFlow.f3d` in Fusion 360 to modify the enclosure design, add mounting holes, or adjust dimensions for different components.

---

## Quick Verification Checklist

After each phase, verify:

- [ ] **Phase 1:** All parts received, repo cloned
- [ ] **Phase 2:** All 3 room ESP32s powered, RFID reads cards, sensors pulse; main ESP32 triggers solenoids via relay
- [ ] **Phase 3:** ESP-NOW link working — room data + RFID tags appear on main ESP32 Serial Monitor
- [ ] **Phase 4:** 5L bucket test → < 3% error on each sensor
- [ ] **Phase 5:** Main ESP32 connected to WiFi, data visible in Firebase RTDB, Next.js dashboard shows live data
- [ ] **Phase 6:** All 6 leak rules trigger correctly, anomaly detection working, dashboard shows real-time alerts

---

## License

MIT

## Author

[qppd](https://github.com/qppd) — Quezon Province, Philippines