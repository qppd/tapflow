# Flowchart — Water Meter with Leak Detection (ESP-NOW + WiFi → Firebase)

## 1. Main System Flow (High-Level)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Start((Room ESP32 Start)) --> Init[Initialize Flow Sensor + ESP-NOW]
    Init --> MainLoop[Enter Main Loop]
    
    MainLoop --> ReadPulses[Read Pulse Counter via ISR]
    ReadPulses --> CalcFlow[Calculate Flow Rate + Volume]
    CalcFlow --> LocalRules[Apply Local Leak Rules]
    
    LocalRules --> Interval{Send Interval 5s?}
    Interval -->|Yes| SendESPNOW[Send Data via ESP-NOW to Main]
    Interval -->|No| MainLoop
    
    SendESPNOW --> MainLoop
```

> Room ESP32s transmit wirelessly via ESP-NOW. The main ESP32 aggregates and pushes to Firebase via WiFi.

</details>

---

## 2. Main ESP32 → Firebase Data Flow

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart LR
    subgraph Rooms["Room ESP32s x3"]
        RFID1[RFID] --> ESP1[Room 1]
        R1[Flow Sensor] --> ESP1
        ESP1 --> SSR1[SSR + Solenoid]
        ESP1 --> TX1[ESP-NOW TX]

        RFID2[RFID] --> ESP2[Room 2]
        R2[Flow Sensor] --> ESP2
        ESP2 --> SSR2[SSR + Solenoid]
        ESP2 --> TX2[ESP-NOW TX]

        RFID3[RFID] --> ESP3[Room 3]
        R3[Flow Sensor] --> ESP3
        ESP3 --> SSR3[SSR + Solenoid]
        ESP3 --> TX3[ESP-NOW TX]
    end

    subgraph Main["Main ESP32"]
        TX1 -.->|wireless| RX[ESP-NOW RX]
        TX2 -.->|wireless| RX
        TX3 -.->|wireless| RX
        RX --> AGG[Aggregate Room Data]
        AGG --> WIFI[WiFi + mobizt SDK]
    end

    subgraph Firebase["Firebase Cloud"]
        WIFI -.->|WiFi + mobizt| RTDB[(Realtime Database)]
        AUTH[Firebase Auth] --> NEXTJS
    end

    subgraph Vercel["Vercel Hosting"]
        RTDB --> NEXTJS[Next.js Dashboard]
    end
```

</details>

---

## 3. RFID Tap + Smart Solenoid Control

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Start((Customer Enters Room)) --> Tap[Tap RFID Card on MFRC522]
    Tap --> Read[Read Card UID]
    Read --> Valid{Valid Card for This Room?}
    
    Valid -->|No| Deny[LED Red Blink - Access Denied]
    Deny --> Start
    
    Valid -->|Yes| SSR_ON[SSR ON - Room Powered]
    SSR_ON --> SOL_ON[Solenoid ON - Water Flows]
    SOL_ON --> LED_G[LED Green - Session Active]
    
    LED_G --> FlowCheck{Flow Sensor Active?}
    
    FlowCheck -->|Flow Detected| SOL_STAY[Solenoid Stays ON]
    SOL_STAY --> FlowCheck
    
    FlowCheck -->|No Flow for N sec| SOL_OFF[Solenoid OFF - Prevent Overheating]
    SOL_OFF --> WaitFlow{Flow Detected?}
    
    WaitFlow -->|Yes| SOL_ON2[Solenoid ON Again]
    SOL_ON2 --> FlowCheck
    
    WaitFlow -->|Timeout X min| SSR_OFF[SSR OFF - Session Ends]
    SSR_OFF --> End((Room Powers Off))
    
    FlowCheck -->|Leak Detected| EMERGENCY[Emergency: SSR OFF + Solenoid OFF]
    EMERGENCY --> Alert[Send Alert via ESP-NOW]
    Alert --> End
```

</details>

> **Smart Solenoid Logic:** The solenoid is ONLY energized when the flow sensor detects water usage. When no flow is detected for N seconds, the solenoid automatically turns OFF to prevent overheating. It turns back ON when flow resumes. This allows continuous water use without damaging the solenoid.

---

## 4. Leak Detection Rules (6 Scenarios)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Check{Flow Detected?}
    Check -->|No Flow| OK[Normal - No Leak]
    Check -->|Flow > 0.01 L/min| Rule1{RFID Session Active?}
    
    Rule1 -->|No Session| LEAK1[LEAK: No Customer + Flow = Pipe Burst / Broken Fitting]
    Rule1 -->|Session Active| Rule2{Solenoid ON?}
    
    Rule2 -->|Solenoid OFF| LEAK2[LEAK: Solenoid Stuck Open = Hardware Failure]
    Rule2 -->|Solenoid ON| Rule3{Flow Duration?}
    
    Rule3 -->|Less than 30 min| Rule4{Flow Rate?}
    Rule3 -->|More than 30 min| LEAK3[LEAK: Continuous Flow = Stuck Valve / Running Toilet]
    
    Rule4 -->|0.1 - 0.5 L/min for 5+ min| LEAK4[LEAK: Drip = Loose Fitting / Dripping Faucet]
    Rule4 -->|Normal usage| Rule5{Night Time 22:00-05:00?}
    
    Rule5 -->|Yes + No Session| LEAK5[LEAK: Night Flow = Suspicious / Unauthorized Use]
    Rule5 -->|No| OK2[Normal Usage - Session Active]
    
    LEAK1 --> EMERGENCY[Emergency Shutoff: SSR OFF + Solenoid OFF]
    LEAK2 --> EMERGENCY
    LEAK3 --> EMERGENCY
    LEAK4 --> EMERGENCY
    LEAK5 --> EMERGENCY
    EMERGENCY --> ALERT[Send Alert via ESP-NOW to Main ESP32]
```

</details>

> **6 Leak Detection Scenarios:**
> 1. **No RFID + Flow** = No customer in room but water flowing → CRITICAL
> 2. **Solenoid OFF + Flow** = Valve closed but flow persists → Hardware failure
> 3. **Continuous flow > 30 min** = Stuck valve / running toilet
> 4. **Drip (0.1–0.5 L/min) > 5 min** = Slow leak from loose fitting
> 5. **Night flow (22:00–05:00) no session** = Suspicious unauthorized usage
> 6. **Session ended + Flow** = Customer left but water continues → Solenoid stuck open
>
> **All rules trigger emergency shutoff:** SSR OFF + Solenoid OFF + Alert sent to Firebase → Next.js dashboard.

---

## 5. ESP32 ISR Pulse Processing

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Pulse[/Pulse from Flow Sensor/] --> ISR[ISR Triggered]
    ISR --> Time[Read Millis]
    Time --> Debounce{Debounce Check dt greater than 5ms?}
    Debounce -->|Yes| Count[Increment Pulse Counter]
    Debounce -->|No| Ignore[Ignore - Bounce]
    Count --> Update[Update Last Pulse Time]
    Ignore --> Return[Return to Main Loop]
    Update --> Return
```

</details>

---

## 4. Firebase RTDB Data Structure

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Raw[/Raw Serial JSON/] --> Parse[Parse JSON]
    Parse --> Loop{For Each Fixture}
    Loop -->|Fixture 1-3| Extract[Extract Raw Metrics]
    Extract --> Compute[Compute Derived Metrics]
    
    Compute --> F1[flow_rate L/min]
    Compute --> F2[volume_ml]
    Compute --> F3[inlet_balance]
    Compute --> F4[continuous_flow_duration]
    
    F1 --> Rules[Local Leak Rules]
    F2 --> Rules
    F3 --> Rules
    F4 --> Rules
    
    Rules --> Decision{Leak Detected?}
```

</details>

---

## 5. Local Leak Detection Rules

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Features[/Sensor Readings/] --> Rule1{Inlet Balance OK?}
    Rule1 -->|Yes| Rule2{Continuous Flow > 30 min?}
    Rule1 -->|No| Alert1[Hidden Leak Alert]
    
    Rule2 -->|Yes| Alert2[Stuck Valve Alert]
    Rule2 -->|No| Rule3{Drip 0.1-0.5 L/min > 5 min?}
    
    Rule3 -->|Yes| Alert3[Drip Leak Alert]
    Rule3 -->|No| OK[Normal - No Leak]
    
    Alert1 --> Notify[In-App Notification]
    Alert2 --> Notify
    Alert3 --> Notify
    
    Notify --> Cmd[Send Command via Serial]
```

</details>

---

## 6. ESP32 Serial Command Execution

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Serial[/Serial Read JSON/] --> CmdType{Command Type?}
    
    CmdType -->|calibrate| CalStart[Start Calibration Routine]
    CmdType -->|reboot| Reboot[Reboot ESP32]
    CmdType -->|reset_counters| Reset[Reset Pulse Counters]
    CmdType -->|set_ppl| SetPPL[Update PPL Values]
    CmdType -->|sleep| Sleep[Deep Sleep Duration]
    
    CalStart --> CalStatus[Update Status and LED]
    Reboot --> CalStatus
    Reset --> CalStatus
    SetPPL --> CalStatus
    Sleep --> CalStatus
    
    CalStatus --> Ack[Send Acknowledgment JSON]
```

</details>

---

## 7. Local Leak Detection Rules (ESP32 Fallback)

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart TD
    Cycle[Every Read Cycle] --> Rule1[Rule 1: Hidden Leak]
    Rule1 --> Check1{Inlet Volume GT Sum Fixtures plus 10%?}
    Check1 -->|Yes| Alert1[Hidden Leak Alert]
    Check1 -->|No| OK1[Balance OK]
    
    Cycle --> Rule2[Rule 2: Continuous Flow]
    Rule2 --> Loop{For Each Fixture}
    Loop --> Check2{Pulse GT 0 for GT 30 min?}
    Check2 -->|Yes| Alert2[Stuck Valve or Running Toilet]
    Check2 -->|No| OK2[Fixture OK]
    
    Cycle --> Rule3[Rule 3: Drip Detection]
    Loop2{For Each Fixture} --> Check3{Flow 0.1-0.5 L/min for GT 5 min?}
    Check3 -->|Yes| Alert3[Drip Leak Suspected]
    Check3 -->|No| OK3[No Drip]
    
    Alert1 --> SerialAlert[Send Alert via Serial]
    Alert2 --> SerialAlert
    Alert3 --> SerialAlert
```

</details>

---

## 8. Full System Data Flow

> Mermaid-based diagram (SVG export removed; source below)

<details>
<summary><b> Mermaid Source</b> (click to expand)</summary>

```mermaid
flowchart LR
    %% Physical Layer
    Water[/Water Flow/]:::physical --> Sensor[YF-S201 Flow Sensor]:::physical
    Sensor --> Pulse[/Pulse Signal/]:::physical
    
    %% Firmware Layer
    Pulse --> ISR[ISR Pulse Counter]:::firmware
    ISR --> Debounce[Debounce 5ms]:::firmware
    Debounce --> Calc[Calculate Flow and Volume]:::firmware
    Calc --> LocalRules[Local Leak Rules]:::firmware
    Calc --> SerialOut[USB Serial Output]:::firmware
    LocalRules --> SerialOut
    
    %% USB Layer
    SerialOut -->|USB CDC/ACM 921600 baud| USB[USB Cable]:::usb
    
    %% Firebase Layer
    SerialOut -->|WiFi + mobizt| Firebase[Firebase RTDB]:::backend
    Firebase --> Parser[JSON Parser]:::backend
    Parser --> LocalRules[Local Leak Rules]:::backend
    LocalRules --> AlertEngine[Alert Engine]:::backend
    AlertEngine --> Notify[In-App Notification]:::user
    AlertEngine --> FB[(Firebase RTDB)]:::backend
    
    %% User Layer
    FB --> Dashboard[Next.js Dashboard on Vercel]:::user
    USB -->|Commands| CmdHandler[Command Handler]:::firmware
    
    classDef physical fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef firmware fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef usb fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef user fill:#fffde7,stroke:#f9a825,stroke-width:2px
```

</details>