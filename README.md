# WMLDAD — Smart Water Monitoring System

> **A Research Project** — Smart Water Monitoring System that detects leaks and per-room consumption using ESP32 mesh (ESP-NOW), RFID usage tracking, SSR solenoid valve control, and a Next.js web dashboard on Vercel with Firebase Realtime Database + Authentication.

---

## System Overview

```
Room 1 ESP32 ──┐
Room 2 ESP32 ──┼── ESP-NOW ──▶ Main ESP32 ──WiFi──▶ Firebase RTDB
Room 3 ESP32 ──┘                                      │
     │                                                ▼
     ├── RFID Reader (MFRC522) — tap card      Next.js on Vercel
     ├── Flow Sensor (YF-S201) — measure       (Web Dashboard)
     └── SSR + Solenoid Valve — shutoff
```

- **3 Room ESP32s** — each has RFID reader (MFRC522), flow sensor (YF-S201), Fotek 40A SSR + solenoid valve. Sends readings via ESP-NOW.
- **1 Main ESP32** — receives ESP-NOW data from all rooms, pushes to Firebase RTDB via WiFi using [mobizt Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client). Also receives commands/callbacks from Firebase.
- **Firebase** — Realtime Database (data storage) + Authentication (user login)
- **Next.js on Vercel** — web dashboard, real-time monitoring, leak alerts, usage logging per person

> **No Raspberry Pi needed!** Main ESP32 talks to Firebase directly via WiFi.

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
| 3 | **Wire 3× Room ESP32** — Each gets MFRC522 RFID, YF-S201 flow sensor, Fotek 40A SSR + solenoid valve | [block-diagram.md](./docs/block-diagram.md) | 2 hrs |
| 4 | **Wire Main ESP32** — Power only (no SSR — each room handles its own, WiFi connects to Firebase) | [block-diagram.md](./docs/block-diagram.md) | 30 min |
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
| [esp32-firmware-complete-guide.md](./docs/esp32-firmware-complete-guide.md) | **Complete ESP32 firmware** (room + main, ESP-NOW, ArduinoJson, SSR control) |
| [troubleshooting.md](./docs/troubleshooting.md) | Serial commands, LED codes, common fixes |

---

## Hardware Summary

| Component | Qty | Key Spec |
|-----------|-----|----------|
| ESP32 38-pin Dev Module | 4 | 3 room + 1 main, CP2102/CH340 USB-UART |
| ESP32 Expansion Board | 4 | Screw terminals for each ESP32 |
| MFRC522 RFID Reader | 3 | SPI, 1 per room — usage tracking |
| RFID Cards/Tags | 3+ | Mifare Classic 1K — one per user |
| YF-S201 Flow Sensor | 3 | 1/2" NPT, Hall effect, 1 per room |
| Fotek 40A SSR | 3 | Solid-state relay, 1 per room |
| Solenoid Valve 1/2" | 3 | NC (normally closed), 12V DC, 1 per room |
| Check Valve 1/2" | 3 | Brass, prevent backflow |
| PPE Pipe + Fittings | 1 set | 1/2" Polypropylene, heat-fused joints |
| 12V 5A PSU + LM2596S buck | 1 | 220V → 12V → 5V |
| IP67 ABS Enclosure | 4 | 175×125×75mm, one per ESP32 |
| Perf board 20×80mm | 4 | Soldered connections |

---

## Quick Verification Checklist

After each phase, verify:

- [ ] **Phase 1:** All parts received, repo cloned
- [ ] **Phase 2:** All 3 room ESP32s powered, RFID reads cards, sensors pulse, SSR triggers solenoid
- [ ] **Phase 3:** ESP-NOW link working — room data + RFID tags appear on main ESP32 Serial Monitor
- [ ] **Phase 4:** 5L bucket test → < 3% error on each sensor
- [ ] **Phase 5:** Main ESP32 connected to WiFi, data visible in Firebase RTDB, Next.js dashboard shows live data

---

## License

MIT

## Author

[qppd](https://github.com/qppd) — Quezon Province, Philippines