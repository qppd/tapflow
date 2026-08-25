# Leak Detection Advanced Guide — TapFlow

> **Purpose:** Comprehensive leak detection system — 6 core rules, advanced detection methods, mass balance analysis, and combined anomaly+leak logic.
> **Builds on:** [anomaly-detection-guide.md](./anomaly-detection-guide.md), [block-diagram.md](./block-diagram.md) (6 rules reference)
> **Feeds into:** [module-integration-guide.md](./module-integration-guide.md), [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md)

---

## Table of Contents

1. [Detection Philosophy](#1-detection-philosophy)
2. [6 Core Leak Detection Rules](#2-6-core-leak-detection-rules)
3. [Advanced Detection Methods](#3-advanced-detection-methods)
4. [Mass Balance Leak Detection](#4-mass-balance-leak-detection)
5. [Pulse Pattern Analysis](#5-pulse-pattern-analysis)
6. [Combined Anomaly + Leak Logic](#6-combined-anomaly--leak-logic)
7. [Response Matrix](#7-response-matrix)
8. [False Positive Reduction](#8-false-positive-reduction)
9. [Firebase RTDB Structure](#9-firebase-rtdb-structure)
10. [ESP32 Module: `leak_detector.h`](#10-esp32-module-leak_detectorh)
11. [Configuration Thresholds](#11-configuration-thresholds)
12. [Validation Checklist](#12-validation-checklist)

---

## 1. Detection Philosophy

Leak detection in TapFlow operates on **three principles:**

```
┌─────────────────────────────────────────────────────────────────┐
│  PRINCIPLE 1: REDUNDANCY                                        │
│  ─────────────────────────────────────────────────────────────  │
│  Same event detected from multiple angles:                      │
│    • Room ESP32 (local flow rules)                              │
│    • Main ESP32 (cross-room mass balance)                       │
│    • Firebase Cloud (historical trends)                         │
│  Any 2 of 3 confirming = high confidence alert                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PRINCIPLE 2: LAYERED RESPONSE                                  │
│  ─────────────────────────────────────────────────────────────  │
│  Response scales with severity:                                 │
│    • Log only      → suspicious pattern, no action needed       │
│    • Warning       → investigate, notify user                   │
│    • Alert         → recommend shutoff                          │
│    • Emergency     → automatic shutoff + all notifications      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PRINCIPLE 3: CONTEXT-AWARE                                     │
│  ─────────────────────────────────────────────────────────────  │
│  Same flow reading means different things depending on:         │
│    • RFID session state (authorized vs. unauthorized)           │
│    • Solenoid valve state (commanded ON vs. OFF)                │
│    • Time of day (normal hours vs. night)                       │
│    • Duration (brief use vs. continuous)                        │
│  Detection rules combine ALL context, not just flow rate.       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 6 Core Leak Detection Rules

> These rules run on **every room ESP32** in `local_rules.h`. They are the primary defense and work **offline** (no WiFi needed).

### Rule 1: No RFID + Flow = CRITICAL LEAK

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 1: NO SESSION + FLOW DETECTED                             │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    sessionActive == false                                        │
│    AND flowRate > MIN_FLOW_THRESHOLD (0.01 L/min)              │
│    AND持续 for > DEBOUNCE_TIME (3 sec)                         │
│                                                                 │
│  Meaning: No authorized customer in room, but water is flowing. │
│                                                                 │
│  Possible Causes:                                               │
│    • Broken pipe or burst fitting                               │
│    • Stuck solenoid valve (failed open)                         │
│    • Upstream valve failure                                     │
│    • Unauthorized water access                                  │
│                                                                 │
│  Response:                                                      │
│    severity = EMERGENCY                                         │
│    action = emergencyShutoff()                                  │
│    alert = "no_session_flow"                                    │
│    → SSR OFF + Solenoid OFF                                     │
│    → Send alert via ESP-NOW to main ESP32                       │
│    → Log to SPIFFS + Firebase                                   │
│                                                                 │
│  Confidence: HIGH (95%+) — this is almost certainly a leak     │
│  False Positive Rate: < 1% (only if RFID reader malfunction)   │
└─────────────────────────────────────────────────────────────────┘
```

**Pseudocode:**

```cpp
if (!sessionActive && flowRate > MIN_FLOW_THRESHOLD) {
    noFlowDebounce++;
    if (noFlowDebounce > DEBOUNCE_CYCLES) {  // 3 sec at 100ms/cycle
        triggerLeakAlert("no_session_flow", SEVERITY_EMERGENCY);
        emergencyShutoff();
    }
} else {
    noFlowDebounce = 0;
}
```

---

### Rule 2: Session Ended + Flow Continues = SOLENOID STUCK

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 2: POST-SESSION FLOW                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    sessionActive == false (session ended)                       │
│    AND solenoidOn == false (solenoid commanded OFF)             │
│    AND flowRate > MIN_FLOW_THRESHOLD (0.01 L/min)              │
│    AND持续 for > DEBOUNCE_TIME (3 sec)                         │
│                                                                 │
│  Meaning: Customer left, solenoid is OFF, but water still flows.│
│                                                                 │
│  Possible Causes:                                               │
│    • Solenoid physically stuck open (mechanical failure)        │
│    • SSR contacts welded shut (relay failure)                   │
│    • Pipe burst downstream of solenoid                          │
│                                                                 │
│  Response:                                                      │
│    severity = EMERGENCY                                         │
│    action = emergencyShutoff()                                  │
│    alert = "post_session_flow"                                  │
│    → SSR OFF + Solenoid OFF (redundant — already OFF)          │
│    → Log hardware failure                                       │
│    → Send alert via ESP-NOW                                     │
│                                                                 │
│  Confidence: VERY HIGH (98%+) — solenoid commanded OFF but     │
│  flow persists = hardware failure                               │
│  False Positive Rate: < 0.5%                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Rule 3: Solenoid OFF + Flow = HARDWARE FAILURE

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 3: SOLENOID OFF + FLOW                                    │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    solenoidOn == false                                          │
│    AND flowRate > MIN_FLOW_THRESHOLD (0.01 L/min)              │
│    AND持续 for > DEBOUNCE_TIME (3 sec)                         │
│                                                                 │
│  Meaning: Solenoid is commanded closed, but flow sensor reads   │
│  water. Valve is physically stuck open or pipe burst.           │
│                                                                 │
│  Possible Causes:                                               │
│    • Solenoid stuck open (debris, corrosion)                    │
│    • SSR welded contacts (relay keeps passing current)          │
│    • Pipe burst between solenoid and flow sensor                │
│    • Flow sensor error (false positive)                         │
│                                                                 │
│  Response:                                                      │
│    severity = EMERGENCY                                         │
│    action = emergencyShutoff() + retry shutoff (pulse relay)   │
│    alert = "solenoid_stuck_open"                                │
│    → Attempt rapid relay toggle (3x OFF-ON-OFF)                │
│    → If flow persists after retry: hardware alert               │
│    → Send alert via ESP-NOW                                     │
│                                                                 │
│  Confidence: HIGH (90%+) — may need sensor validation          │
│  False Positive Rate: ~2% (sensor noise on startup)            │
└─────────────────────────────────────────────────────────────────┘
```

**Pseudocode:**

```cpp
if (!solenoidOn && flowRate > MIN_FLOW_THRESHOLD) {
    stuckDebounce++;
    if (stuckDebounce > DEBOUNCE_CYCLES) {
        // Attempt relay reset (toggle 3x)
        for (int i = 0; i < 3; i++) {
            digitalWrite(PIN_RELAY, HIGH); delay(200);
            digitalWrite(PIN_RELAY, LOW);  delay(200);
        }
        // Check if flow stopped
        delay(1000);
        if (flowRate > MIN_FLOW_THRESHOLD) {
            triggerLeakAlert("solenoid_stuck_open", SEVERITY_EMERGENCY);
            // Hardware failure — relay toggle didn't help
        }
    }
} else {
    stuckDebounce = 0;
}
```

---

### Rule 4: Continuous Flow > 30 Min = STUCK VALVE

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 4: CONTINUOUS FLOW                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    flowRate > MIN_FLOW_THRESHOLD (0.01 L/min)                  │
│    AND持续时间 > CONTINUOUS_FLOW_MIN (30 minutes)              │
│                                                                 │
│  Meaning: Water has been flowing non-stop for 30+ minutes.      │
│  Even with active session, this is abnormal.                    │
│                                                                 │
│  Possible Causes:                                               │
│    • Stuck valve (solenoid or faucet)                           │
│    • Running toilet (flapper not sealing)                       │
│    • Forgotten faucet left open                                 │
│    • Slow leak from loose fitting                               │
│                                                                 │
│  Response:                                                      │
│    severity = ALERT                                             │
│    action = emergencyShutoff() if no session,                   │
│             warnUser() if session active                        │
│    alert = "continuous_flow"                                    │
│    → If session active: warn via LED + log                      │
│    → If no session: emergency shutoff                           │
│    → Send alert via ESP-NOW                                     │
│                                                                 │
│  Confidence: MEDIUM (80%) — some legitimate uses last long      │
│  (filling large container, garden hose)                         │
│  False Positive Rate: ~5% (legitimate long-use scenarios)       │
└─────────────────────────────────────────────────────────────────┘
```

**Pseudocode:**

```cpp
if (flowRate > MIN_FLOW_THRESHOLD) {
    continuousFlowTime += SEND_INTERVAL_MS / 1000;  // accumulate seconds
    if (continuousFlowTime > CONTINUOUS_FLOW_MIN * 60) {
        if (!sessionActive) {
            triggerLeakAlert("continuous_flow", SEVERITY_ALERT);
            emergencyShutoff();
        } else {
            triggerLeakAlert("continuous_flow", SEVERITY_WARNING);
            // Warn user — don't shutoff during active session
        }
    }
} else {
    continuousFlowTime = 0;  // reset when flow stops
}
```

---

### Rule 5: Drip Leak (0.1–0.5 L/min > 5 Min)

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 5: DRIP LEAK                                              │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    flowRate > DRIP_MIN_RATE (0.1 L/min)                        │
│    AND flowRate < DRIP_MAX_RATE (0.5 L/min)                    │
│    AND持续时间 > DRIP_MIN_TIME (5 minutes)                     │
│    AND sessionActive == false (no authorized user)              │
│                                                                 │
│  Meaning: Slow, steady trickle for extended period with no      │
│  authorized user. Classic drip leak signature.                  │
│                                                                 │
│  Possible Causes:                                               │
│    • Dripping faucet (worn washer/O-ring)                       │
│    • Loose pipe fitting                                         │
│    • Slow leak from check valve                                 │
│    • Toilet flapper leak                                        │
│                                                                 │
│  Response:                                                      │
│    severity = WARNING                                           │
│    action = log + notify                                        │
│    alert = "drip_leak"                                          │
│    → No emergency shutoff (drip is slow, not critical)          │
│    → Log to Firebase for trend analysis                         │
│    → Dashboard notification                                     │
│    → Recommend maintenance                                      │
│                                                                 │
│  Confidence: MEDIUM (75%) — drip rate can overlap with normal   │
│  low-flow usage (filling a glass)                               │
│  False Positive Rate: ~8% (normal low-flow use < 5 min)        │
└─────────────────────────────────────────────────────────────────┘
```

**Pseudocode:**

```cpp
if (flowRate > DRIP_MIN_RATE && flowRate < DRIP_MAX_RATE && !sessionActive) {
    dripTime += SEND_INTERVAL_MS / 1000;
    if (dripTime > DRIP_MIN_TIME * 60) {
        triggerLeakAlert("drip_leak", SEVERITY_WARNING);
        // Don't shutoff — drip is slow, recommend maintenance
    }
} else {
    dripTime = 0;
}
```

---

### Rule 6: Night Flow (22:00–05:00) = SUSPICIOUS

```
┌─────────────────────────────────────────────────────────────────┐
│  RULE 6: NIGHT FLOW                                             │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    current_hour >= NIGHT_START_HOUR (22)                        │
│    OR current_hour < NIGHT_END_HOUR (5)                         │
│    AND flowRate > MIN_FLOW_THRESHOLD (0.01 L/min)              │
│    AND sessionActive == false (no authorized user)              │
│                                                                 │
│  Meaning: Water flowing during sleeping hours with no           │
│  authorized user. Possible leak, unauthorized use, or           │
│  pipe burst.                                                    │
│                                                                 │
│  Possible Causes:                                               │
│    • Pipe burst at night (undetected)                           │
│    • Unauthorized water access                                  │
│    • Toilet running (flapper leak)                              │
│    • Irrigation system malfunction                              │
│                                                                 │
│  Response:                                                      │
│    severity = ALERT                                             │
│    action = emergencyShutoff()                                  │
│    alert = "night_flow"                                         │
│    → Emergency shutoff (conservative — night = unattended)      │
│    → Send alert via ESP-NOW                                     │
│    → Log to Firebase                                            │
│    → Dashboard push notification                                │
│                                                                 │
│  Confidence: HIGH (90%) — night flow with no session is         │
│  almost always a problem                                        │
│  False Positive Rate: ~3% (late-night legitimate use)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Advanced Detection Methods

Beyond the 6 core rules, these methods catch leaks that the basic rules miss.

### 3.1 Slow Accumulation Leak

A leak too small to trigger Rule 5 (drip) but detectable over hours.

```
┌─────────────────────────────────────────────────────────────────┐
│  METHOD: Slow Accumulation                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Logic:                                                         │
│    Track cumulative volume when NO session is active            │
│    IF unauthorized_volume > SLOW_LEAK_THRESHOLD (500 ml/hr)    │
│       → FLAG: slow accumulation leak                            │
│                                                                 │
│  Why it works:                                                  │
│    Normal rooms have 0 ml unauthorized volume.                  │
│    Any sustained accumulation = hidden leak.                    │
│                                                                 │
│  Runs on: Main ESP32 (aggregates across rooms)                 │
│  Window: 1 hour                                                 │
│  Threshold: 500 ml/hr (configurable)                           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Flow After Shutoff

Detects water flowing after the main ESP32 has commanded solenoid shutoff.

```
┌─────────────────────────────────────────────────────────────────┐
│  METHOD: Post-Shutoff Flow                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Logic:                                                         │
│    Main ESP32 commands solenoid OFF                             │
│    Waits 5 seconds for solenoid to close                        │
│    Reads calibrated flow sensor                                 │
│    IF flow > 0.01 L/min after shutoff:                          │
│       → FLAG: solenoid failure or downstream burst              │
│       → Attempt shutoff on SECOND solenoid (redundancy)         │
│       → If still flowing: CRITICAL hardware alert               │
│                                                                 │
│  Why it works:                                                  │
│    Dual-solenoid design allows verification.                    │
│    If both solenoids OFF but flow persists = pipe burst.        │
│                                                                 │
│  Runs on: Main ESP32 only (has both solenoids)                 │
│  Delay: 5 sec after shutoff command                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Sensor Disagreement

Detects when room sensors and main sensor disagree beyond calibration error.

```
┌─────────────────────────────────────────────────────────────────┐
│  METHOD: Sensor Disagreement                                    │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Logic:                                                         │
│    main_volume = calibrated sensor reading                      │
│    room_sum = sum of all room uncalibrated readings             │
│    expected_ratio = main_volume / room_sum                     │
│                                                                 │
│    IF expected_ratio > 1.5 OR expected_ratio < 0.5:            │
│       → FLAG: sensor disagreement                               │
│       → Possible: sensor failure, debris, air bubble            │
│       → Action: log warning, recommend calibration check        │
│                                                                 │
│  Why it works:                                                  │
│    Room sensors are uncalibrated (±10-15%), but a 50%+          │
│    discrepancy means something is wrong.                        │
│                                                                 │
│  Runs on: Main ESP32                                            │
│  Min volume: 5L (for meaningful ratio)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Intermittent Leak Detection

Catches leaks that come and go (e.g., pressure-dependent leaks).

```
┌─────────────────────────────────────────────────────────────────┐
│  METHOD: Intermittent Leak                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Logic:                                                         │
│    Track leak alert count per room in rolling 1-hour window     │
│    IF leak_alert_count > INTERMITTENT_THRESHOLD (3):            │
│       → FLAG: intermittent leak                                 │
│       → Same room keeps triggering briefly, then stops          │
│       → Action: escalate to WARNING (investigate)               │
│                                                                 │
│  Why it works:                                                  │
│    Intermittent leaks trigger Rule 1 or Rule 2 briefly,         │
│    then stop (pressure equalizes, valve reseats).               │
│    Multiple brief triggers in short window = real problem.      │
│                                                                 │
│  Runs on: Main ESP32 (tracks across room reports)              │
│  Window: 1 hour                                                 │
│  Threshold: 3 triggers per hour                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Mass Balance Leak Detection

> Cross-references the **calibrated inlet sensor** (main ESP32) against **uncalibrated room sensors** to detect hidden leaks in pipe runs.

### 4.1 How Mass Balance Works

```
                    ┌──────────────────────┐
                    │   Calibrated Sensor  │
                    │   (Main ESP32)       │
                    │   Volume = 12,500 ml │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    T-Connector Split  │
                    └──┬───────┬────────┬──┘
                       │       │        │
              ┌────────▼──┐ ┌──▼──────┐ ┌▼────────┐
              │ Room 1    │ │ Room 2  │ │ Room 3  │
              │ 4,500 ml  │ │ 3,200ml │ │ 3,500ml │
              └───────────┘ └─────────┘ └─────────┘

              Room Sum = 4,500 + 3,200 + 3,500 = 11,200 ml
              Balance  = 12,500 - 11,200 = 1,300 ml (10.4%)
```

### 4.2 Balance Thresholds

| Balance % | Status | Action |
|-----------|--------|--------|
| < 5% | ✅ Normal | Within calibration error margin |
| 5–10% | ℹ️ Info | Log for trend analysis |
| 10–20% | ⚠️ Warning | Investigate pipe connections, check for drips |
| > 20% | 🔴 Anomaly | Hidden leak between main and rooms — urgent investigation |

### 4.3 Balance Calculation Rules

```
┌─────────────────────────────────────────────────────────────────┐
│  MASS BALANCE CALCULATION                                       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Inputs:                                                        │
│    inlet_ml    — calibrated sensor total (main ESP32)           │
│    room_ml[]   — uncalibrated sensor totals (room ESP32s)       │
│                                                                 │
│  Computation:                                                   │
│    expected = room_ml[0] + room_ml[1] + room_ml[2]             │
│    balance_ml = inlet_ml - expected                             │
│    balance_pct = (balance_ml / inlet_ml) × 100                 │
│                                                                 │
│  Guard conditions:                                              │
│    • Skip if inlet_ml < 5000 ml (too small for meaningful %)   │
│    • Skip if any room sensor read error (pulses = 0 but flow > 0)│
│    • Average over 5-minute window (reduce noise)                │
│                                                                 │
│  Output:                                                        │
│    balance_flag = (|balance_pct| > ANOMALY_BALANCE_ANOMALY_PCT)│
│    balance_severity = based on threshold table above            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Balance Over Time

Track balance trends to distinguish **calibration drift** from **real leaks:**

```
Day 1: balance = +8%   (calibration error, stable)
Day 2: balance = +9%   (stable)
Day 3: balance = +11%  (starting to increase)
Day 4: balance = +14%  (increasing — possible leak)
Day 5: balance = +18%  (likely leak — investigate)
Day 6: balance = +22%  (confirmed leak — urgent)
```

If balance **increases over days**, it's a growing leak. If balance is **stable**, it's calibration error.

---

## 5. Pulse Pattern Analysis

Analyzes the raw pulse stream from flow sensors to detect **non-flow anomalies.**

### 5.1 Sensor Noise / Debris

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN: Erratic Pulses                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Normal pulse pattern:                                          │
│    ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─  (regular, ~10ms apart)        │
│     └─┘ └─┘ └─┘ └─┘ └─┘ └─┘                                  │
│                                                                 │
│  Noisy pulse pattern:                                           │
│    ─┐ ┌┐┌─┐  ┌─┐┌┐ ┌┐ ┌─┐ ┌  (irregular, varying intervals)  │
│     └─┘└┘ └──┘ └┘└─┘└─┘ └─┘                                  │
│                                                                 │
│  Detection:                                                     │
│    • Compute variance of inter-pulse intervals                 │
│    • Normal: variance < 5 ms²                                   │
│    • Noisy:  variance > 20 ms²                                  │
│    • IF noisy AND flow > 0:                                     │
│       → FLAG: sensor may have debris                            │
│       → Action: log warning, recommend sensor cleaning          │
│                                                                 │
│  Runs on: Room ESP32 (closest to sensor)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 No-Flow Pulse Detection

Detects pulses when no water should be flowing (sensor malfunction or air bubbles).

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN: Ghost Pulses                                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Condition:                                                     │
│    pulses > 0 AND flowRate == 0 (after PPL calculation)        │
│    AND sessionActive == false                                   │
│                                                                 │
│  Meaning: Sensor is generating pulses but calculated flow       │
│  is zero. Could be:                                             │
│    • Air bubbles in sensor (turbulence)                         │
│    • Sensor Hall effect noise                                   │
│    • EMI interference                                           │
│                                                                 │
│  Detection:                                                     │
│    IF ghost_pulse_count > 10 per 5-sec interval:               │
│       → FLAG: sensor calibration issue                          │
│       → Action: log, recommend recalibration                    │
│                                                                 │
│  Runs on: Room ESP32                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Pulse Saturation

Detects when the sensor is maxed out (flow exceeds sensor range).

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN: Pulse Saturation                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  YF-S201 max flow: ~30 L/min                                   │
│  At 450 PPL: ~22,500 pulses/min = 375 pulses/sec              │
│                                                                 │
│  Condition:                                                     │
│    pulse_count_this_interval > SATURATION_THRESHOLD             │
│    (e.g., > 3000 pulses in 5 sec = 10 L/min sustained)        │
│                                                                 │
│  Meaning: Flow rate exceeds normal household range.             │
│  Could be main pipe burst or sensor error.                      │
│                                                                 │
│  Detection:                                                     │
│    IF pulses > SATURATION_THRESHOLD:                            │
│       → FLAG: high flow anomaly                                 │
│       → Action: log alert, check for major leak                 │
│                                                                 │
│  Runs on: Room ESP32 + Main ESP32                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Combined Anomaly + Leak Logic

When anomaly detection and leak detection both flag the same event, the system uses a **combined decision matrix.**

### 6.1 Decision Matrix

| Leak Rule | Anomaly Signal | Combined Severity | Action |
|-----------|---------------|-------------------|--------|
| Rule 1 (no session + flow) | Spike detected | **EMERGENCY** | Immediate shutoff |
| Rule 1 (no session + flow) | Baseline deviation | **EMERGENCY** | Immediate shutoff |
| Rule 1 (no session + flow) | No anomaly signal | **EMERGENCY** | Immediate shutoff (leak alone is enough) |
| Rule 4 (continuous flow) | Trend increasing | **CRITICAL** | Shutoff + investigate |
| Rule 4 (continuous flow) | No trend | **WARNING** | Warn user, log |
| Rule 5 (drip leak) | Burst detected | **WARNING** | Log + recommend maintenance |
| Rule 5 (drip leak) | No burst | **INFO** | Log only |
| Rule 6 (night flow) | Time-pattern anomaly | **EMERGENCY** | Immediate shutoff |
| No leak rule triggered | Spike detected | **WARNING** | Log + notify |
| No leak rule triggered | Z-score > 3.0 | **WARNING** | Log + notify |
| No leak rule triggered | Mass balance > 20% | **CRITICAL** | Investigate pipes |
| No leak rule triggered | Trend > 30% increase | **WARNING** | Recommend audit |

### 6.2 Priority Override Rules

```
┌─────────────────────────────────────────────────────────────────┐
│  OVERRIDE RULES                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. LEAK RULES ALWAYS WIN                                       │
│     If any leak rule triggers → anomaly flags are suppressed    │
│     (leak detection is more specific, anomaly is redundant)     │
│                                                                 │
│  2. HIGHEST SEVERITY PREVAILS                                   │
│     If both systems flag: max(leak_severity, anomaly_severity)  │
│                                                                 │
│  3. COMBINED CONFIDENCE BOOST                                   │
│     If BOTH systems flag the same room:                         │
│        confidence = leak_confidence × 1.5 (capped at 100%)     │
│        → Dashboard shows "HIGH CONFIDENCE" badge                │
│                                                                 │
│  4. DEDUPLICATION                                               │
│     If leak alert + anomaly alert fire within 10 sec of each   │
│     other for the same room:                                    │
│        → Merge into single alert                                │
│        → Record both sources in alert detail                    │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Combined Detection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMBINED DETECTION FLOW                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Room ESP32 (per cycle):                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Read flow sensor                                      │  │
│  │  2. Run Leak Rules 1-6 → leak_flags                      │  │
│  │  3. Run Anomaly Detection → anomaly_flags                 │  │
│  │  4. Merge: combined_flags = leak_flags OR anomaly_flags   │  │
│  │  5. If leak_flags: suppress anomaly (redundant)           │  │
│  │  6. Send combined_flags via ESP-NOW                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  Main ESP32 (per 5 sec):                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Receive room data + combined_flags                    │  │
│  │  2. Run Mass Balance check → balance_flag                 │  │
│  │  3. Run Time-Pattern check → time_flag                    │  │
│  │  4. Run Post-Shutoff verification → shutoff_flag          │  │
│  │  5. Cross-room correlation → multi_room_flag              │  │
│  │  6. Combine all flags → global_severity                   │  │
│  │  7. Execute response matrix (shutoff/warn/log)            │  │
│  │  8. Push to Firebase RTDB                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  Firebase Cloud:                                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Store alert in /alerts/active/                        │  │
│  │  2. Store in /alerts/history/ for audit trail             │  │
│  │  3. Update /rooms/{id}/anomaly/ with latest flags         │  │
│  │  4. Trigger Cloud Function for push notification          │  │
│  │  5. Update daily baselines for trend analysis             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  Next.js Dashboard:                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. onValue listener on /alerts/active/                   │  │
│  │  2. Render real-time alert cards                          │  │
│  │  3. Show severity badge (info/warning/critical/emergency) │  │
│  │  4. Allow acknowledge/dismiss                             │  │
│  │  5. Show trend charts with anomaly markers                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Response Matrix

### 7.1 Automatic Responses

| Severity | Solenoid | SSR | LED | Firebase Alert | Dashboard | Push Notification |
|----------|----------|-----|-----|----------------|-----------|-------------------|
| **INFO** | No change | No change | Green | Log only | Badge | No |
| **WARNING** | No change | No change | Yellow blink | ✅ | Card + badge | No |
| **ALERT** | OFF | OFF | Yellow solid | ✅ | Card + popup | ✅ |
| **CRITICAL** | OFF | OFF | Red solid | ✅ | Card + popup + banner | ✅ |
| **EMERGENCY** | OFF | OFF | Red flash | ✅ + escalation | Full-screen alert | ✅ + SMS (if configured) |

### 7.2 Escalation Timeline

```
T+0 sec:   Anomaly/leak detected
T+0 sec:   Room ESP32 sends alert via ESP-NOW
T+0-5 sec: Main ESP32 receives, validates, pushes to Firebase
T+5 sec:   Dashboard shows alert card
T+30 sec:  If warning persists → escalate to alert
T+5 min:   If alert persists → escalate to critical
T+15 min:  If critical persists → escalate to emergency
T+15 min:  Emergency → recommend manual intervention
```

### 7.3 Recovery Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  RECOVERY: After Leak/Anomaly Resolved                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  1. Flow stops (leak fixed, valve replaced, etc.)               │
│  2. Room ESP32 detects flow == 0 for > 30 sec                  │
│  3. Clears leak/anomaly flags                                   │
│  4. Sends "resolved" status via ESP-NOW                         │
│  5. Main ESP32 updates Firebase:                                │
│     /alerts/active/{id}/resolved_at = timestamp                 │
│     Moves alert to /alerts/history/                             │
│  6. Dashboard:                                                  │
│     Alert card moves from "Active" to "History" tab             │
│     Green "Resolved" badge shown                                │
│  7. User can manually re-enable solenoid from dashboard        │
│     (solenoid stays OFF until explicit re-enable)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. False Positive Reduction

### 8.1 Debouncing

All leak rules require **sustained conditions** before triggering:

| Rule | Debounce Time | Rationale |
|------|--------------|-----------|
| Rule 1 (no session + flow) | 3 sec | Prevents trigger on sensor noise |
| Rule 2 (post-session flow) | 3 sec | Solenoid needs time to close |
| Rule 3 (solenoid OFF + flow) | 3 sec + retry | May be sensor startup noise |
| Rule 4 (continuous flow) | 30 min | Long window avoids legitimate uses |
| Rule 5 (drip leak) | 5 min | Distinguish drip from normal low-flow |
| Rule 6 (night flow) | 3 sec | Night = conservative, short debounce OK |

### 8.2 Context Requirements

Each rule requires **specific context** to reduce false positives:

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT REQUIREMENTS PER RULE                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Rule 1: !sessionActive AND flowRate > threshold                │
│          (RFID state is critical context)                       │
│                                                                 │
│  Rule 2: !sessionActive AND !solenoidOn AND flowRate > threshold│
│          (Both RFID AND solenoid state required)                │
│                                                                 │
│  Rule 3: !solenoidOn AND flowRate > threshold                   │
│          (Solenoid state is critical)                           │
│                                                                 │
│  Rule 4: flowRate > threshold AND duration > 30 min             │
│          (Time is the differentiator)                            │
│                                                                 │
│  Rule 5: flowRate in [0.1, 0.5] AND duration > 5 min           │
│          AND !sessionActive                                     │
│          (Rate range + time + RFID state)                       │
│                                                                 │
│  Rule 6: isNightTime() AND flowRate > threshold                 │
│          AND !sessionActive                                     │
│          (Time + RFID state)                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Learning from History

The system learns normal patterns to reduce future false positives:

- **Daily baselines** per room per time period (stored in Firebase)
- **Per-room calibration** factors (updated via bucket test)
- **User feedback** — "this was not a leak" button on dashboard adjusts thresholds

---

## 9. Firebase RTDB Structure

### 9.1 Active Alerts

```
/tapflow/alerts/active/{alert_id}
├── type: "leak" | "anomaly" | "combined"
├── rule: "no_session_flow" | "solenoid_stuck_open" | "continuous_flow" | ...
├── severity: "info" | "warning" | "alert" | "critical" | "emergency"
├── room_id: 1
├── device_id: "tapflow-room1"
├── ts: 1703123456789
├── detail: "Flow detected with no active RFID session"
├── flow_rate_lpm: 2.34
├── threshold: 0.01
├── anomaly_context:
│   ├── zscore: 4.2
│   ├── spike: true
│   └── burst: false
├── acknowledged: false
├── acknowledged_by: null
├── resolved: false
└── resolved_at: null
```

### 9.2 Alert History

```
/tapflow/alerts/history/{alert_id}
├── (same fields as active)
├── resolved_at: 1703124000000
├── duration_sec: 544
├── response_time_sec: 5
├── auto_shutoff: true
└── user_action: "replaced solenoid valve"
```

### 9.3 Leak Event Log

```
/tapflow/events/leaks/{event_id}
├── room_id: 2
├── rule: "solenoid_stuck_open"
├── ts_start: 1703123456789
├── ts_end: 1703124000000
├── duration_sec: 544
├── volume_lost_ml: 12500
├── severity: "emergency"
├── auto_shutoff: true
├── shutoff_time_sec: 5
└── resolution: "hardware_replacement"
```

---

## 10. ESP32 Module: `leak_detector.h`

### 10.1 Room ESP32 Leak Detector

**Responsibilities:**
- Run 6 core leak detection rules
- Manage debounce timers per rule
- Control emergency shutoff
- Export leak flags via ESP-NOW

**Interface:**

```cpp
class LeakDetector {
public:
    void begin();                          // Initialize thresholds from config.h
    void checkAll(                         // Run all rules every cycle
        float flowRate,
        bool sessionActive,
        bool solenoidOn,
        float continuousFlowTime,
        float dripTime,
        bool isNightTime
    );
    bool isLeakActive();                   // Any leak rule currently triggered
    uint8_t getLeakFlags();                // Bitmask of active rules
    const char* getLeakType();             // Highest severity leak type
    void emergencyShutoff();               // SSR OFF + Solenoid OFF
    void acknowledge();                    // User acknowledged alert
};
```

**Leak flag bitmask:**

| Bit | Rule | Name |
|-----|------|------|
| 0 | Rule 1 | `no_session_flow` |
| 1 | Rule 2 | `post_session_flow` |
| 2 | Rule 3 | `solenoid_stuck_open` |
| 3 | Rule 4 | `continuous_flow` |
| 4 | Rule 5 | `drip_leak` |
| 5 | Rule 6 | `night_flow` |

### 10.2 Main ESP32 Leak Detector

**Responsibilities:**
- Aggregate room leak flags
- Mass balance check
- Post-shutoff verification (dual solenoid)
- Intermittent leak detection
- Push to Firebase

**Interface:**

```cpp
class MainLeakDetector {
public:
    void begin();
    void checkAll(                         // Run every 5 sec
        RoomData rooms[],                  // ESP-NOW data from 3 rooms
        float inletVolume,                 // Calibrated sensor reading
        bool solenoid1On,
        bool solenoid2On
    );
    bool isGlobalLeakActive();
    int getGlobalSeverity();               // Max severity across all rooms
    void pushToFirebase(FirebaseData &fb); // Write alerts + data to RTDB
    void verifyShutoff();                  // Check flow after solenoid OFF
};
```

---

## 11. Configuration Thresholds

### Room ESP32

| Parameter | Default | Unit | Config Key |
|-----------|---------|------|------------|
| Min flow threshold | 0.01 | L/min | `MIN_FLOW_THRESHOLD` |
| Debounce cycles | 30 | cycles (×100ms) | `LEAK_DEBOUNCE_CYCLES` |
| Continuous flow min | 30 | minutes | `CONTINUOUS_FLOW_MIN` |
| Drip min rate | 0.1 | L/min | `DRIP_MIN_RATE` |
| Drip max rate | 0.5 | L/min | `DRIP_MAX_RATE` |
| Drip min time | 5 | minutes | `DRIP_MIN_TIME` |
| Night start hour | 22 | hour | `NIGHT_START_HOUR` |
| Night end hour | 5 | hour | `NIGHT_END_HOUR` |
| Solenoid off delay | 5 | seconds | `SOLENOID_OFF_DELAY_MS` |
| Session timeout | 10 | minutes | `SESSION_TIMEOUT_MS` |

### Main ESP32

| Parameter | Default | Unit | Config Key |
|-----------|---------|------|------------|
| Balance warning % | 10 | % | `BALANCE_WARNING_PCT` |
| Balance anomaly % | 20 | % | `BALANCE_ANOMALY_PCT` |
| Min volume for balance | 5000 | ml | `BALANCE_MIN_VOLUME` |
| Slow leak threshold | 500 | ml/hr | `SLOW_LEAK_THRESHOLD` |
| Intermittent threshold | 3 | triggers/hr | `INTERMITTENT_THRESHOLD` |
| Post-shutoff delay | 5 | seconds | `POST_SHUTOFF_DELAY` |
| Sensor disagreement | 50 | % | `SENSOR_DISAGREEMENT_PCT` |
| Saturation threshold | 3000 | pulses/5sec | `SATURATION_THRESHOLD` |

---

## 12. Validation Checklist

- [ ] **Rule 1:** Simulate RFID removed while faucet running → emergency shutoff within 3 sec
- [ ] **Rule 2:** End RFID session while water flows → emergency shutoff within 3 sec
- [ ] **Rule 3:** Command solenoid OFF while flow persists → relay retry + alert
- [ ] **Rule 4:** Run water for 31 min without stopping → continuous flow alert
- [ ] **Rule 5:** Simulate drip (0.2 L/min) for 6 min → drip leak warning
- [ ] **Rule 6:** Set clock to 2 AM, flow without RFID → night flow alert
- [ ] **Mass balance:** Run 10L through inlet, verify rooms sum within 10%
- [ ] **Mass balance:** Block one room pipe → balance > 20% flagged
- [ ] **Post-shutoff:** Command solenoid OFF, verify flow stops within 5 sec
- [ ] **Intermittent:** Trigger Rule 1 three times in 1 hour → intermittent flag
- [ ] **Debounce:** Brief flow burst (< 3 sec) → no leak alert (debounce filters)
- [ ] **False positive:** Normal faucet use for 30 min → zero leak alerts
- [ ] **Combined:** Leak + anomaly both flag → merged alert, highest severity
- [ ] **Recovery:** Fix leak, flow stops → alert resolved, solenoid stays OFF until re-enable
- [ ] **Firebase:** Alert appears in `/alerts/active/` within 5 sec of detection
- [ ] **Dashboard:** Alert card shows within 5 sec of Firebase write

---

## Related Guides

| Guide | Relationship |
|-------|-------------|
| [anomaly-detection-guide.md](./anomaly-detection-guide.md) | Anomaly algorithms that complement leak rules |
| [module-integration-guide.md](./module-integration-guide.md) | How ESP32 modules wire together |
| [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md) | Dashboard UI for leak visualization |
| [block-diagram.md](./block-diagram.md) | 6 rules reference diagram |
| [system-architecture.md](./system-architecture.md) | Overall system design |
