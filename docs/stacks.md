# Technology Stack — Water Meter with Leak Detection

> **Architecture:** Room ESP32s → ESP-NOW → Main ESP32 → WiFi → Firebase RTDB → Next.js on Vercel

---

## ESP32 Firmware Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | Arduino framework (esp32 core) | ≥ 2.0.x | Mature, well-documented, large ecosystem |
| **IDE** | Arduino IDE 2.x | Latest | ESP32 board support, Library Manager, Serial Monitor |
| **Language** | C++11/Arduino | — | Standard for ESP32 |
| **JSON** | [ArduinoJson](https://arduinojson.org/) | ≥ 7.x | Payload serialization |
| **ESP-NOW** | esp_now.h (built-in) | Built-in | Wireless room-to-main communication |
| **RFID** | [MFRC522](https://github.com/miguelbalboa/rfid) | ≥ 1.4.x | SPI RFID reader for usage tracking |
| **Firebase** | [Firebase-ESP-Client (mobizt)](https://github.com/mobizt/Firebase-ESP-Client) | ≥ 4.x | RTDB read/write/stream/callbacks via WiFi |
| **WiFi** | WiFi.h (Arduino) | Built-in | Station mode (for ESP-NOW + OTA) |
| **NTP** | NTPClient / configTime() | Built-in | Time sync for timestamped data |
| **OTA** | ArduinoOTA | Built-in | Over-the-air firmware updates |
| **SPIFFS** | SPIFFS (via LittleFS) | Built-in | Offline data logging |

### ArduinoJson Usage (v7+)

```cpp
#include <ArduinoJson.h>

JsonDocument doc;  // v7+ uses JsonDocument (replaces StaticJsonDocument)

doc["room_id"] = 1;
doc["ts"] = millis();
doc["pulses"] = 127;
doc["flow_rate_lpm"] = 2.34;
doc["volume_ml"] = 456;
doc["leak_alert"] = false;

serializeJson(doc, Serial);
Serial.println();  // Newline delimiter for JSON Lines
```

---

## ESP-NOW Communication Stack

| Layer | Technology | Protocol | Details |
|-------|------------|----------|---------|
| **Wireless** | ESP-NOW (Espressif) | 2.4 GHz | Low-latency, no WiFi router needed |
| **Range** | ~200m outdoor, ~30m indoor | — | Sufficient for room-to-main distance |
| **Payload** | Binary struct | — | Room ID, pulses, flow rate, volume, leak flag |
| **Frequency** | Every 5 sec | — | Matches USB serial interval |

---

## WiFi + Firebase Stack (Main ESP32)

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **WiFi** | WiFi.h (Arduino) | Built-in | Connect to local WiFi network |
| **Firebase SDK** | [Firebase-ESP-Client (mobizt)](https://github.com/mobizt/Firebase-ESP-Client) | ≥ 4.x | RTDB read/write/stream/callbacks |
| **Stream** | Firebase.onValue() | — | Real-time listener for commands from dashboard |
| **Callback** | Firebase.setCallback() | — | React to data changes on Firebase |
| **Auth** | Firebase ESP32 Auth | — | Optional: authenticate ESP32 with Firebase |

---

## Web Dashboard Stack (Next.js + Firebase)

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | [Next.js](https://nextjs.org/) ≥ 14.x | React framework with App Router |
| **Language** | TypeScript | Type safety |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Chart.js / Recharts | Real-time flow rate charts |
| **Auth** | [Firebase Authentication](https://firebase.google.com/docs/auth) | Email/password, Google sign-in |
| **Database** | [Firebase Realtime Database](https://firebase.google.com/docs/database) | Real-time data sync |
| **Firebase SDK** | firebase (JS SDK) | Client-side Firebase integration |
| **Hosting** | [Vercel](https://vercel.com/) | Auto-deploy from Git, serverless |
| **Real-time** | Firebase RTDB `onValue()` listener | Instant data updates in browser |

---

## Communication Summary

| Path | Protocol | Data Format | Frequency |
|------|----------|-------------|-----------|
| Sensor → Room ESP32 | Pulse (GPIO interrupt) | Rising edge | Continuous |
| Room ESP32 → Main ESP32 | ESP-NOW (wireless) | Binary payload | Every 5 sec |
| Main ESP32 → Firebase | WiFi + HTTPS | JSON (RTDB) | Every 5 sec |
| Firebase → Main ESP32 | WiFi + HTTPS | Callbacks/Streams | On command |
| Firebase → Next.js | WebSocket (RTDB) | Real-time sync | Instant |
| Main ESP32 → Relay → Solenoid | GPIO HIGH/LOW | Digital signal | Smart: ON when flow, OFF when idle |
| User → Dashboard | HTTPS | Internet | Firebase Auth login |

---

## Development Tools

| Tool | Purpose |
|------|---------|
| **Arduino IDE** | Build, upload, and debug ESP32 firmware (C++) |
| **Firebase Console** | Manage RTDB, Authentication, project settings |
| **Vercel Dashboard** | Deploy Next.js app, manage domains |
| **Serial Monitor** | ESP32 debug output (921600 baud) |
| **Git + GitHub** | Version control + Vercel auto-deploy |

---

## Stack Decision Matrix

| Requirement | Chosen | Alternatives Considered | Why This Won |
|-------------|--------|------------------------|--------------|
| **Web Framework** | **Next.js** | Flask, Django, Express | React ecosystem, Vercel auto-deploy, TypeScript |
| **Database** | **Firebase Realtime Database** | SQLite, PostgreSQL, Supabase | Real-time sync, no backend server, free tier |
| **Authentication** | **Firebase Authentication** | Custom JWT, Auth0, Clerk | Free, integrates with RTDB, Google sign-in |
| **Hosting** | **Vercel** | Netlify, AWS | Free tier, auto-deploy from Git, serverless |
| ESP32 38-pin ESP32 Dev Module | 30-pin, ESP32-C3, ESP8266 | More GPIOs, ESP-NOW support, 4 boards total |
| **mobizt Firebase-ESP-Client** | Direct ESP32 → Firebase, stream + callbacks | Custom backend | No extra hardware needed |

---

## Stack Summary

- **Room ESP32s ×3**: Arduino + ArduinoJson + MFRC522 RFID → 1 flow sensor (leak detection) each → ESP-NOW to main
- **Main ESP32 (centralized)**: ESP-NOW receiver + 2× relay (solenoid valves) + calibrated flow sensor
- **Main ESP32**: WiFi + mobizt Firebase-ESP-Client → pushes to Firebase RTDB directly
- **Firebase**: Realtime Database (data) + Authentication (user login)
- **Next.js on Vercel**: Web dashboard with real-time Firebase sync, deployed from Git
- ESP32 handles everything — sensors, RFID, relays, WiFi, Firebase