# Bill of Materials (BOM) — Water Meter with Leak Detection

> **System:** 3 room ESP32s (RFID + flow sensor + SSR + solenoid) → ESP-NOW → Main ESP32 → WiFi → Firebase RTDB → Next.js on Vercel
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
| 5 | **YF-S201 Water Flow Sensor** 1/2" thread, Hall-effect | **3** | ₱180 | **₱540** | [Makerlab Shopee](https://shopee.ph/search?keyword=yf-s201%20flow%20sensor%20makerlab) |
| 6 | **Fotek 40A SSR** (solid-state relay, DC control) | **3** | ₱120 | **₱360** | [Makerlab Shopee](https://shopee.ph/search?keyword=fotek%2040a%20ssr%20makerlab) |
| 7 | **1-ch Relay 10A** (optocoupler, for solenoid) | **3** | ₱50 | **₱150** | [Makerlab Shopee](https://shopee.ph/search?keyword=1ch%20relay%2010a%20optocoupler%20makerlab) |
| 8 | **Solenoid Valve 1/2" NC** (12V DC, normally closed) | **3** | ₱250 | **₱750** | [Makerlab Shopee](https://shopee.ph/search?keyword=solenoid%20valve%2012v%201%2F2%20nc) |
| 8 | **Check Valve 1/2"** Brass (non-return) | 3 | ₱120 | ₱360 | [Makerlab Shopee](https://shopee.ph/search?keyword=check%20valve%201%2F2%20makerlab) |
| 9 | **1/2" PPE Pipe** (Polypropylene, 4m length) | 2 | ₱150 | ₱300 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%201%2F2%20makerlab) |
| 10 | **1/2" PPE Pipe Fittings** (tees, elbows, couplers, nipples) | 1 set | ₱200 | ₱200 | [Shopee Hardware](https://shopee.ph/search?keyword=ppe%20pipe%20fitting%20set) |
| 11 | **PTFE Thread Seal Tape** (Teflon, 10m roll) | 2 | ₱20 | ₱40 | [Makerlab Shopee](https://shopee.ph/search?keyword=teflon%20tape%20makerlab) |
| 12 | **PPR Welding Machine** (for heat-fusing PPE joints) | 1 | ₱350 | ₱350 | [Shopee Hardware](https://shopee.ph/search?keyword=ppr%20welding%20machine%20makerlab) |

**Core Subtotal:** **₱2,080**

---

## 2. Prototyping & Wiring

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 8 | **Perf Board 20×80mm** (for permanent soldering) | **4** | ₱25 | **₱100** | [Makerlab Shopee](https://shopee.ph/search?keyword=perf%20board%2020x80%20makerlab) |
| 9 | **JST-XH 3-pin Male** (for flow sensor side) | 3 | ₱10 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%203pin%20male%20makerlab) |
| 10 | **JST-XH 3-pin Female** (for board/perf board side) | 3 | ₱12 | ₱36 | [Makerlab Shopee](https://shopee.ph/search?keyword=jst-xh%203pin%20female%20makerlab) |
| 11 | **Terminal Block 2-pin Blue** (5mm pitch, power input) | 4 | ₱15 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=terminal%20block%202pin%20blue%20makerlab) |

**Wiring Subtotal:** **₱163**

> **Note:** JST-XH connectors are purchased **pre-crimped / ready-to-use** — no crimp kit or crimping tool needed. Just solder the female connectors to the perf board and plug in the sensor cables.

---

## 3. Power Supply

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 12 | **220V AC to 12V 5A Switching Power Supply** (S-60-12, 60W, LRS-50/60-12) | 1 | ₱280 | ₱280 | [Shopee](https://shopee.ph/Switching-Power-Supply-(S-60-12)-12V-5A-60W-LRS-50-5V-10A-12V-4.2A-24V-2.1A-50W-i.18252381.363361010?extraParams=%7B%22display_model_id%22%3A164466543878%2C%22model_selection_logic%22%3A3%7D) |
| 13 | **12V to 5V Buck Converter** (LM2596S, DC-DC Step-Down Module, USB output) | 1 | ₱65 | ₱65 | [Shopee](https://shopee.ph/24V-12V-to-5V-Buck-Converter-USB-Mobile-Phone-DC-DC-Step-Down-Module-LM2596S-HW-688-HCW-P715-i.18252381.1920327681?extraParams=%7B%22display_model_id%22%3A80023951201%2C%22model_selection_logic%22%3A3%7D) |
| 14 | **USB to Micro USB Data Cable** (braided, 1m) | 1 | ₱120 | ₱120 | [Makerlab Shopee](https://shopee.ph/search?keyword=micro%20usb%20cable%20makerlab) |

**Power Subtotal:** **₱465**

> **Note:** The 12V 5A supply powers both the buck converter (for ESP32 + sensors at 5V) and can directly power 12V components if needed. The LM2596S buck converter steps down 12V → 5V for the ESP32 and flow sensors.

---

## 4. Enclosure & Mounting

| # | Item | Qty | Unit (₱) | Total (₱) | Link |
|---|------|-----|----------|-----------|------|
| 15 | **Waterproof ABS Enclosure Box IP67** 175×125×75mm | **4** | ₱280 | **₱1,120** | [Shopee](https://shopee.ph/Waterproof-Plastic-Enclosure-Box-Electronic-IP67-Project-Instrument-Case-Electrical-Project-Box-ABS-Outdoor-Junction-Box-Housing-i.291988242.6261564475?extraParams=%7B%22display_model_id%22%3A22547988641%2C%22model_selection_logic%22%3A3%7D) |
| 16 | **Cable Glands** PG9 / PG11 (waterproof entry) | 6 | ₱15 | ₱90 | [Shopee Hardware](https://shopee.ph/search?keyword=cable%20gland%20pg9) |
| 17 | **Heat Shrink Tube Set** (assorted sizes) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=heat%20shrink%20tube%20makerlab) |
| 18 | **Cable Ties** 100mm (100pc) | 1 | ₱30 | ₱30 | [Makerlab Shopee](https://shopee.ph/search?keyword=cable%20tie%20makerlab) |
| 19 | **M3 Screws + Standoffs Kit** (PCB mounting) | 1 | ₱60 | ₱60 | [Makerlab Shopee](https://shopee.ph/search?keyword=m3%20standoff%20makerlab) |
| 20 | **Double-sided Tape / Velcro** (mounting sensors) | 1 | ₱30 | ₱30 | [Shopee Hardware](https://shopee.ph/search?keyword=double%20sided%20tape%20heavy%20duty) |

**Enclosure Subtotal:** **₱550**

> **Note:** IP67 waterproof enclosure provides excellent protection for outdoor/wet environments. 175×125×75mm size fits ESP32, expansion board, buck converter, terminal block, and perf board with room for cable management.

---

## 5. Raspberry Pi (NOT NEEDED)

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
| **MVP** | 1 room (RFID + sensor + SSR + solenoid) + main + PPE pipe | **~₱2,905** | Prove ESP-NOW + Firebase concept |
| **Standard** | 3 rooms + main + enclosure + PPE pipe + welding machine | **~₱9,361** | Full multi-room system |
| **Complete** | Standard + Firebase (free tier) + Vercel (free tier) | **~₱9,361** | Production-ready — no RPi needed! |

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

### Room ESP32 (×3) — each gets RFID + flow sensor + SSR + solenoid

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

**YF-S201 Flow Sensor:**
| Wire | Pin |
|------|-----|
| Red (VCC) | 5V |
| Black (GND) | GND |
| Yellow (Signal) | GPIO 26 |

**Fotek 40A SSR (room power):**
| Wire | Pin |
|------|-----|
| SSR CTRL | GPIO 25 |
| SSR VCC | 5V |
| SSR GND | GND |

**1-ch Relay 10A (solenoid valve):**
| Wire | Pin |
|------|-----|
| Relay IN | GPIO 13 |
| Relay VCC | 5V |
| Relay GND | GND |
| Relay OUT+ | Solenoid 12V NC (+) |
| Relay OUT- | 12V PSU (-) |### Main ESP32 — WiFi + Firebase

| Connection | Notes |
|------------|-------|
| WiFi | Connects to local network, pushes to Firebase RTDB |
| Power | 5V from buck converter or USB |

> **ESP-NOW:** No wiring between room ESP32s and main ESP32 — communication is wireless via ESP-NOW protocol.
> **Note:** Solenoid valves are 12V NC (normally closed). SSR fires to OPEN valve (allow water flow). On leak detection, SSR turns OFF → solenoid closes → water stops.