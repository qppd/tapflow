# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** Main ESP32 (WiFi + 2 relays + 2 solenoids + calibrated flow sensor) ← ESP-NOW ← 3 Room ESP32s (RFID + leak detection flow sensor) → Firebase RTDB → Next.js on Vercel
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) → 4–5 alternatives  
> **Prices:** Estimated in Philippine Peso (₱), July 2026

---

## 1. Core Components

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 1 | **ESP32 38-Pin Dev Board** (ESP32 Dev Module, CP2102, WiFi + BLE) | **4** | ₱450 | **₱1,800** | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%2038pin%20makerlab) |
| 2 | **ESP32 38-Pin Expansion Board** (screw terminals, labeled) | **4** | ₱180 | **₱720** | [Makerlab Shopee](https://shopee.ph/search?keyword=esp32%20expansion%20board%20makerlab) |
| 3 | **MFRC522 RFID Reader Module** (SPI, 13.56MHz) | **3** | ₱80 | **₱240** | [Makerlab Shopee](https://shopee.ph/search?keyword=mfrc522%20rfid%20makerlab) |
| 4 | **RFID Card / Tag** (Mifare Classic 1K) | 3+ | ₱30 | ₱90 | [Makerlab Shopee](https://shopee.ph/search?keyword=mifare%20classic%201k%20card) |
| 5 | **YF-S201 Water Flow Sensor** 1/2" thread, Hall-effect | **4** | ₱180 | **₱720** | [Makerlab Shopee](https://shopee.ph/search?keyword=yf-s201%20flow%20sensor%20makerlab) |
| 6 | **1-ch Relay 10A** (optocoupler, for solenoid) | **2** | ₱50 | **₱100** | [Makerlab Shopee](https://shopee.ph/search?keyword=1ch%20relay%2010a%20optocoupler%20makerlab) |
| 7 | **Solenoid Valve 1/2" NC** (12V DC, normally closed) | **2** | ₱250 | **₱500** | [Makerlab Shopee](https://shopee.ph/search?keyword=solenoid%20valve%2012v%201%2F2%20nc) |
| 8 | **Check Valve 1/2"** Brass (non-return) | 2 | ₱120 | ₱240 | [Makerlab Shopee](https://shopee.ph/search?keyword=check%20valve%201%2F2%20makerlab) |
| 9 | **1/2" PPE Pipe** (Polypropylene, 4m length) | 2 | ₱150 | ₱300 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%201%2F2%20makerlab) |
| 10 | **1/2" PPE Pipe Fittings** (tees, elbows, couplers, nipples) | 1 set | ₱200 | ₱200 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%20fitting%20set) |
| 11 | **PTFE Thread Seal Tape** (Teflon, 10m roll) | 2 | ₱20 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=teflon%20tape%20makerlab) |
| 12 | **PPR Welding Machine** (for heat-fusing PPE joints) | 1 | ₱350 | ₱350 | [Shopee Hardware](https://shopee.ph/search?keyword=ppr%20welding%20machine%20makerlab) |

**Core Subtotal:** **₱5,300**

---

## 2. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 12 | **220V AC to 12V 5A Switching Power Supply** (S-60-12, 60W, LRS-50/60-12) | **4** | ₱280 | **₱1,120** | [Shopee](https://shopee.ph/Switching-Power-Supply-(S-60-12)-12V-5A-60W-LRS-50-5V-10A-12V-4.2A-24V-2.1A-50W-i.18252381.363361010?extraParams=%7B%22display_model_id%22%3A164466543878%2C%22model_selection_logic%22%3A3%7D) |
| 13 | **12V to 5V Buck Converter** (LM2596S, DC-DC Step-Down Module, USB output) | **4** | ₱65 | **₱260** | [Shopee](https://shopee.ph/24V-12V-to-5V-Buck-Converter-USB-Mobile-Phone-DC-DC-Step-Down-Module-LM2596S-HW-688-HCW-P715-i.18252381.1920327681?extraParams=%7B%22display_model_id%22%3A80023951201%2C%22model_selection_logic%22%3A3%7D) |
| 14 | **USB to Micro USB Data Cable** (braided, 1m) | **4** | ₱120 | **₱480** | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |

**Power Subtotal:** **₱1,860**

> **Note:** Each ESP32 (3 room + 1 main) has its own dedicated 12V 5A power supply and buck converter. The main ESP32 PSU powers 12V solenoid valves directly, while the LM2596S buck converter steps down 12V → 5V for the ESP32 and sensors.

---

## 3. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 15 | **Waterproof ABS Enclosure Box IP67** 175×125×75mm | **4** | ₱280 | **₱1,120** | [Shopee](https://shopee.ph/Waterproof-Plastic-Enclosure-Box-Electronic-IP67-Project-Instrument-Case-Electrical-Project-Box-ABS-Outdoor-Junction-Box-Housing-i.291988242.6261564475?extraParams=%7B%22display_model_id%22%3A22547988641%2C%22model_selection_logic%22%3A3%7D) |
| 16 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 17 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 18 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 19 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 20 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱550**

> **Note:** IP67 waterproof enclosure provides excellent protection for outdoor/wet environments. 175×125×75mm size fits ESP32, expansion board, buck converter, and room for cable management.

---

## 4. Raspberry Pi (NOT NEEDED)

> **No Raspberry Pi required!** Main ESP32 connects to Firebase directly via WiFi using mobizt Firebase-ESP-Client.

---

## Already Purchased (Not in BOM)

| Item | Qty | Notes |
|------|-----|-------|
| ~~Raspberry Pi 4/5~~ | ~~1~~ | ~~No longer needed — ESP32 handles everything~~ |

---

## Total Cost Summary

| Tier | Category | ₱ | Notes |
|------|----------|---|-------|
| **MVP** | 1 room (RFID + leak sensor) + main (2 solenoids + calibrated sensor) + PPE pipe | **~₱7,710** | Prove ESP-NOW + Firebase concept |
| **Standard** | 3 rooms + main + enclosure + PPE pipe + welding machine | **~₱7,710** | Full multi-room system |
| **Complete** | Standard + Firebase (free tier) + Vercel (free tier) | **~₱7,710** | Production-ready — no RPi needed! |

> **Note:** No Raspberry Pi needed — ESP32 connects to Firebase directly via WiFi. Firebase free tier and Vercel free tier keep costs at zero for hosting.

---

## Recommended Seller: Makerlab Electronics

| Platform | Store | Rating | Notes |
|----------|-------|--------|-------|
| **Shopee** | [Makerlab Electronics](https://shopee.ph/makerlabelectronics) | 4.9 | Fast shipping, good stock |
| **Lazada** | [Makerlab Electronics](https://www.lazada.com.ph/shop/makerlab-electronics/) | 4.8 | Wider payment options |

### Alternative Sellers (4–5)

| Store | Platform | Rating | Specializes In |
|-------|----------|--------|---------------|
| [e-Gizmo](https://shopee.ph/e-gizmo) | Shopee | 4.8 | Arduino/ESP32 parts, sensors |
| [Cytron Technologies](https://shopee.ph/cytrontechnologies) | Shopee | 4.9 | Robotics, IoT, sensors |
| [DIY Electronics](https://shopee.ph/diy_electronics) | Shopee | 4.7 | General electronics |
| [Handson Technology](https://www.lazada.com.ph/shop/handsome-technology/) | Lazada | 4.8 | Sensors, power supplies |

---

## Wiring Summary

### Room ESP32 (×3) — each gets RFID + flow sensor (leak detection only)

**MFRC522 RFID (SPI):**
| RFID Pin | ESP32 Pin |
|----------|-----------|
| SDA (NSS) | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| RST | GPIO 27 |
| VCC | 3.3V |
| GND | GND |

**YF-S201 Flow Sensor (leak detection — uncalibrated):**
| Wire | Pin |
|------|-----|
| Red (VCC) | 5V |
| Black (GND) | GND |
| Yellow (Signal) | GPIO 26 |

### Main ESP32 — WiFi + Firebase + Centralized Control

**YF-S201 Flow Sensor (calibrated — for accurate metering):**
| Wire | Pin |
|------|-----|
| Red (VCC) | 5V |
| Black (GND) | GND |
| Yellow (Signal) | GPIO 34 |

**1-ch Relay 10A — Solenoid Valve 1:**
| Wire | Pin |
|------|-----|
| Relay IN | GPIO 25 |
| Relay VCC | 5V |
| Relay GND | GND |
| Relay OUT+ | Solenoid 1 12V NC (+) |
| Relay OUT- | 12V PSU (-) |

**1-ch Relay 10A — Solenoid Valve 2:**
| Wire | Pin |
|------|-----|
| Relay IN | GPIO 13 |
| Relay VCC | 5V |
| Relay GND | GND |
| Relay OUT+ | Solenoid 2 12V NC (+) |
| Relay OUT- | 12V PSU (-) |

| Connection | Notes |
|------------|-------|
| WiFi | Connects to local network, pushes to Firebase RTDB |
| ESP-NOW | Receives RFID + leak alerts from room ESP32s |
| Power | 5V from buck converter (ESP32 + sensors) + 12V from PSU (solenoids) |

> **Architecture:** Main ESP32 is centralized before the rooms. It controls both solenoid valves and reads the calibrated flow sensor. Room ESP32s only handle RFID and leak detection — they wirelessly report to main via ESP-NOW.
> **Note:** Solenoid valves are 12V NC (normally closed). Relay fires to OPEN valve (allow water flow). On leak detection, relay turns OFF → solenoid closes → water stops.