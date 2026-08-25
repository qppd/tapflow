# System Architecture

## Overview

Smart water monitoring system with **per-room leak detection** using **ESP32 mesh (ESP-NOW) → Main ESP32 → WiFi → Firebase → Next.js on Vercel**.

3 room ESP32s each have an **MFRC522 RFID reader** (usage tracking) and a **YF-S201 flow sensor** (leak detection, uncalibrated). Room ESP32s transmit readings wirelessly via **ESP-NOW** to a centralized main ESP32. The main ESP32 controls **2 solenoid valves via relays**, reads a **calibrated flow sensor** (accurate metering), and connects to WiFi to push data directly to **Firebase Realtime Database** using the [mobizt Firebase-ESP-Client](https://github.com/mobizt/Firebase-ESP-Client) library. It also receives commands and callbacks from Firebase. The web dashboard is a **Next.js app deployed on Vercel** with **Firebase Authentication** for user login.

> **No Raspberry Pi needed!** ESP32 talks to Firebase directly via WiFi.

---

## Architecture Diagram

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
graph TB
    subgraph "Room 1 — Bathroom"
        RFID1[MFRC522 RFID<br/>Usage Tracking] --> R1[Room ESP32 #1]
        R1S[Flow Sensor<br/>YF-S201 (leak)] --> R1
        R1 --> R1E[ESP-NOW Transmitter]
    end

    subgraph "Room 2 — Kitchen"
        RFID2[MFRC522 RFID<br/>Usage Tracking] --> R2[Room ESP32 #2]
        R2S[Flow Sensor<br/>YF-S201 (leak)] --> R2
        R2 --> R2E[ESP-NOW Transmitter]
    end

    subgraph "Room 3 — Shower"
        RFID3[MFRC522 RFID<br/>Usage Tracking] --> R3[Room ESP32 #3]
        R3S[Flow Sensor<br/>YF-S201 (leak)] --> R3
        R3 --> R3E[ESP-NOW Transmitter]
    end

    subgraph "Main ESP32 — Centralized"
        direction TB
        ESPRX[ESP-NOW Receiver<br/>Aggregates Room Data]
        MFS[Calibrated Flow Sensor<br/>YF-S201 (GPIO 34)] --> MAIN[Main ESP32]
        MAIN --> RELAY1[1-ch Relay 10A<br/>Solenoid 1]
        MAIN --> RELAY2[1-ch Relay 10A<br/>Solenoid 2]
        RELAY1 --> SOL1[Solenoid Valve 1<br/>12V NC]
        RELAY2 --> SOL2[Solenoid Valve 2<br/>12V NC]
        ESPRX --> MAIN
        MAIN --> WIFI[WiFi + mobizt<br/>Firebase-ESP-Client]
    end

    subgraph "Firebase Cloud"
        RTDB[(Firebase Realtime<br/>Database)]
        Auth[Firebase Authentication<br/>User Login]
    end

    subgraph "Vercel"
        NextJS[Next.js App<br/>Web Dashboard]
    end

    R1E -.->|ESP-NOW| ESPRX
    R2E -.->|ESP-NOW| ESPRX
    R3E -.->|ESP-NOW| ESPRX
    WIFI -.->|WiFi + mobizt SDK| RTDB
    RTDB --> NextJS
    Auth --> NextJS
```

</details>

---

## Data Flow (End-to-End)

```
Step 1: RFID TAP (per room)
        Customer taps Mifare card on MFRC522 reader
        → Validate card against registered cards for this room
        → Send RFID event via ESP-NOW to main ESP32
        → Log RFID tag + timestamp to SPIFFS / send via ESP-NOW

Step 2: LEAK DETECTION (per room)
        Room flow sensor monitors for leaks (uncalibrated):
        → Flow detected when no RFID session = leak alert
        → Send leak_alert via ESP-NOW to main ESP32

Step 3: CENTRALIZED SOLENOID CONTROL (main ESP32)
        Main ESP32 receives ESP-NOW data from rooms:
        → Validates RFID session + checks leak alerts
        → Controls 2 solenoid valves via relays (GPIO HIGH/LOW)
        → Reads calibrated flow sensor for accurate metering
        → Smart auto on/off prevents overheating

Step 4: ESP-NOW TRANSMISSION (every 5 sec)
        Room ESP32 → Main ESP32 (broadcast)
        → Payload: {room_id, rfid_tag, pulses, leak_alert}

Step 5: MAIN ESP32 → FIREBASE (WiFi + mobizt)
        Main ESP32 receives from all 3 rooms via ESP-NOW:
        → Aggregate room data into Firebase JSON structure
        → Push to Firebase RTDB using mobizt Firebase-ESP-Client
        → Path: /rooms/{room_id}/data, /rooms/{room_id}/alerts
        → Also reads commands from Firebase (remote shutoff, config updates)

Step 6: FIREBASE CLOUD
        → Realtime Database stores all room data, usage logs, alerts
        → Firebase Authentication handles user login (email/password or Google)
        → Real-time sync to all connected clients
        → ESP32 receives callbacks for remote commands

Step 7: USER ACTION (Next.js on Vercel)
        → User logs in via Firebase Auth
        → Dashboard displays real-time readings per room (Firebase RTDB listener)
        → Usage logs per person (RFID tag + duration + volume)
        → Leak alerts appear instantly (real-time sync)
        → User can send remote commands (shutoff, config) via Firebase → ESP32
```

---

## Communication Paths

| Path | Method | Protocol | Library |
|------|--------|----------|---------|
| RFID Card → Room ESP32 | SPI (MFRC522) | Mifare Classic | MFRC522 library |
| Flow Sensor → Room ESP32 | Pulse (GPIO interrupt) | Rising edge | Arduino ISR |
| Main ESP32 → Relay → Solenoid | GPIO HIGH/LOW | Digital signal | Arduino digitalWrite |
| Room ESP32 → Main ESP32 | ESP-NOW (wireless) | Binary payload | esp_now.h (built-in) |
| Main ESP32 → Firebase | WiFi + HTTPS | JSON (RTDB) | mobizt Firebase-ESP-Client |
| Firebase → Main ESP32 | WiFi + HTTPS | Callbacks/Streams | mobizt Firebase-ESP-Client |
| Firebase → Next.js | WebSocket (RTDB) | Real-time sync | Firebase JS SDK |
| User → Dashboard | HTTPS | Internet | Next.js + Firebase Auth |
| Dashboard → ESP32 | Firebase RTDB | Remote commands | mobizt stream + set |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **ESP-NOW for room-to-main** | Low-latency, no WiFi router needed, works offline, peer-to-peer |
| **mobizt Firebase-ESP-Client** | Direct ESP32 → Firebase, no RPi bridge, stream + callback support |
| **WiFi on main ESP32 only** | Room ESP32s stay offline (ESP-NOW only) — saves power, no WiFi config per room |
| **Centralized solenoid control** | Main ESP32 controls both solenoid valves — room ESP32s only handle RFID + leak detection |
| **RFID per room** | MFRC522 tracks who used water (tap card to log usage) |
| **Firebase RTDB** | Real-time sync, ESP32 reads/writes directly, no backend server needed |
| **Firebase Auth** | User login (email/password, Google sign-in) — no custom auth system |
| **Next.js on Vercel** | Serverless, auto-deploy from Git, free tier sufficient |
| **No RPi needed** | ESP32 handles everything — WiFi, Firebase, sensors, RFID, relays |
| **6 Leak Detection Rules** | No RFID+flow, session ended+flow, solenoid OFF+flow, continuous flow, drip, night flow |
| **RFID-based leak context** | RFID session state tells firmware whether flow is expected or a leak |
| **Check Valves per Room** | Prevents backflow contamination between rooms |
| **SPIFFS Backup** | Survives WiFi disconnects — data cached locally until reconnect |
| **921600 baud** | High throughput for 3 rooms × 5 sec interval; reliable on CP2102/CH340 |

---

## Hardware Summary

| Component | Qty | Purpose |
|-----------|-----|---------|
| ESP32 38-Pin Dev Board | 4 | 3 room + 1 main |
| ESP32 38-Pin Expansion Board | 4 | Screw terminals for wiring |
| MFRC522 RFID Reader | 3 | 1 per room — usage tracking |
| YF-S201 Flow Sensor | 4 | 3 rooms (leak detection, uncalibrated) + 1 main (calibrated) |
| 1-ch Relay 10A | 2 | Main ESP32 — controls solenoid valves |
| Solenoid Valve 1/2" NC | 2 | 12V DC, normally closed — centralized at main |
| Check Valve 1/2" | 2 | One per solenoid line (backflow prevention) |
| 12V 5A Switching PSU (S-60-12 / LRS-60-12) | 4 | 1 per ESP32 — Mains power → 12V |
| LM2596S Buck Converter | 4 | 1 per ESP32 — 12V → 5V |
| Waterproof ABS Enclosure IP67 (175×125×75mm) | 4 | One per ESP32 |
| ~~Raspberry Pi~~ | ~~1~~ | ~~Serial-to-Firebase bridge~~ — **NO LONGER NEEDED** |

---

## Power Architecture

```
Per-ESP32 Power (×4 — each has its own PSU + buck):

220V AC Outlet
    │
    ▼
12V 5A Switching PSU (S-60-12 / LRS-60-12)
    │
    ├──► 12V Rail → Solenoid Valves (main ESP32 only)
    │
    ▼
LM2596S Buck Converter (12V → 5V)
    │
    ├──► ESP32 VIN (5V)
    ├──► Flow Sensor VCC (5V)
    └──► RFID / other 5V sensors
```

> **Room ESP32s** connect to: MFRC522 RFID (SPI) and YF-S201 flow sensor (GPIO 26, leak detection). **Main ESP32** connects to: calibrated YF-S201 flow sensor (GPIO 34), 2× 1-ch relay (GPIO 25, 13) for solenoid valves, and WiFi. Main ESP32 is centralized before the rooms — controls both solenoid valves and reads calibrated flow sensor.

---

## References

- [Raspberry Pi OS Documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- [Raspberry Pi Imager GitHub](https://github.com/raspberrypi/rpi-imager)
- [Raspberry Pi Forums - OS Installation](https://forums.raspberrypi.com/viewforum.php?f=117)
- [Debian Trixie Release Notes](https://www.debian.org/releases/trixie/)