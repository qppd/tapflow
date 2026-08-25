# ESP32 Firmware Complete Guide — ESP-NOW + Firebase (mobizt)

> **Target:** 3 Room ESP32s + 1 Main ESP32 (38-pin Dev Module with Expansion Board)  
> **Sensors:** 3× YF-S201 Flow Sensors (1 per room), 3× MFRC522 RFID  
> **Communication:** ESP-NOW (room→main) + WiFi → Firebase RTDB (mobizt Firebase-ESP-Client)  
> **Relay:** Fotek 40A SSR per room for solenoid valve control (local leak shutoff)  
> **IDE:** Arduino IDE 2.x (Windows/macOS/Linux)  
> **Libraries:** ArduinoJson (≥ 7.x), MFRC522, Firebase-ESP-Client by mobizt (≥ 4.x), ESP-NOW (built-in)  
> **Audience:** Complete setup from hardware to deployed firmware

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Arduino IDE Installation](#arduino-ide-installation)
3. [ESP32 Board Support Configuration](#esp32-board-support-configuration)
4. [ArduinoJson Library Setup](#arduinojson-library-setup)
5. [Firmware Architecture & File Structure](#firmware-architecture--file-structure)
6. [Main Loop & Sensor Management](#main-loop--sensor-management)
7. [USB Serial Communication](#usb-serial-communication)
8. [Local Leak Detection Rules (Offline Fallback)](#local-leak-detection-rules-offline-fallback)
9. [Configuration (`config.h`)](#configuration-configh)
10. [Build, Upload & Verify](#build-upload--verify)
11. [Sensor Calibration (Bucket Test)](#sensor-calibration-bucket-test)
12. [OTA Firmware Updates](#ota-firmware-updates)
13. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Hardware Overview

### Room ESP32s (×3)

| Component | Qty | Key Specs |
|-----------|-----|-----------|
| **ESP32 Dev Module** | 3 | 38-pin, CP2102/CH340, 4 MB Flash |
| **ESP32 Expansion Board** | 3 | Screw terminals for all GPIOs |
| **MFRC522 RFID Reader** | 3 | SPI, 13.56MHz, reads Mifare Classic |
| **YF-S201 Flow Sensor** | 3 | 1/2" NPT, Hall effect, 5V, ~450 pulses/L |
| **Fotek 40A SSR** | 3 | DC control, powers room electrical line |
| **1-ch Relay 10A** | 3 | Optocoupler, controls solenoid valve |
| **Solenoid Valve 1/2" NC** | 3 | 12V DC, normally closed |

| Room ESP32 | Room | Flow GPIO | SSR GPIO | Relay GPIO | RFID Interface |
|------------|------|-----------|----------|------------|----------------|
| #1 | Bathroom | GPIO 26 | GPIO 25 | GPIO 13 | SPI (5,18,23,19,27) |
| #2 | Kitchen | GPIO 26 | GPIO 25 | GPIO 13 | SPI (5,18,23,19,27) |
| #3 | Shower | GPIO 26 | GPIO 25 | GPIO 13 | SPI (5,18,23,19,27) |

### Main ESP32

| Component | Qty | Key Specs |
|-----------|-----|-----------|
| **ESP32 Dev Module** | 1 | 38-pin, CP2102/CH340, 4 MB Flash |
| **ESP32 Expansion Board** | 1 | Screw terminals for all GPIOs |

| Component | Interface | Notes |
|-----------|-----------|-------|
| USB Serial | CDC/ACM | Debug / firmware upload only |
| Built-in LED | GPIO 2 | Status indication |

> **Note:** Main ESP32 has no SSR — each room controls its own solenoid valve independently via local leak rules.

---

## Arduino IDE Installation

### Method: `pip install arduino` (Recommended)

```bash
# 1. Update system
sudo apt update && sudo apt full-upgrade -y

# 2. Install pip if needed
sudo apt install -y python3-pip

# 3. Install Arduino IDE (includes Arduino CLI + IDE 2.x)
pip install arduino

# 4. Verify
arduino --version
# Arduino IDE 2.3.x
```

### Launch

```bash
# From terminal
arduino

# Or Applications Menu → Programming → Arduino IDE 2
```


---

## ESP32 Board Support Configuration

### 1. Open Preferences
**File → Preferences** (`Ctrl+,`)

### 2. Add Board Manager URL
In **Additional Boards Manager URLs**, paste:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Click **OK**.

> 📸 **Screenshot Placeholder:** *Arduino IDE Preferences dialog with ESP32 URL in Additional Boards Manager URLs field*

### 3. Install ESP32 Core
**Tools → Board → Boards Manager...** (`Ctrl+Shift+B`)
1. Search: **esp32**
2. Click **Install** on **"esp32 by Espressif Systems"** (latest version)
3. Wait for ~200 MB download (toolchain, libraries, examples)

> 📸 **Screenshot Placeholder:** *Boards Manager showing "esp32 by Espressif Systems" installing with progress bar*

### 4. Select Your Board
**Tools → Board → ESP32 Arduino → ESP32 Dev Module**

| Setting | Value |
|---------|-------|
| **Board** | ESP32 Dev Module |
| **Upload Speed** | 921600 |
| **CPU Frequency** | 240 MHz (WiFi/BT) |
| **Flash Mode** | QIO |
| **Flash Size** | 4 MB (32 Mb) |
| **Partition Scheme** | Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS) |
| **Core Debug Level** | None |
| **PSRAM** | Disabled |

> ⚠️ **Critical:** Selecting **ESP32 Dev Module** ensures correct pin mapping for 38-pin board. The GPIO pins in `config.h` (26, 25, 33, 32) match this board definition.

---

## ArduinoJson Library Setup

### Install via Library Manager

1. **Tools → Manage Libraries...** (`Ctrl+Shift+I`)
2. Search: **ArduinoJson**
3. Click **Install** on **"ArduinoJson by Benoit Blanchon"** (v7.x+)
4. Wait for installation

> 📸 **Screenshot Placeholder:** *Library Manager showing "ArduinoJson" by Benoit Blanchon installing*

### Version Note
- **ArduinoJson v7+** uses `JsonDocument` (replaces `StaticJsonDocument`/`DynamicJsonDocument`)
- Memory efficient, zero-copy parsing
- No separate `Firebase-ESP-Client` needed — we use plain USB Serial

---

## Firmware Architecture & File Structure

```
src/
├── water-meter.ino          # Main sketch (setup + loop)
├── config.h                 # ALL parameters (WiFi, sensors, timing)
├── config.example.h         # Template for git (copy to config.h)
├── sensor_manager.h         # Single ISR pulse counter + flow calc
├── flow_sensor.h            # Single sensor class
├── serial_comm.h            # USB Serial JSON sender/receiver
├── local_rules.h            # Offline leak detection
├── wifi_manager.h           # WiFi connect + auto-reconnect (for OTA)
├── data_logger.h            # SPIFFS fallback logging
├── ntp_sync.h               # NTP time sync for timestamps
├── ota_updater.h            # OTA firmware updates via WiFi
└── led_indicator.h          # Built-in LED (GPIO 2) status patterns
```

### Key Design Principles

- **Non-blocking loop** — `delay(100)` max, all operations poll-based
- **ISR-safe** — Pulse counters use `volatile` + `IRAM_ATTR` + 5ms debounce
- **Modular** — Each subsystem in own header, single responsibility
- **Fail-safe** — SPIFFS logging when USB disconnected
- **Observable** — LED patterns indicate state at a glance

---

## Main Loop & Sensor Management

### Main Loop (`water-meter.ino`)

```cpp
#include <Arduino.h>
#include "config.h"
#include "sensor_manager.h"
#include "serial_comm.h"
#include "local_rules.h"
#include "wifi_manager.h"
#include "data_logger.h"
#include "led_indicator.h"
#include "ota_updater.h"
#include "ntp_sync.h"

SensorManager sensorManager;
SerialComm serialComm;
LocalRules localRules;
WiFiManager wifiManager;
DataLogger dataLogger;
LEDIndicator ledIndicator;
OTAUpdater otaUpdater;
NTPSync ntpSync;

unsigned long lastSend = 0;
unsigned long lastStatus = 0;

void setup() {
    Serial.begin(921600);
    while (!Serial) delay(10);  // Wait for USB CDC
    
    // 1. Initialize sensors
    sensorManager.begin();
    
    // 2. Initialize WiFi (for OTA + NTP only)
    wifiManager.begin();
    
    // 3. Sync time via NTP
    ntpSync.begin();
    
    // 4. Initialize SPIFFS logger
    dataLogger.begin();
    
    // 5. Initialize OTA
    otaUpdater.begin();
    
    // 6. LED ready pattern
    ledIndicator.setPattern(LED_READY);
    
    Serial.println("{\"status\":\"ready\",\"device_id\":\"" DEVICE_ID "\",\"firmware\":\"" FIRMWARE_VERSION "\"}");
}

void loop() {
    // 1. Check WiFi + OTA (non-blocking)
    wifiManager.loop();
    otaUpdater.loop();
    
    // 2. Check for incoming commands from Firebase (via mobizt stream)
    if (Serial.available()) {
        serialComm.handleCommand();
    }
    
    // 3. Read all pulse counters (non-blocking)
    sensorManager.readAll();
    
    // 4. Periodic sensor data send (every 5 sec)
    if (millis() - lastSend >= SEND_INTERVAL_MS) {
        sendSensorData();
        lastSend = millis();
    }
    
    // 5. Local leak rules (runs every cycle)
    localRules.checkAll();
    
    // 6. Status LED update
    ledIndicator.update();
    
    // 7. Periodic status heartbeat (every 30 sec)
    if (millis() - lastStatus >= 30000) {
        serialComm.sendStatus();
        lastStatus = millis();
    }
    
    delay(100);  // Non-blocking cycle
}
```

### Sensor Manager (`sensor_manager.h`)

```cpp
// Manages 4 flow sensors with ISR pulse counting
class SensorManager {
public:
    void begin() {
        for (int i = 0; i < 4; i++) {
            pinMode(sensorPins[i], INPUT);
            attachInterruptArg(digitalPinToInterrupt(sensorPins[i]),
                               pulseISR, (void*)i, RISING);
        }
    }

    void readAll() {
        // Atomic read of pulse counters
        noInterrupts();
        for (int i = 0; i < 4; i++) {
            pulseCountLocal[i] = pulseCount[i];
            pulseCount[i] = 0;  // Reset for next interval
        }
        interrupts();
        
        // Calculate flow rate per sensor
        float intervalSec = SEND_INTERVAL_MS / 1000.0;
        for (int i = 0; i < 4; i++) {
            flowRate[i] = (pulseCountLocal[i] * 60.0) / (ppl[i] * intervalSec);
            totalVolume[i] += pulseCountLocal[i] / ppl[i];
        }
    }

    float getFlowRate(int index) { return flowRate[index]; }
    float getVolume(int index) { return totalVolume[index]; }
    uint32_t getPulses(int index) { return pulseCountLocal[index]; }

private:
    static void IRAM_ATTR pulseISR(void* arg) {
        int idx = (int)arg;
        uint32_t now = millis();
        if (now - lastPulseTime[idx] > 5) {  // 5ms debounce
            pulseCount[idx]++;
            lastPulseTime[idx] = now;
        }
    }

    const uint8_t sensorPin = PIN_SENSOR;
    float ppl = PPL_SENSOR;  // From config.h
    
    volatile uint32_t pulseCount[4] = {0};
    volatile uint32_t lastPulseTime[4] = {0};
    uint32_t pulseCountLocal[4] = {0};
    float flowRate[4] = {0};
    float totalVolume[4] = {0};
};
```

---

## USB Serial Communication

### Serial Protocol

**Baud Rate:** 921600  
**Format:** JSON Lines (newline-delimited JSON)  
**Encoding:** UTF-8

### Room → Main (ESP-NOW, every 5 sec)

```json
{"room_id":1,"ts":1703123456789,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456,"leak_alert":false}
```

### Main ESP32 → Firebase RTDB (WiFi + mobizt)

```json
{"device_id":"wmldad-main","ts":1703123456789,"rooms":[{"room_id":1,"flow_rate_lpm":2.34},{"room_id":2,"flow_rate_lpm":0.0},{"room_id":3,"flow_rate_lpm":1.12}]}
```

### Alert Frame (leak detected)

```json
{"device_id":"wmldad-main","ts":1703123456789,"type":"alert","level":"major_leak","room_id":2,"flow_rate_lpm":15.2,"message":"Major leak in Kitchen"}
```

### Command Frame (Firebase → Main ESP32 via mobizt stream)

```json
{"cmd":"shutoff","room_id":1}
{"cmd":"calibrate","room_id":2,"ppl":450}
{"cmd":"reset_counters"}
```

### Serial Communication Handler (`serial_comm.h`)

```cpp
#include <ArduinoJson.h>

class SerialComm {
public:
    void sendSensorData(const SensorManager& sensors, const char* deviceId) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = deviceId;
        doc["ts"] = millis();  // Use NTP time if available
        
        const char* sensorNames[4] = {"inlet", "bidet", "kitchen", "bathroom_shower"};
        const uint8_t sensorPin = PIN_SENSOR;
        
        for (int i = 0; i < 4; i++) {
            JsonObject s = doc[sensorNames[i]].to<JsonObject>();
            s["gpio"] = sensorPins[i];
            s["pulses"] = sensors.getPulses(i);
            s["flow_rate_lpm"] = round(sensors.getFlowRate(i) * 100) / 100.0;
            s["volume_ml"] = round(sensors.getVolume(i) * 1000);
        }
        
        serializeJson(doc, Serial);
        Serial.println();  // Newline delimiter
    }
    
    void sendAlert(int sensorIdx, const char* level, float flowRate, int duration, const char* msg) {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["ts"] = millis();
        doc["type"] = "alert";
        doc["level"] = level;
        doc["sensor"] = sensorIdx;
        doc["flow_rate_lpm"] = flowRate;
        doc["duration_sec"] = duration;
        doc["message"] = msg;
        
        serializeJson(doc, Serial);
        Serial.println();
    }
    
    void sendStatus() {
        StaticJsonDocument<256> doc;
        doc["device_id"] = DEVICE_ID;
        doc["ts"] = millis();
        doc["type"] = "status";
        doc["uptime_sec"] = millis() / 1000;
        doc["free_heap"] = ESP.getFreeHeap();
        doc["wifi_rssi"] = WiFi.RSSI();
        doc["sensors_ok"] = true;
        
        serializeJson(doc, Serial);
        Serial.println();
    }
    
    void handleCommand() {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() == 0) return;
        
        StaticJsonDocument<256> cmdDoc;
        DeserializationError err = deserializeJson(cmdDoc, line);
        if (err) return;
        
        const char* cmd = cmdDoc["cmd"];
        if (!cmd) return;
        
        StaticJsonDocument<128> resp;
        resp["cmd"] = cmd;
        resp["status"] = "ok";
        
        if (strcmp(cmd, "calibrate") == 0) {
            sensorManager.startCalibration();
            resp["msg"] = "Calibration mode: run known volume";
        } else if (strcmp(cmd, "reboot") == 0) {
            resp["msg"] = "Rebooting...";
            serializeJson(resp, Serial);
            Serial.println();
            ESP.restart();
        } else if (strcmp(cmd, "reset_counters") == 0) {
            for (int i = 0; i < 4; i++) sensorManager.resetVolume(i);
            resp["msg"] = "Counters reset";
        } else if (strcmp(cmd, "set_ppl") == 0) {
            int sensor = cmdDoc["sensor"] | 0;
            float ppl = cmdDoc["ppl"] | 450.0;
            sensorManager.setPPL(sensor, ppl);
            resp["msg"] = "PPL updated (not persistent)";
        }
        
        serializeJson(resp, Serial);
        Serial.println();
    }
};
```

---

## Local Leak Detection Rules (Offline Fallback)

Runs on ESP32 locally — critical for immediate alerting, even without WiFi.

```cpp
// local_rules.h — Runs on each room ESP32
// Handles RFID session + smart solenoid + leak detection:

class LocalRules {
public:
    void checkAll(float flowRate, float continuousTime) {
        unsigned long now = millis();
        
        // === SMART SOLENOID CONTROL ===
        // Only energize solenoid when water is actually flowing
        // This prevents solenoid overheating from continuous energization
        
        if (sessionActive) {
            if (flowRate > 0.01) {
                // Water flowing — keep solenoid ON
                lastFlowTime = now;
                digitalWrite(PIN_RELAY, HIGH);
            } else if (now - lastFlowTime > SOLENOID_OFF_DELAY_MS) {
                // No flow for N sec — turn solenoid OFF (prevent heating)
                digitalWrite(PIN_RELAY, LOW);
            }
            
            // Session timeout (no activity for X min)
            if (now - lastFlowTime > SESSION_TIMEOUT_MS) {
                endSession();
            }
        }
        
        // ============================================
        // === LEAK DETECTION RULES ===
        // ============================================
        
        // RULE 1: NO RFID + FLOW DETECTED = LEAK
        // No customer in room (no valid session) but water is flowing
        // This is the most common leak scenario: broken pipe, stuck valve, etc.
        if (!sessionActive && flowRate > 0.01) {
            triggerAlert("no_session_flow");  // Critical: unknown water flow
            emergencyShutoff();
        }
        
        // RULE 2: SESSION ENDED + FLOW CONTINUES = LEAK
        // Customer left (SSR OFF) but water still flowing
        // Solenoid should be closed — if flow persists, solenoid is stuck open
        if (!sessionActive && !solenoidOn && flowRate > 0.01) {
            triggerAlert("post_session_flow");  // Solenoid stuck open
            emergencyShutoff();
        }
        
        // RULE 3: SOLENOID OFF + FLOW DETECTED = LEAK
        // Solenoid is commanded OFF but flow sensor still reads water
        // Means solenoid is physically stuck open or pipe burst downstream
        if (!solenoidOn && flowRate > 0.01) {
            triggerAlert("solenoid_stuck_open");  // Critical hardware failure
            emergencyShutoff();
        }
        
        // RULE 4: CONTINUOUS FLOW > 30 MIN = STUCK VALVE / RUNNING TOILET
        // Even with active session, flowing for 30+ min is abnormal
        if (flowRate > 0.01 && continuousTime > 30 * 60) {
            triggerAlert("continuous_flow");
            emergencyShutoff();
        }
        
        // RULE 5: DRIP LEAK (0.1–0.5 L/min for > 5 MIN)
        // Slow, steady trickle — dripping faucet, loose fitting
        if (flowRate > 0.1 && flowRate < 0.5 && continuousTime > 5 * 60) {
            triggerAlert("drip_leak");
            emergencyShutoff();
        }
        
        // RULE 6: NIGHT FLOW (22:00–05:00) WITH NO SESSION = SUSPICIOUS
        // Water usage during sleeping hours with no authorized user
        if (!sessionActive && isNightTime() && flowRate > 0.01) {
            triggerAlert("night_flow");  // Possible unauthorized use or leak
            emergencyShutoff();
        }
    }
    
    void startSession() {
        sessionActive = true;
        lastFlowTime = millis();
        digitalWrite(PIN_SSR, HIGH);        // Room powered ON (electrical line)
        digitalWrite(PIN_RELAY, HIGH);      // Solenoid ON (water flows)
        solenoidOn = true;
    }
    
    void endSession() {
        sessionActive = false;
        digitalWrite(PIN_RELAY, LOW);       // Solenoid OFF first (stop water)
        digitalWrite(PIN_SSR, LOW);         // Room powered OFF
        solenoidOn = false;
    }
    
    void emergencyShutoff() {
        digitalWrite(PIN_RELAY, LOW);       // Solenoid OFF (stop water)
        digitalWrite(PIN_SSR, LOW);         // Room OFF
        sessionActive = false;
        solenoidOn = false;
    }

    void triggerAlert(const char* type) {
        dataLogger.logAlert(type, ROOM_ID);
        ledIndicator.setPattern(LED_FAST_BLINK);
        // Send via ESP-NOW to main ESP32 (with leak_alert flag)
    }
};
```

> **6 Leak Detection Rules:**
> 1. **No RFID + Flow** = No customer but water flowing → CRITICAL leak
> 2. **Session ended + Flow** = Customer left but water continues → Solenoid stuck open
> 3. **Solenoid OFF + Flow** = Valve commanded closed but flow persists → Hardware failure
> 4. **Continuous flow > 30 min** = Stuck valve / running toilet
> 5. **Drip (0.1–0.5 L/min) > 5 min** = Slow leak from loose fitting / dripping faucet
> 6. **Night flow (22:00–05:00) no session** = Suspicious unauthorized usage or leak
>
> **All leak rules trigger emergency shutoff:** SSR OFF + Solenoid OFF.
> **All alerts sent via ESP-NOW** to main ESP32 → Firebase RTDB → Next.js dashboard notification.

---

## Configuration (`config.h`)

```cpp
// config.h — ALL parameters in one place
// Copy config.example.h to config.h and fill in your values
// For ROOM ESP32s: set ROOM_ID and PIN_SENSOR
// For MAIN ESP32: set IS_MAIN = true and configure SSR

#pragma once

// ===== Device Identity =====
#define DEVICE_ID        "wmldad-room1"   // wmldad-room2, wmldad-room3, wmldad-main
#define FIRMWARE_VERSION "v4.0.0-espnow"
#define ROOM_ID          1                // 1=bathroom, 2=kitchen, 3=shower
#define IS_MAIN          false            // true for main ESP32

// ===== WiFi (main ESP32 connects to WiFi + Firebase) =====
#define WIFI_SSID        "YourWiFiSSID"
#define WIFI_PASSWORD    "YourWiFiPassword"

// ===== Firebase (main ESP32 only — mobizt Firebase-ESP-Client) =====
// Get these from Firebase Console → Project Settings → General
#define FIREBASE_API_KEY "YOUR_FIREBASE_API_KEY"
#define FIREBASE_DATABASE_URL "https://your-project.firebaseio.com"
// Optional: Firebase Auth (if RTDB rules require auth)
#define FIREBASE_USER_EMAIL "your@email.com"
#define FIREBASE_USER_PASSWORD "your-password"

// ===== Sensor Calibration (PPL = Pulses Per Liter) =====
// UPDATE AFTER BUCKET TEST!
#define PPL_SENSOR       450

// ===== Sensor Pin (all room ESP32s use GPIO 26) =====
#define PIN_SENSOR       26

// ===== Main ESP32 Peer MAC (for ESP-NOW) =====
// Update with your main ESP32's MAC address
#define MAIN_ESP_MAC     {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}

// ===== RFID Reader (MFRC522 SPI) =====
#define RFID_SS_PIN     5              // SDA/NSS
#define RFID_RST_PIN    27
// SPI: SCK=18, MOSI=23, MISO=19 (default ESP32 SPI)

// ===== SSR Relay Pin (per room — powers room electrical line) =====
#define PIN_SSR          25            // HIGH = room powered, LOW = room off

// ===== Solenoid Relay Pin (per room — 1-ch 10A relay controls solenoid) =====
#define PIN_RELAY        13            // HIGH = solenoid ON (water flows), LOW = shutoff
// Solenoid is ONLY energized when flow sensor detects water usage
// This prevents solenoid overheating from continuous energization
#define SOLENOID_OFF_DELAY_MS  5000    // Solenoid OFF after 5 sec no flow (prevent heating)
#define SESSION_TIMEOUT_MS  600000     // Session ends after 10 min no flow

// ===== Timing =====
#define SEND_INTERVAL_MS 5000            // ESP-NOW send every 5 sec
#define CALIBRATION_TIMEOUT_MS 300000    // 5 min calibration window

// ===== Local Leak Thresholds =====
#define CONTINUOUS_FLOW_MIN 30           // Minutes — stuck valve / running toilet
#define DRIP_MIN_RATE 0.1                // L/min
#define DRIP_MAX_RATE 0.5                // L/min
#define DRIP_MIN_TIME 5                  // Minutes — drip detection window
#define NIGHT_START_HOUR 22              // 10 PM — night flow detection starts
#define NIGHT_END_HOUR 5                 // 5 AM — night flow detection ends
#define MIN_FLOW_THRESHOLD 0.01          // L/min — minimum detectable flow

// ===== SPIFFS Logging =====
#define MAX_OFFLINE_LOGS 500
```

---

## Build, Upload & Verify

### 1. Verify (Compile)
**Sketch → Verify/Compile** (`Ctrl+R`)
- Should compile with 0 errors, ~250 KB flash usage

### 2. Select Port
**Tools → Port** → `/dev/ttyUSB0` (Linux) or `COMx` (Windows)

### 3. Upload
**Sketch → Upload** (`Ctrl+U`)

#### If Upload Fails (Bootloader Mode):
1. Hold **BOOT** button
2. Press and release **EN** (Reset) while holding BOOT
3. Release **BOOT**
4. Retry Upload (`Ctrl+U`)

### 4. Verify via Serial Monitor
**Tools → Serial Monitor** (`Ctrl+Shift+M`) → **921600 baud**

**Expected Output:**
```
// Room ESP32:
{"status":"ready","device_id":"wmldad-room1","firmware":"v4.0.0-espnow"}
{"room_id":1,"ts":123456,"pulses":127,"flow_rate_lpm":2.34,"volume_ml":456,"leak_alert":false}

// Main ESP32:
{"status":"ready","device_id":"wmldad-main","firmware":"v4.0.0-espnow"}
{"rooms":[{"room_id":1,"flow_rate_lpm":2.34},{"room_id":2,"flow_rate_lpm":0.0},{"room_id":3,"flow_rate_lpm":1.12}]}
```

---

## Sensor Calibration (Bucket Test)

> **Importance:** Accurate calibration is critical for leak detection. An uncalibrated sensor with ±10% error will trigger false positives or miss real leaks.

### Quick Calibration (Bucket Test)

1. **Prepare:** Get a 5L graduated container
2. **Connect:** Run water from faucet through the inlet sensor into the container
3. **Open:** Turn on faucet at medium flow
4. **Collect:** Exactly 5 liters
5. **Read:** Get pulse count from Serial Monitor (command: `status` or watch pulses field)
6. **Calculate:**
   ```
   Actual PPL = Total Pulse Count ÷ 5
   ```
7. **Update:** Change `PPL_SENSOR` in `config.h`
8. **Repeat** for each sensor (move sensor to each fixture line)

### Target
< 3% error per sensor. Typical YF-S201: 400–480 PPL.

---

## OTA Firmware Updates

Even though primary communication is USB Serial, WiFi + OTA allows remote firmware updates without physical access.

### OTA Updater (`ota_updater.h`)

```cpp
#include <ArduinoOTA.h>

class OTAUpdater {
public:
    void begin() {
        ArduinoOTA.setHostname(DEVICE_ID);
        ArduinoOTA.setPassword(OTA_PASSWORD);  // Define in config.h
        
        ArduinoOTA.onStart([]() {
            String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
            Serial.println("{\"ota\":\"start\",\"type\":\"" + type + "\"}");
        });
        ArduinoOTA.onEnd([]() {
            Serial.println("{\"ota\":\"end\"}");
        });
        ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
            Serial.printf("{\"ota\":\"progress\",\"pct\":%u}\n", (progress / (total / 100)));
        });
        ArduinoOTA.onError([](ota_error_t error) {
            Serial.printf("{\"ota\":\"error\",\"code\":%u}\n", error);
        });
        
        ArduinoOTA.begin();
    }
    
    void loop() {
        ArduinoOTA.handle();
    }
};
```

### Trigger OTA Update
```bash
# From any computer on same network
arduino-cli upload -p wmldad-main.local -b esp32:esp32:esp32 --port network
# Or use Arduino IDE: Tools → Port → Network ports → wmldad-main
```

---

## Troubleshooting Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| **No Serial output** | Baud rate mismatch | Set Serial Monitor to **921600** |
| **Upload fails** | Not in bootloader | Hold BOOT → Press EN → Release BOOT → Upload |
| **JSON parse errors** | Buffer overflow | Increase `StaticJsonDocument` size |
| **Flow rate reads 0** | Wrong GPIO pin | Verify pin in `config.h` matches wiring |
| **WiFi won't connect** | Wrong credentials | Check `WIFI_SSID`/`WIFI_PASSWORD` in `config.h` |
| **OTA not showing** | mDNS not working | Use IP address; install Bonjour on Windows |
| **SPIFFS not mounting** | Partition scheme | Use "Default 4MB with spiffs" partition |
| **Pulses too high/low** | Uncalibrated | Run bucket test, update PPL in `config.h` |

---

## LED Indicator Reference

| LED Pattern | Meaning |
|-------------|---------|
| Solid green | Normal operation, all OK |
| Blink green (1s) | WiFi connecting |
| Blink blue (fast) | Transmitting serial data |
| Solid yellow | Minor leak detected (alert) |
| Solid red | Major leak detected (critical) |
| Red flash | Emergency — urgent action needed |
| Blink white (3x + pause) | Successful data send |
| Blink red (5x + pause) | Send failed / error |
| Off | Deep sleep or no power |

---

## Checklist Before Panicking

- [ ] Is ESP32 getting power? (LED on?)
- [ ] Is USB cable a **data cable**? (not charge-only)
- [ ] Is Serial Monitor baud set to **921600**?
- [ ] Is the flow sensor arrow pointing **WITH** the water flow?
- [ ] Are WiFi SSID and password correct? (for OTA only)
- [ ] Is `PPL` calibrated for each sensor?
- [ ] Is ArduinoJson v7+ installed?
- [ ] Is board set to **ESP32 Dev Module**?