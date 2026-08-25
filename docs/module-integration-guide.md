# Module Integration Guide — TapFlow

> **Purpose:** How all ESP32 modules wire together to form the complete anomaly detection + leak detection system. Covers module responsibilities, data flow, ESP-NOW protocol, and Firebase integration.
> **Builds on:** [anomaly-detection-guide.md](./anomaly-detection-guide.md), [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md)
> **Feeds into:** [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md)

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Room ESP32 Module Architecture](#2-room-esp32-module-architecture)
3. [Main ESP32 Module Architecture](#3-main-esp32-module-architecture)
4. [Module Responsibilities Matrix](#4-module-responsibilities-matrix)
5. [Data Flow: Sensor → Detection → Alert → Firebase](#5-data-flow-sensor--detection--alert--firebase)
6. [ESP-NOW Protocol (Room → Main)](#6-espnow-protocol-room--main)
7. [Firebase RTDB Integration](#7-firebase-rtdb-integration)
8. [Module Initialization Order](#8-module-initialization-order)
9. [Main Loop Execution Order](#9-main-loop-execution-order)
10. [Error Handling & Fallbacks](#10-error-handling--fallbacks)
11. [Configuration Management](#11-configuration-management)
12. [Validation Checklist](#12-validation-checklist)

---

## 1. Module Overview

### Room ESP32 Modules (×3)

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM ESP32 MODULE STACK                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  water-meter.ino          Main sketch (setup + loop)      │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  config.h              All parameters (pins, thresholds)  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────┬───────────┼───────────┬───────────┬───────────┐  │
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  sensor_    rfid_       espnow_     local_      anomaly_    serial_│
│  manager.h  manager.h   comm.h      rules.h     detector.h  comm.h │
│  (pulses)   (RFID)      (ESP-NOW)   (leak)      (anomaly)   (USB) │
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  ┌───────────┬───────────┬───────────┬───────────┬───────────┐  │
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  wifi_      data_       led_        ntp_        ota_        —   │
│  manager.h  logger.h    indicator.h sync.h      updater.h       │
│  (WiFi)     (SPIFFS)    (LED)       (NTP)       (OTA)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Main ESP32 Modules (×1)

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN ESP32 MODULE STACK                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  main-esp32.ino          Main sketch (setup + loop)       │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  config.h              All parameters (pins, thresholds)  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────┬───────────┼───────────┬───────────┬───────────┐  │
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  sensor_    espnow_     firebase_   relay_      leak_       anomaly_│
│  manager.h  receiver.h  client.h    controller.h detector.h  detector.h│
│  (pulses)   (ESP-NOW)   (Firebase)  (relays)    (leak)      (anomaly)│
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  ┌───────────┬───────────┬───────────┬───────────┬───────────┐  │
│  │           │           │           │           │           │  │
│  ▼           ▼           ▼           ▼           ▼           ▼  │
│  wifi_      data_       led_        ntp_        ota_        serial_│
│  manager.h  logger.h    indicator.h sync.h      updater.h   comm.h│
│  (WiFi)     (SPIFFS)    (LED)       (NTP)       (OTA)       (USB)│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Room ESP32 Module Architecture

### 2.1 Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM ESP32: MODULE DEPENDENCIES                                │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  config.h ◄────────────────── All modules read config.h        │
│      │                                                           │
│      ├──► sensor_manager.h   Reads flow sensor (GPIO 26)       │
│      │        │                                                   │
│      │        ├──► flow_rate, pulses, volume                    │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► local_rules.h      Leak detection (6 rules)          │
│      │        │                                                   │
│      │        ├──► leak_alert, leak_flags                       │
│      │        ├──► controls: PIN_SSR, PIN_RELAY                 │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► anomaly_detector.h Anomaly detection (3 methods)     │
│      │        │                                                   │
│      │        ├──► anomaly_flags, zscore, spike, burst          │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► espnow_comm.h      ESP-NOW transmitter               │
│      │        │                                                   │
│      │        ├──► sends: sensor + leak + anomaly data          │
│      │        │   to main ESP32                                 │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► rfid_manager.h     MFRC522 RFID reader               │
│      │        │                                                   │
│      │        ├──► card_uid, session_active                     │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► serial_comm.h      USB Serial output (debug)         │
│      │        │                                                   │
│      │        ├──► JSON frames to Serial Monitor                │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► data_logger.h      SPIFFS fallback logging           │
│      │        │                                                   │
│      │        ├──► logs alerts when WiFi/ESP-NOW unavailable    │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► led_indicator.h    LED status patterns               │
│      │        │                                                   │
│      │        ├──► green=safe, yellow=warning, red=leak        │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► wifi_manager.h     WiFi (for OTA + NTP only)         │
│      │        │                                                   │
│      │        ├──► connects to WiFi for OTA updates             │
│      │        │                                                   │
│      │        ▼                                                   │
│      ├──► ntp_sync.h         NTP time sync                     │
│      │        │                                                   │
│      │        ├──► timestamps for alerts                        │
│      │        │                                                   │
│      │        ▼                                                   │
│      └──► ota_updater.h      OTA firmware updates              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Through Modules

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM ESP32: DATA FLOW PER CYCLE (~100ms)                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  T=0ms     sensor_manager.readAll()                            │
│            │  Reads ISR pulse counter (atomic)                  │
│            │  Calculates: flowRate, volume, pulses              │
│            │  Output: float flowRate                            │
│            ▼                                                    │
│  T=5ms     rfid_manager.poll()                                 │
│            │  Checks MFRC522 for card tap                       │
│            │  Validates card UID against registered list        │
│            │  Manages session start/end                         │
│            │  Output: bool sessionActive, char cardUid[]        │
│            ▼                                                    │
│  T=10ms    local_rules.checkAll(flowRate, sessionActive, ...)  │
│            │  Runs Rules 1-6                                    │
│            │  Checks debounce timers                            │
│            │  Controls SSR + Solenoid if leak detected          │
│            │  Output: bool leakAlert, uint8_t leakFlags         │
│            ▼                                                    │
│  T=15ms    anomaly_detector.checkAll(flowRate, ...)            │
│            │  Runs rate-of-change, baseline, burst detection    │
│            │  Updates baseline tracker                          │
│            │  Output: bool spike, bool baseline_dev, bool burst │
│            ▼                                                    │
│  T=20ms    [IF send interval elapsed: every 5 sec]             │
│            espnow_comm.send(payload)                            │
│            │  Builds JSON payload:                              │
│            │  { room_id, pulses, flow_rate, volume,             │
│            │    leak_alert, leak_flags,                         │
│            │    anomaly_spike, anomaly_baseline, anomaly_burst }│
│            │  Sends via ESP-NOW to main ESP32                   │
│            ▼                                                    │
│  T=25ms    led_indicator.update()                               │
│            │  Sets LED pattern based on:                        │
│            │  - leakAlert → red flash                           │
│            │  - anomaly → yellow blink                          │
│            │  - normal → green solid                            │
│            ▼                                                    │
│  T=30ms    [IF USB Serial available]                           │
│            serial_comm.sendStatus()                             │
│            │  Outputs JSON to Serial Monitor (921600 baud)      │
│            ▼                                                    │
│  T=50ms    [IF alert logged]                                   │
│            data_logger.logAlert(alertType, roomId)              │
│            │  Writes to SPIFFS if ESP-NOW/ WiFi unavailable     │
│            ▼                                                    │
│  T=100ms   delay(100) — end of cycle                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Main ESP32 Module Architecture

### 3.1 Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN ESP32: MODULE DEPENDENCIES                                │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  config.h ◄────────────────── All modules read config.h        │
│      │                                                           │
│      ├──► sensor_manager.h   Reads calibrated flow sensor      │
│      │        │              (GPIO 34)                          │
│      │        ├──► inlet_flow_rate, inlet_volume                │
│      │        │                                                   │
│      ▼                                                           │
│      ├──► espnow_receiver.h  ESP-NOW receiver                  │
│      │        │                                                   │
│      │        ├──► receives: room data from 3 room ESP32s      │
│      │        ├──► output: RoomData rooms[3]                    │
│      │        │   (pulses, flow_rate, volume,                   │
│      │        │    leak_alert, leak_flags,                      │
│      │        │    anomaly_spike, anomaly_baseline, anomaly_burst)│
│      │        │                                                   │
│      ▼                                                           │
│      ├──► leak_detector.h    Aggregated leak detection         │
│      │        │                                                   │
│      │        ├──► mass_balance check (inlet vs rooms)          │
│      │        ├──► post-shutoff verification                    │
│      │        ├──► intermittent leak detection                  │
│      │        ├──► sensor disagreement check                    │
│      │        ├──► output: global_leak_flag, severity           │
│      │        │                                                   │
│      ▼                                                           │
│      ├──► anomaly_detector.h Cross-room anomaly detection      │
│      │        │                                                   │
│      │        ├──► mass balance anomaly                         │
│      │        ├──► time-pattern analysis                        │
│      │        ├──► multi-room correlation                       │
│      │        ├──► trend detection (daily baselines)            │
│      │        ├──► output: global_anomaly_flag, anomaly_data    │
│      │        │                                                   │
│      ▼                                                           │
│      ├──► relay_controller.h Solenoid valve control            │
│      │        │                                                   │
│      │        ├──► controls 2CH relay (GPIO 19, GPIO 18)       │
│      │        ├──► shutoff solenoid 1, solenoid 2               │
│      │        ├──► verify shutoff (read flow after OFF)         │
│      │        ├──► output: solenoid1_on, solenoid2_on           │
│      │        │                                                   │
│      ▼                                                           │
│      ├──► firebase_client.h  Firebase RTDB + Auth              │
│      │        │                                                   │
│      │        ├──► push: room data, anomaly, alerts             │
│      │        ├──► pull: config overrides from dashboard        │
│      │        ├──► stream: real-time commands from dashboard    │
│      │        ├──► output: config updates, remote commands      │
│      │        │                                                   │
│      ▼                                                           │
│      ├──► serial_comm.h      USB Serial output (debug)         │
│      ├──► data_logger.h      SPIFFS fallback logging           │
│      ├──► led_indicator.h    LED status patterns               │
│      ├──► wifi_manager.h     WiFi connect + reconnect          │
│      ├──► ntp_sync.h         NTP time sync                     │
│      └──► ota_updater.h      OTA firmware updates              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow Per Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN ESP32: DATA FLOW PER CYCLE (~100ms)                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  T=0ms     sensor_manager.readAll()                            │
│            │  Reads calibrated flow sensor (GPIO 34)            │
│            │  Output: float inlet_flow_rate, float inlet_volume │
│            ▼                                                    │
│  T=5ms     espnow_receiver.poll()                              │
│            │  Checks for incoming ESP-NOW packets               │
│            │  Updates RoomData rooms[3] with latest data        │
│            │  Output: rooms[0..2] with full payloads            │
│            ▼                                                    │
│  T=10ms    [IF send interval elapsed: every 5 sec]             │
│            │                                                    │
│            ├──► leak_detector.checkAll(rooms, inlet, ...)      │
│            │        │                                           │
│            │        ├── Mass balance: inlet vs sum(rooms)      │
│            │        ├── Post-shutoff: flow after solenoid OFF  │
│            │        ├── Intermittent: leak count per room      │
│            │        ├── Sensor disagreement: room vs main      │
│            │        │                                           │
│            │        ▼                                           │
│            │    global_leak_flag, severity, leak_details       │
│            │                                                    │
│            ├──► anomaly_detector.checkAll(rooms, inlet, ...)   │
│            │        │                                           │
│            │        ├── Cross-room: 2+ rooms anomaly = flag   │
│            │        ├── Time-pattern: night/weekend usage      │
│            │        ├── Trend: daily volume vs 7-day avg      │
│            │        │                                           │
│            │        ▼                                           │
│            │    global_anomaly_flag, anomaly_details           │
│            │                                                    │
│            ├──► relay_controller.executeResponse(severity)     │
│            │        │                                           │
│            │        ├── EMERGENCY → shutoff both solenoids    │
│            │        ├── CRITICAL → shutoff + retry            │
│            │        ├── WARNING → log only                    │
│            │        │                                           │
│            │        ▼                                           │
│            │    solenoid1_on, solenoid2_on updated             │
│            │                                                    │
│            └──► firebase_client.pushData(rooms, anomaly, ...)  │
│                     │                                           │
│                     ├── Write /rooms/{id}/data                 │
│                     ├── Write /rooms/{id}/anomaly              │
│                     ├── Write /alerts/active/ (if alert)       │
│                     ├── Write /anomaly/global                  │
│                     │                                           │
│                     ▼                                           │
│                 Firebase RTDB updated                          │
│                                                                 │
│  T=50ms    firebase_client.stream()                            │
│            │  Check for incoming commands from dashboard        │
│            │  (remote shutoff, config update, recalibrate)     │
│            ▼                                                    │
│  T=60ms    led_indicator.update()                               │
│  T=70ms    serial_comm.sendStatus()                             │
│  T=100ms   delay(100) — end of cycle                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Module Responsibilities Matrix

### 4.1 Room ESP32 Modules

| Module | Runs | Input | Output | Detection Role |
|--------|------|-------|--------|----------------|
| `sensor_manager.h` | Every cycle | GPIO 26 pulses | flowRate, volume, pulses | Provides raw data |
| `rfid_manager.h` | Every cycle | MFRC522 SPI | sessionActive, cardUid | Context for leak rules |
| `local_rules.h` | Every cycle | flowRate, sessionActive, solenoidOn | leakAlert, leakFlags | **Core leak detection** |
| `anomaly_detector.h` | Every cycle | flowRate, flowRate_prev | spike, baseline_dev, burst | **Core anomaly detection** |
| `espnow_comm.h` | Every 5 sec | All above outputs | ESP-NOW packet | Transmits to main |
| `serial_comm.h` | On interval | All above outputs | JSON to Serial | Debug output |
| `data_logger.h` | On alert | Alert data | SPIFFS entry | Offline fallback |
| `led_indicator.h` | Every cycle | leakAlert, anomalyFlag | LED pattern | Visual status |

### 4.2 Main ESP32 Modules

| Module | Runs | Input | Output | Detection Role |
|--------|------|-------|--------|----------------|
| `sensor_manager.h` | Every cycle | GPIO 34 pulses | inlet_flow_rate, inlet_volume | Calibrated metering |
| `espnow_receiver.h` | Every cycle | ESP-NOW packets | rooms[3] data | Aggregates room data |
| `leak_detector.h` | Every 5 sec | rooms[], inlet_volume | global_leak, severity | **Cross-room leak detection** |
| `anomaly_detector.h` | Every 5 sec | rooms[], inlet_volume | global_anomaly, anomaly_data | **Cross-room anomaly detection** |
| `relay_controller.h` | On command | severity, leakFlags | solenoid1_on, solenoid2_on | **Emergency shutoff execution** |
| `firebase_client.h` | Every 5 sec | All above outputs | Firebase RTDB writes | Cloud sync + dashboard |
| `firebase_client.h` | Streaming | Firebase commands | config updates, remote cmds | Dashboard → ESP32 |
| `serial_comm.h` | On interval | All above outputs | JSON to Serial | Debug output |

---

## 5. Data Flow: Sensor → Detection → Alert → Firebase

### 5.1 Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA PIPELINE                       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  PHYSICAL LAYER                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Water flows through YF-S201 sensor                      │  │
│  │  Hall effect generates pulses (GPIO interrupt)            │  │
│  │  ~450 pulses per liter                                    │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  FIRMWARE LAYER (Room ESP32)                                    │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  sensor_manager: ISR counts pulses → flowRate (L/min)     │  │
│  │  rfid_manager: reads card → sessionActive                 │  │
│  │  local_rules: applies 6 rules → leakAlert + leakFlags     │  │
│  │  anomaly_detector: z-score, spike, burst → anomalyFlags   │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  WIRELESS LAYER                                                  │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  espnow_comm: sends JSON payload via ESP-NOW              │  │
│  │  { room_id, pulses, flow_rate, volume,                    │  │
│  │    leak_alert, leak_flags,                                │  │
│  │    anomaly_spike, anomaly_baseline, anomaly_burst }       │  │
│  │  Frequency: every 5 seconds                               │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  AGGREGATION LAYER (Main ESP32)                                 │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  espnow_receiver: collects data from 3 rooms              │  │
│  │  leak_detector: mass balance, post-shutoff, intermittent  │  │
│  │  anomaly_detector: cross-room, time-pattern, trend        │  │
│  │  relay_controller: execute shutoff if severity >= CRITICAL│  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  CLOUD LAYER                                                     │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  firebase_client: pushes to Firebase RTDB via WiFi        │  │
│  │  /rooms/{id}/data      — sensor readings                  │  │
│  │  /rooms/{id}/anomaly   — anomaly flags + scores           │  │
│  │  /alerts/active/{id}   — active leak/anomaly alerts       │  │
│  │  /anomaly/global       — cross-room anomaly data          │  │
│  │  /baselines/           — learned patterns                 │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│  DASHBOARD LAYER                                                │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │  Next.js on Vercel                                       │  │
│  │  Firebase onValue() listener — real-time sync             │  │
│  │  Renders: room cards, flow charts, alert feed, anomaly    │  │
│  │  gauge, trend analysis, threshold config                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Latency Budget

| Stage | Latency | Notes |
|-------|---------|-------|
| Sensor pulse → ISR count | < 1ms | Hardware interrupt |
| ISR count → flowRate calc | < 5ms | Per cycle |
| Leak rule evaluation | < 10ms | 6 rules × simple comparisons |
| Anomaly detection | < 10ms | Z-score + rate-of-change |
| ESP-NOW transmit | < 50ms | Wireless, best effort |
| Main ESP32 aggregation | < 100ms | Per 5-sec cycle |
| Firebase push (WiFi) | 100–500ms | Depends on network |
| Dashboard render | < 100ms | Firebase onValue callback |
| **Total (sensor → dashboard)** | **< 1 second** | End-to-end |

---

## 6. ESP-NOW Protocol (Room → Main)

### 6.1 Packet Structure

```cpp
// Room → Main ESP32 (every 5 sec)
struct RoomPayload {
    uint8_t  room_id;              // 1, 2, or 3
    uint32_t ts;                   // Timestamp (millis or NTP)
    uint32_t pulses;               // Pulse count this interval
    float    flow_rate_lpm;        // Current flow rate (L/min)
    uint32_t volume_ml;            // Cumulative volume (ml)
    bool     leak_alert;           // Any leak rule triggered
    uint8_t  leak_flags;           // Bitmask: rules 1-6
    bool     anomaly_spike;        // Rate-of-change spike
    bool     anomaly_baseline;     // Z-score > 3.0
    bool     anomaly_burst;        // Short burst detected
    uint8_t  anomaly_flags;        // Bitmask: spike|baseline|burst
    uint8_t  session_active;       // RFID session state
    uint8_t  solenoid_on;          // Solenoid valve state
    uint8_t  reserved[3];          // Future use / alignment
};
// Total: ~40 bytes (well within ESP-NOW 250-byte limit)
```

### 6.2 ESP-NOW Callback Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  ESP-NOW TRANSMIT FLOW (Room ESP32)                            │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Every 5 sec:                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Build RoomPayload struct from module outputs          │  │
│  │  2. Call esp_now_send(mainMac, &payload, sizeof(payload)) │  │
│  │  3. ESP-NOW callback fires:                               │  │
│  │     - SUCCESS: log "sent" to Serial                       │  │
│  │     - FAIL: retry once, then log error                    │  │
│  │  4. If 3 consecutive fails:                               │  │
│  │     - Switch to Serial-only output                        │  │
│  │     - Log to SPIFFS for later sync                        │  │
│  │     - LED shows red blink (send failed)                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ESP-NOW RECEIVE FLOW (Main ESP32)                       │  │
│  │  ───────────────────────────────────────────────────────  │  │
│  │                                                           │  │
│  │  On receive callback:                                     │  │
│  │  1. Parse RoomPayload from bytes                         │  │
│  │  2. Validate room_id (1-3)                               │  │
│  │  3. Store in rooms[room_id - 1]                          │  │
│  │  4. Update last_seen timestamp                           │  │
│  │  5. If room not seen for > 30 sec:                       │  │
│  │     - Flag room as "offline"                             │  │
│  │     - Log warning                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Room Offline Handling

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM OFFLINE HANDLING                                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  IF room ESP32 not received for > 30 sec:                      │
│    1. Mark room as OFFLINE in main ESP32 memory                │
│    2. Set room flow_rate = 0 (assume no flow)                  │
│    3. Set room leak_alert = false (can't confirm)              │
│    4. Log warning: "Room X offline — no ESP-NOW data"          │
│    5. Send Firebase: /rooms/{id}/status = "offline"            │
│                                                                 │
│  IF room comes back online:                                     │
│    1. Resume normal data collection                            │
│    2. Clear OFFLINE flag                                        │
│    3. Send Firebase: /rooms/{id}/status = "online"             │
│    4. Sync any SPIFFS-stored offline data                      │
│                                                                 │
│  Impact on detection:                                           │
│    - Mass balance: skip offline room from calculation          │
│    - Anomaly: can't detect anomalies for offline room          │
│    - Dashboard: show "offline" badge for room                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Firebase RTDB Integration

### 7.1 Write Operations (Main ESP32 → Firebase)

| Path | Frequency | Data |
|------|-----------|------|
| `/rooms/{id}/data` | Every 5 sec | flow_rate_lpm, volume_ml, ts |
| `/rooms/{id}/anomaly` | Every 5 sec | spike, baseline, burst, zscore |
| `/rooms/{id}/status` | On change | "online" / "offline" |
| `/alerts/active/{id}` | On alert | Full alert object |
| `/alerts/history/{id}` | On resolve | Resolved alert object |
| `/anomaly/global` | Every 5 sec | mass_balance, time_pattern |
| `/anomaly/trend/{room_id}` | Daily | slope, weekly_increase |
| `/baselines/periods/{period}` | Daily | avg_ml, std_ml |
| `/config/anomaly/{key}` | On change | Updated threshold value |

### 7.2 Read Operations (Firebase → Main ESP32)

| Path | Method | Purpose |
|------|--------|---------|
| `/config/anomaly/spike_threshold` | Stream | Dashboard threshold override |
| `/config/anomaly/zscore_anomaly` | Stream | Dashboard threshold override |
| `/commands/{device_id}` | Stream | Remote shutoff, recalibrate |
| `/rooms/{id}/anomaly` | Read | Current anomaly state |

### 7.3 Firebase Stream (Real-time Commands)

```
┌─────────────────────────────────────────────────────────────────┐
│  FIREBASE STREAM: Dashboard → ESP32                            │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Dashboard writes to:                                           │
│  /commands/tapflow-main                                         │
│  {                                                              │
│    "cmd": "shutoff",                                            │
│    "room_id": 2,                                                │
│    "ts": 1703123456789                                          │
│  }                                                              │
│                                                                 │
│  Main ESP32 stream callback:                                    │
│  1. Parse command JSON                                          │
│  2. If cmd == "shutoff":                                        │
│     - Call relay_controller.shutoffRoom(room_id)               │
│     - Update Firebase: /rooms/{id}/solenoid = false            │
│  3. If cmd == "enable":                                         │
│     - Call relay_controller.enableRoom(room_id)                │
│     - Update Firebase: /rooms/{id}/solenoid = true             │
│  4. If cmd == "recalibrate":                                    │
│     - Enter calibration mode                                    │
│  5. If cmd == "update_config":                                  │
│     - Update local thresholds from Firebase values             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Firebase Auth

```
┌─────────────────────────────────────────────────────────────────┐
│  FIREBASE AUTHENTICATION                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ESP32 → Firebase:                                              │
│    • Optional: anonymous auth or service account                │
│    • Most RTDB writes don't require auth (test mode)           │
│    • For production: use Firebase Auth token from dashboard     │
│                                                                 │
│  Dashboard → Firebase:                                          │
│    • Email/Password sign-in                                     │
│    • Google sign-in                                             │
│    • Firebase ID token sent with all requests                  │
│    • RTDB rules validate token                                 │
│                                                                 │
│  RTDB Rules (production):                                       │
│  {                                                              │
│    "rules": {                                                   │
│      "rooms": {                                                 │
│        ".read": "auth != null",                                │
│        ".write": "auth != null"                                │
│      },                                                         │
│      "alerts": {                                                │
│        ".read": "auth != null",                                │
│        ".write": "auth != null"                                │
│      },                                                         │
│      "config": {                                                │
│        ".read": "auth != null",                                │
│        ".write": "auth != null && auth.uid === 'admin_uid'"   │
│      }                                                          │
│    }                                                            │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Module Initialization Order

### 8.1 Room ESP32 Setup Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM ESP32: SETUP ORDER                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. Serial.begin(921600)                                        │
│     └─ Wait for USB CDC                                        │
│                                                                 │
│  2. sensor_manager.begin()                                      │
│     └─ Attach ISR to GPIO 26                                   │
│     └─ Initialize pulse counters to 0                          │
│                                                                 │
│  3. rfid_manager.begin()                                       │
│     └─ Initialize MFRC522 via SPI                              │
│     └─ Load registered card UIDs from config                   │
│                                                                 │
│  4. local_rules.begin()                                        │
│     └─ Load thresholds from config.h                           │
│     └─ Initialize debounce counters                            │
│     └─ Set SSR + Relay pins to OUTPUT, LOW (OFF)               │
│                                                                 │
│  5. anomaly_detector.begin()                                   │
│     └─ Initialize baseline tracker                             │
│     └─ Load thresholds from config.h                           │
│     └─ Initialize burst tracker                                │
│                                                                 │
│  6. espnow_comm.begin(mainMac)                                 │
│     └─ Init WiFi in STA mode (for ESP-NOW)                     │
│     └─ Init ESP-NOW                                            │
│     └─ Register peer (main ESP32 MAC)                          │
│                                                                 │
│  7. wifi_manager.begin()                                       │
│     └─ Connect to WiFi (for OTA + NTP only)                    │
│     └─ Non-blocking — continues if WiFi fails                  │
│                                                                 │
│  8. ntp_sync.begin()                                           │
│     └─ Sync time via NTP                                       │
│     └─ Provides timestamps for alerts                          │
│                                                                 │
│  9. data_logger.begin()                                        │
│     └─ Mount SPIFFS                                            │
│     └─ Check for offline logs to sync                          │
│                                                                 │
│  10. ota_updater.begin()                                       │
│      └─ Register OTA callbacks                                 │
│      └─ Start OTA server                                       │
│                                                                 │
│  11. led_indicator.begin()                                     │
│      └─ Set LED pins to OUTPUT                                 │
│      └─ Show "ready" pattern (green blink)                     │
│                                                                 │
│  12. Serial.println("ready")                                   │
│      └─ JSON status frame to Serial Monitor                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Main ESP32 Setup Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN ESP32: SETUP ORDER                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. Serial.begin(921600)                                        │
│                                                                 │
│  2. sensor_manager.begin()                                      │
│     └─ Attach ISR to GPIO 34 (calibrated sensor)               │
│                                                                 │
│  3. relay_controller.begin()                                    │
│     └─ Set GPIO 19, GPIO 18 to OUTPUT, LOW (solenoids OFF)    │
│     └─ Initialize retry counter                                │
│                                                                 │
│  4. espnow_receiver.begin()                                     │
│     └─ Init WiFi in STA mode                                   │
│     └─ Init ESP-NOW                                            │
│     └─ Register receive callback                               │
│                                                                 │
│  5. wifi_manager.begin()                                       │
│     └─ Connect to WiFi for Firebase                            │
│     └─ Critical: Firebase requires WiFi                        │
│                                                                 │
│  6. ntp_sync.begin()                                           │
│     └─ Sync time for Firebase timestamps                       │
│                                                                 │
│  7. firebase_client.begin()                                    │
│     └─ Initialize mobizt Firebase-ESP-Client                   │
│     └─ Authenticate with Firebase                              │
│     └─ Start stream for commands from dashboard                │
│                                                                 │
│  8. leak_detector.begin()                                      │
│     └─ Load thresholds from config.h                           │
│     └─ Initialize balance tracker                              │
│     └─ Initialize intermittent counter                         │
│                                                                 │
│  9. anomaly_detector.begin()                                   │
│     └─ Load thresholds from config.h                           │
│     └─ Initialize time-pattern baselines                       │
│     └─ Load daily baselines from Firebase (if available)       │
│                                                                 │
│  10. data_logger.begin()                                       │
│      └─ Mount SPIFFS                                           │
│                                                                 │
│  11. ota_updater.begin()                                       │
│                                                                 │
│  12. led_indicator.begin()                                     │
│      └─ Show "ready" pattern                                   │
│                                                                 │
│  13. serial_comm.begin()                                       │
│      └─ Send ready status                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Main Loop Execution Order

### 9.1 Room ESP32 Main Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  ROOM ESP32: MAIN LOOP (every ~100ms)                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  LOOP {                                                         │
│                                                                 │
│    1. wifi_manager.loop()           [non-blocking]              │
│    2. otaUpdater.loop()            [non-blocking]              │
│    3. sensor_manager.readAll()     [~5ms]                      │
│    4. rfid_manager.poll()          [~5ms]                      │
│    5. local_rules.checkAll()       [~2ms]                      │
│    6. anomaly_detector.checkAll()  [~2ms]                      │
│                                                                 │
│    7. [IF 5 sec elapsed]                                        │
│       espnow_comm.send()            [~10ms]                    │
│                                                                 │
│    8. [IF USB Serial available]                                 │
│       serial_comm.handleCommand()   [~1ms]                     │
│                                                                 │
│    9. led_indicator.update()        [~1ms]                      │
│    10. ntp_sync.update()            [~1ms, non-blocking]       │
│                                                                 │
│    delay(100)                                                   │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Main ESP32 Main Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  MAIN ESP32: MAIN LOOP (every ~100ms)                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  LOOP {                                                         │
│                                                                 │
│    1. wifi_manager.loop()           [non-blocking]              │
│    2. otaUpdater.loop()            [non-blocking]              │
│    3. sensor_manager.readAll()     [~5ms]                      │
│    4. espnow_receiver.poll()       [~2ms]                      │
│    5. firebase_client.stream()     [~5ms, checks commands]     │
│                                                                 │
│    6. [IF 5 sec elapsed]                                        │
│       a. leak_detector.checkAll()     [~10ms]                  │
│       b. anomaly_detector.checkAll()  [~10ms]                  │
│       c. relay_controller.execute()   [~2ms]                   │
│       d. firebase_client.pushData()   [~50ms, WiFi write]      │
│       e. serial_comm.sendStatus()     [~5ms]                   │
│                                                                 │
│    7. led_indicator.update()        [~1ms]                      │
│    8. ntp_sync.update()            [~1ms]                      │
│                                                                 │
│    delay(100)                                                   │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Error Handling & Fallbacks

### 10.1 ESP-NOW Failure

```
┌─────────────────────────────────────────────────────────────────┐
│  ESP-NOW FAILURE HANDLING                                       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  IF espnow_comm.send() fails:                                   │
│    1. Retry once (immediate)                                    │
│    2. IF retry fails:                                           │
│       - Increment consecutive_fail_count                        │
│       - LED: red blink (send failed)                           │
│       - Continue detection locally (leak rules still run)      │
│                                                                 │
│  IF consecutive_fail_count > 3:                                 │
│    1. Switch to Serial-only output                             │
│    2. Log all data to SPIFFS (offline mode)                    │
│    3. IF WiFi available:                                        │
│       - Send data directly to Firebase (bypass main ESP32)     │
│       - Use Firebase REST API via WiFi                         │
│    4. IF WiFi also unavailable:                                │
│       - Continue SPIFFS logging                                │
│       - Sync when connection restored                          │
│                                                                 │
│  Recovery:                                                      │
│    - When ESP-NOW reconnects:                                   │
│      - Sync SPIFFS-stored data to main ESP32                   │
│      - Clear SPIFFS after successful sync                      │
│      - Resume normal operation                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 WiFi Failure (Main ESP32)

```
┌─────────────────────────────────────────────────────────────────┐
│  WIFI FAILURE HANDLING (Main ESP32)                             │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  IF wifi_manager fails to connect:                              │
│    1. ESP-NOW still works (no WiFi needed)                     │
│    2. Room data still received and processed                   │
│    3. Leak/anomaly detection still runs locally                │
│    4. Relay control still works                                 │
│    5. Firebase push delayed (queued)                           │
│    6. LED: yellow blink (WiFi disconnected)                    │
│                                                                 │
│  IF WiFi disconnects mid-operation:                             │
│    1. Auto-reconnect (exponential backoff)                     │
│    2. Queue Firebase writes to SPIFFS                           │
│    3. On reconnect: flush SPIFFS queue to Firebase             │
│    4. Dashboard shows "delayed data" badge                     │
│                                                                 │
│  Detection impact:                                              │
│    - Leak detection: ✅ works (local on ESP32)                 │
│    - Anomaly detection: ✅ works (local on ESP32)              │
│    - Mass balance: ✅ works (local on main ESP32)              │
│    - Dashboard alerts: ❌ delayed until WiFi restored           │
│    - Remote commands: ❌ blocked until WiFi restored            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Firebase Failure

```
┌─────────────────────────────────────────────────────────────────┐
│  FIREBASE FAILURE HANDLING                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  IF firebase_client.pushData() fails:                           │
│    1. Log error to Serial Monitor                              │
│    2. Queue write to SPIFFS                                    │
│    3. Retry on next cycle (up to 3 retries)                    │
│    4. After 3 failures:                                         │
│       - Stop retrying (avoid battery drain from retry loop)    │
│       - Continue local operation                               │
│       - Try again in 60 seconds                                │
│                                                                 │
│  IF Firebase Auth fails:                                        │
│    1. Re-authenticate with stored credentials                  │
│    2. IF re-auth fails:                                         │
│       - Log error                                              │
│       - Continue without cloud sync                            │
│       - Dashboard shows "auth expired" warning                 │
│                                                                 │
│  Data integrity:                                                │
│    - All data logged to SPIFFS as backup                       │
│    - On Firebase reconnect: sync all queued data               │
│    - Timestamps preserved (NTP-synced)                         │
│    - No data loss even during extended outage                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Configuration Management

### 11.1 Config Sources (Priority Order)

```
┌─────────────────────────────────────────────────────────────────┐
│  CONFIGURATION PRIORITY                                         │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. Firebase (highest priority — dashboard overrides)          │
│     /config/anomaly/spike_threshold = 6.0                     │
│     → Overrides config.h value at runtime                      │
│                                                                 │
│  2. config.h (compile-time defaults)                           │
│     #define ANOMALY_SPIKE_THRESHOLD 5.0                        │
│     → Used if no Firebase override exists                      │
│                                                                 │
│  3. Hardcoded fallbacks (lowest priority)                      │
│     Default values in module constructors                      │
│     → Used if config.h is missing or invalid                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Runtime Config Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  RUNTIME CONFIG UPDATE                                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. User changes threshold on dashboard                        │
│     Dashboard writes to Firebase:                              │
│     /config/anomaly/spike_threshold = 6.0                      │
│                                                                 │
│  2. Main ESP32 receives Firebase stream event                  │
│     firebase_client.stream() callback fires                    │
│     Parses: path = /config/anomaly/spike_threshold             │
│             value = 6.0                                         │
│                                                                 │
│  3. Main ESP32 updates local config                            │
│     anomaly_detector.setThreshold("spike", 6.0)               │
│                                                                 │
│  4. Main ESP32 forwards to room ESP32s (optional)             │
│     espnow_comm.sendConfigUpdate({                             │
│       "cmd": "update_config",                                  │
│       "key": "spike_threshold",                                │
│       "value": 6.0                                             │
│     })                                                         │
│                                                                 │
│  5. Room ESP32 receives config update                          │
│     espnow_comm.handleConfigUpdate()                           │
│     anomaly_detector.setThreshold("spike", 6.0)               │
│                                                                 │
│  6. New threshold takes effect immediately                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Validation Checklist

- [ ] **Module init:** All modules initialize without crash (check Serial Monitor)
- [ ] **ISR safety:** Pulse counter atomic read works (no missed pulses)
- [ ] **ESP-NOW range:** Room ESP32 sends data within 30m of main ESP32
- [ ] **ESP-NOW payload:** RoomPayload struct matches between sender and receiver
- [ ] **Room offline:** If room ESP32 powers off, main marks it offline within 30 sec
- [ ] **Room recovery:** If room ESP32 powers back on, main resumes data within 5 sec
- [ ] **Leak detection:** All 6 rules trigger correctly (see leak-detection-advanced-guide.md)
- [ ] **Anomaly detection:** Rate-of-change, baseline, burst work (see anomaly-detection-guide.md)
- [ ] **Combined detection:** Leak + anomaly merge correctly (no duplicate alerts)
- [ ] **Relay control:** Emergency shutoff closes both solenoids
- [ ] **Post-shutoff verify:** Main ESP32 confirms flow stops after shutoff
- [ ] **Firebase write:** Data appears in Firebase Console within 5 sec
- [ ] **Firebase stream:** Dashboard command reaches ESP32 within 2 sec
- [ ] **WiFi failure:** ESP-NOW + detection still works without WiFi
- [ ] **ESP-NOW failure:** Data logged to SPIFFS, synced on reconnect
- [ ] **Config override:** Dashboard threshold change picked up by ESP32 within 10 sec
- [ ] **LED patterns:** Green=safe, yellow=warning, red=leak, red flash=emergency
- [ ] **Serial output:** JSON frames visible at 921600 baud
- [ ] **SPIFFS logging:** Alerts logged when offline, synced on reconnect
- [ ] **No memory leaks:** ESP32 runs for 24+ hours without crash (check heap)

---

## Related Guides

| Guide | Relationship |
|-------|-------------|
| [anomaly-detection-guide.md](./anomaly-detection-guide.md) | Anomaly algorithms used by modules |
| [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md) | Leak rules used by modules |
| [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md) | Dashboard consumes module data |
| [system-architecture.md](./system-architecture.md) | Overall system design |
| [esp32-firmware-complete-guide.md](./esp32-firmware-complete-guide.md) | Base firmware reference |
| [block-diagram.md](./block-diagram.md) | Hardware wiring reference |
