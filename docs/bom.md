# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** Main ESP32 (WiFi + 2 relays + 2 solenoids + calibrated flow sensor) ← ESP-NOW ← 3 Room ESP32s (RFID + leak detection flow sensor) → Firebase RTDB → Next.js on Vercel
> **Supplier Priority:** [Makerlab Electronics](https://shopee.ph/makerlabelectronics) → 4–5 alternatives  
> **Prices:** Estimated in Philippine Peso (₱), July 2026

---

## 1. Core Components

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 1 | **ESP32 38-Pin Dev Board** (ESP32 Dev Module, CP2102, WiFi + BLE) | **4** | ₱450 | **₱1,800** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=esp32%2038pin) |
| 2 | **ESP32 38-Pin Expansion Board** (screw terminals, labeled) | **4** | ₱180 | **₱720** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=esp32%20expansion%20board) |
| 3 | **MFRC522 RFID Reader Module** (SPI, 13.56MHz) | **3** | ₱80 | **₱240** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=mfrc522) |
| 4 | **RFID Card / Tag** (Mifare Classic 1K) | 3+ | ₱30 | ₱90 | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=mifare%20classic%201k) |
| 5 | **YF-S201 Water Flow Sensor** 1/2" thread, Hall-effect | **4** | ₱180 | **₱720** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=yf-s201%20flow%20sensor) |
| 6 | **1-ch Relay 10A** (optocoupler, for solenoid) | **2** | ₱50 | **₱100** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=relay%2010a%20optocoupler) |
| 7 | **Solenoid Valve 1/2" NC** (12V DC, normally closed) | **2** | ₱250 | **₱500** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=solenoid%20valve%2012v) |
| 8 | **Check Valve 1/2"** Brass (non-return) | 2 | ₱120 | ₱240 | [Shopee Hardware](https://shopee.ph/search?keyword=check%20valve%201%2F2%20brass) |
| 9 | **1/2" PPE Pipe** (Polypropylene, 4m length) | 2 | ₱150 | ₱300 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%201%2F2) |
| 10 | **1/2" PPE Pipe Fittings** (tees, elbows, couplers, nipples) | 1 set | ₱200 | ₱200 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%20fitting%20set) |
| 11 | **PTFE Thread Seal Tape** (Teflon, 10m roll) | 2 | ₱20 | ₱40 | [Shopee Hardware](https://shopee.ph/search?keyword=teflon%20tape) |
| 12 | **PPR Welding Machine** (for heat-fusing PPE joints) | 1 | ₱350 | ₱350 | [Shopee Hardware](https://shopee.ph/search?keyword=ppr%20welding%20machine) |

**Core Subtotal:** **₱5,300**

---

## 2. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 12 | **220V AC to 12V 5A Switching Power Supply** (S-60-12, 60W, LRS-50/60-12) | **4** | ₱280 | **₱1,120** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=12v%205a%20power%20supply) |
| 13 | **12V to 5V Buck Converter** (LM2596S, DC-DC Step-Down Module, USB output) | **4** | ₱65 | **₱260** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=lm2596s%20buck%20converter) |
| 14 | **USB to Micro USB Data Cable** (braided, 1m) | **4** | ₱120 | **₱480** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=micro%20usb%20cable) |
| 15 | **12V Male DC Power Jack Adapter** (5.5×2.1mm, screw terminal) | **4** | ₱9 | **₱36** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=dc%20power%20jack%20adapter) |

**Power Subtotal:** **₱1,896**

> **Note:** Each ESP32 (3 room + 1 main) has its own dedicated 12V 5A power supply, buck converter, and DC jack adapter. The DC jack adapter converts the PSU's screw terminal output to a 5.5×2.1mm barrel plug for the expansion board's power jack. The main ESP32 PSU powers 12V solenoid valves directly via 2CH relay.

---

## 3. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 15 | **Waterproof ABS Enclosure Box IP67** 175×125×75mm | **4** | ₱280 | **₱1,120** | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=waterproof%20enclosure%20ip67) |
| 16 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=cable%20gland%20pg9) |
| 17 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=heat%20shrink%20tube) |
| 18 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=cable%20tie) |
| 19 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/makerlabelectronics/search?keyword=m3%20standoff) |
| 20 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱550**

> **Note:** IP67 waterproof enclosure provides excellent protection for outdoor/wet environments. 175×125×75mm size fits ESP32, expansion board, buck converter, and room for cable management.

---

## Total Cost Summary

| Tier | Category | ₱ | Notes |
|------|----------|---|-------|
| **MVP** | 1 room (RFID + leak sensor) + main (2 solenoids + calibrated sensor) + PPE pipe | **~₱7,746** | Prove ESP-NOW + Firebase concept |
| **Standard** | 3 rooms + main + enclosure + PPE pipe + welding machine | **~₱7,746** | Full multi-room system |
| **Complete** | Standard + Firebase (free tier) + Vercel (free tier) | **~₱7,746** | Production-ready! |

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

### Room ESP32 (×3) — each gets RFID + flow sensor + SSR + relay + solenoid

**MFRC522 RFID (SPI):**
| RFID Pin | ESP32 Pin |
|----------|-----------|
| SDA (NSS) | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| RST | GPIO 21 |
| 3.3V | 3V (expansion board) |
| GND | GND |

**YF-S201 Flow Sensor (leak detection — uncalibrated):**
| Wire | Pin |
|------|-----|
| Red (VCC) | 5V |
| Black (GND) | GND |
| Yellow (Signal) | GPIO 26 |

**Fotek 40A SSR (room power — lights, fan, appliances):**
| Wire | Pin |
|------|-----|
| Input + | GPIO 27 |
| Input - | GND |
| Output 1 | 220V line |
| Output 2 | Appliance1st wire |
| Appliance 2nd wire | 220V line |

**1-ch Relay 10A (solenoid valve control):**
| Wire | Pin |
|------|-----|
| VCC | 5V |
| GND | GND |
| IN | GPIO 25 |
| COM | Solenoid + |
| NO | PSU + (12V) |
| Solenoid - | PSU - (directly) |

**Power:** Expansion board jack input → 12V switching PSU (accepts 6.5–16V)

### Main ESP32 — WiFi + Firebase + Centralized Control

**YF-S201 Flow Sensor (calibrated — for accurate metering):**
| Wire | Pin |
|------|-----|
| Red (VCC) | 5V (expansion board) |
| Black (GND) | GND |
| Yellow (Signal) | GPIO 34 |

**2CH Relay with Optocoupler (solenoid valve control):**
| Wire | Pin |
|------|-----|
| VCC | 5V (expansion board) |
| GND | GND |
| IN1 | GPIO 19 |
| IN2 | GPIO 18 |
| COM1 | Solenoid 1 + |
| COM2 | Solenoid 2 + |
| NO1 | PSU + (12V) |
| NO2 | PSU + (12V) |
| Solenoid 1 - | PSU - (directly) |
| Solenoid 2 - | PSU - (directly) |

**Reset Button (Arcade — WiFi credentials reset):**
| Wire | Pin |
|------|-----|
| Pin 1 | GND (expansion board) |
| Pin 2 | GPIO 27 |

**Power:** Expansion board jack input → 12V switching PSU (accepts 6.5–16V)

| Connection | Notes |
|------------|-------|
| WiFi | Connects to local network, pushes to Firebase RTDB |
| ESP-NOW | Receives RFID + leak alerts from room ESP32s |
| Power | 12V from PSU (ESP32 + sensors + solenoids) |

> **Architecture:** Main ESP32 is centralized before the rooms. It controls both solenoid valves via 2CH relay and reads the calibrated flow sensor. Room ESP32s handle RFID, flow sensor (leak detection), SSR (room power), and relay (solenoid) — they wirelessly report to main via ESP-NOW.
> **Note:** Solenoid valves are 12V NC (normally closed). Relay fires to OPEN valve (allow water flow). On leak detection, relay turns OFF → solenoid closes → water stops.