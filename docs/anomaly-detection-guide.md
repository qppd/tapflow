# Anomaly Detection Guide — TapFlow

> **Purpose:** Detect unusual water usage patterns across rooms using statistical and rule-based methods on ESP32 firmware + Firebase cloud + Next.js dashboard.
> **Builds on:** [system-architecture.md](./system-architecture.md), [block-diagram.md](./block-diagram.md)
> **Feeds into:** [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md), [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md)

---

## Table of Contents

1. [What Is Anomaly Detection?](#1-what-is-anomaly-detection)
2. [Detection Layers (ESP32 + Cloud + Dashboard)](#2-detection-layers-esp32--cloud--dashboard)
3. [Algorithms](#3-algorithms)
4. [ESP32 Module: `anomaly_detector.h`](#4-esp32-module-anomaly_detectorh)
5. [Firebase RTDB Data Structure](#5-firebase-rtdb-data-structure)
6. [Main ESP32 → Firebase Push Format](#6-main-esp32--firebase-push-format)
7. [Alert Severity Levels](#7-alert-severity-levels)
8. [Configuration Thresholds](#8-configuration-thresholds)
9. [Integration with Leak Detection](#9-integration-with-leak-detection)
10. [Validation Checklist](#10-validation-checklist)

---

## 1. What Is Anomaly Detection?

Anomaly detection identifies **unusual patterns** in water usage that are not necessarily leaks but deviate from normal behavior. While **leak detection** (see [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md)) handles critical failures, anomaly detection catches **softer signals** that warrant investigation.

| Detection Type | Response | Example |
|----------------|----------|---------|
| **Leak Detection** | Emergency shutoff + alert | Solenoid stuck open, no-RFID flow |
| **Anomaly Detection** | Warning notification + logging | Sudden flow spike, unusual night usage, consumption drift |

---

## 2. Detection Layers (ESP32 + Cloud + Dashboard)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ANOMALY DETECTION LAYERS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 1: Room ESP32 (real-time, offline-capable)                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  • Rate-of-change detection (spike in flow rate)             │  │
│  │  • Burst detection (short high-flow pulses)                  │  │
│  │  • Baseline deviation (current vs. rolling average)          │  │
│  │  • Runs every cycle (~100ms), sends flags via ESP-NOW        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  LAYER 2: Main ESP32 (aggregation + cross-room checks)             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  • Mass balance check (inlet vs. sum of rooms)               │  │
│  │  • Cross-room correlation (multiple rooms active = normal)   │  │
│  │  • Time-pattern analysis (night usage, weekend patterns)     │  │
│  │  • Aggregates room flags + own sensor → pushes to Firebase   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  LAYER 3: Firebase Cloud (history + trend analysis)                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  • Historical baseline computation (7-day rolling average)   │  │
│  │  • Trend detection (gradual consumption increase)            │  │
│  │  • Anomaly scoring (weighted combination of signals)         │  │
│  │  • Stores alerts, scores, and baselines for dashboard        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  LAYER 4: Next.js Dashboard (visualization + user alerts)          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  • Real-time anomaly feed (Firebase onValue listener)        │  │
│  │  • Trend charts (hourly/daily/weekly consumption)            │  │
│  │  • Anomaly score gauge + historical log                      │  │
│  │  • User-configurable threshold overrides                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Algorithms

### 3.1 Rate-of-Change Detection (Room ESP32)

Detects **sudden spikes** in flow rate between consecutive readings.

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Rate-of-Change                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Inputs:                                                        │
│    flow_rate_now    — current flow rate (L/min)                 │
│    flow_rate_prev   — previous flow rate (L/min)                │
│    dt               — time since last reading (seconds)         │
│                                                                 │
│  Computation:                                                   │
│    delta    = flow_rate_now - flow_rate_prev                    │
│    rate     = delta / dt                                        │
│                                                                 │
│  Thresholds:                                                    │
│    SPIKE    = rate > 5.0 L/min/sec   → ANOMALY: sudden spike   │
│    DROP     = rate < -5.0 L/min/sec  → ANOMALY: sudden drop    │
│                                                                 │
│  Rationale: Normal faucet opening reaches steady state in       │
│  ~2-3 sec. Faster changes suggest valve malfunction or pipe     │
│  burst.                                                         │
└─────────────────────────────────────────────────────────────────┘
```

**ESP32 implementation sketch:**

```cpp
// In anomaly_detector.h
struct RateOfChangeResult {
    bool spikeDetected;
    bool dropDetected;
    float rate;          // L/min/sec
    float delta;         // L/min
};

RateOfChangeResult checkRateOfChange(float flowNow, float flowPrev, unsigned long dtMs) {
    RateOfChangeResult result;
    float dt = dtMs / 1000.0;
    if (dt < 0.1) dt = 0.1;  // prevent division by near-zero

    result.delta = flowNow - flowPrev;
    result.rate = result.delta / dt;
    result.spikeDetected = (result.rate > SPIKE_THRESHOLD);   // > 5.0 L/min/sec
    result.dropDetected  = (result.rate < -SPIKE_THRESHOLD);  // < -5.0 L/min/sec
    return result;
}
```

---

### 3.2 Baseline Deviation Detection (Room ESP32)

Compares current flow rate against a **rolling average** maintained on the ESP32.

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Baseline Deviation (Z-Score)                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Maintains:                                                     │
│    baseline[WINDOW_SIZE]  — circular buffer of last N readings  │
│    baseline_mean          — mean of buffer                      │
│    baseline_std           — standard deviation of buffer        │
│                                                                 │
│  Computation:                                                   │
│    z_score = (flow_rate_now - baseline_mean) / baseline_std    │
│                                                                 │
│  Thresholds:                                                    │
│    |z_score| > 3.0  → ANOMALY: significant deviation           │
│    |z_score| > 2.0  → WARNING: notable deviation               │
│                                                                 │
│  Window: 60 readings (5 min at 5-sec intervals)                │
│  Warmup: First 12 readings ignored (build baseline)            │
└─────────────────────────────────────────────────────────────────┘
```

**ESP32 implementation sketch:**

```cpp
// In anomaly_detector.h
#define BASELINE_WINDOW 60    // 5 min at 5-sec intervals
#define BASELINE_WARMUP 12    // 60 sec warmup
#define ZSCORE_ANOMALY  3.0
#define ZSCORE_WARNING  2.0

class BaselineTracker {
    float buffer[BASELINE_WINDOW];
    int index = 0;
    int count = 0;
    float mean = 0;
    float variance = 0;

public:
    void update(float value) {
        if (count < BASELINE_WINDOW) {
            buffer[count] = value;
            count++;
        } else {
            buffer[index] = value;
            index = (index + 1) % BASELINE_WINDOW;
        }
        // Recompute mean and variance
        float sum = 0, sumSq = 0;
        for (int i = 0; i < count; i++) {
            sum += buffer[i];
            sumSq += buffer[i] * buffer[i];
        }
        mean = sum / count;
        variance = (sumSq / count) - (mean * mean);
    }

    float getZScore(float value) {
        if (count < BASELINE_WARMUP) return 0;  // not enough data
        float std = sqrt(max(variance, 0.001f));
        return (value - mean) / std;
    }

    bool isWarmedUp() { return count >= BASELINE_WARMUP; }
};
```

---

### 3.3 Burst Detection (Room ESP32)

Detects **short, high-flow pulses** that may indicate water hammer, valve chatter, or sensor noise.

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Burst Detection                                     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Tracks:                                                        │
│    burst_start      — timestamp when flow started               │
│    burst_volume     — cumulative volume during burst (ml)       │
│    burst_active     — boolean: currently in a burst             │
│                                                                 │
│  Logic:                                                         │
│    IF flow > BURST_MIN_RATE (2.0 L/min)                        │
│       AND burst was not active before:                          │
│         → Start burst timer, set burst_active = true            │
│                                                                 │
│    IF flow < BURST_MIN_RATE                                     │
│       AND burst was active:                                     │
│         → End burst. Check:                                     │
│           duration < BURST_MAX_DURATION (10 sec)                │
│           volume < BURST_MAX_VOLUME (200 ml)                    │
│           → ANOMALY: short burst detected                       │
│                                                                 │
│  Rationale: A burst < 10 sec and < 200 ml is too short for      │
│  normal use. Likely water hammer, valve chatter, or sensor      │
│  noise.                                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Time-Pattern Analysis (Main ESP32)

Detects usage at **unusual times** (not just night — also weekends, holidays, etc.).

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Time-Pattern Analysis                               │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Time periods (configurable):                                   │
│    NIGHT:      22:00 – 05:00  (sleeping hours)                 │
│    MORNING:    05:00 – 08:00  (early risers)                   │
│    DAYTIME:    08:00 – 18:00  (work hours)                     │
│    EVENING:    18:00 – 22:00  (peak usage)                     │
│                                                                 │
│  Baselines per period (learned from history):                   │
│    avg_usage[period]    — average volume per period (L)         │
│    std_usage[period]    — standard deviation                    │
│                                                                 │
│  Detection:                                                     │
│    IF usage during current period > avg_usage + 2*std           │
│       → ANOMALY: usage exceeds expected for this time of day   │
│                                                                 │
│    IF usage during NIGHT period > 0 AND no RFID session         │
│       → ANOMALY: unauthorized night usage                      │
│                                                                 │
│  Main ESP32 stores period baselines in Firebase at midnight.    │
│  Cloud computes baselines from historical data.                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.5 Trend Detection (Firebase Cloud)

Detects **gradual increases** in consumption over days/weeks — a sign of slow leaks.

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Trend Detection (Cloud-side)                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Data: Daily total volume per room (last 30 days)              │
│                                                                 │
│  Computation:                                                   │
│    Fit linear regression: volume = slope * day + intercept      │
│    slope > TREND_THRESHOLD (0.5 L/day increase)                │
│       → ANOMALY: gradual consumption increase                   │
│                                                                 │
│  Also check:                                                    │
│    Week-over-week comparison:                                   │
│       IF this_week_total > last_week_total * 1.5               │
│          → ANOMALY: 50%+ week-over-week increase               │
│                                                                 │
│  Runs daily via Firebase Cloud Function (or scheduled check    │
│  on Next.js dashboard load).                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.6 Mass Balance Anomaly (Main ESP32)

Detects **unaccounted water** — water entering the system but not reaching any room.

```
┌─────────────────────────────────────────────────────────────────┐
│  ALGORITHM: Mass Balance                                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Inputs:                                                        │
│    inlet_volume   — calibrated sensor total (main ESP32)        │
│    room_volumes[] — uncalibrated sensor totals (room ESP32s)    │
│                                                                 │
│  Computation:                                                   │
│    expected = room_volumes[0] + room_volumes[1] + room_volumes[2]│
│    balance  = inlet_volume - expected                           │
│    balance_pct = (balance / inlet_volume) * 100                 │
│                                                                 │
│  Thresholds:                                                    │
│    balance_pct > 20%  → ANOMALY: hidden leak between main and  │
│                          rooms (pipe burst in wall)              │
│    balance_pct > 10%  → WARNING: investigate connections        │
│    balance_pct < -10% → ANOMALY: sensor calibration drift      │
│                                                                 │
│  Note: Room sensors are uncalibrated (±10-15% error), so       │
│  thresholds are set generously to avoid false positives.        │
│  Requires at least 5L total flow for meaningful comparison.     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. ESP32 Module: `anomaly_detector.h`

### 4.1 Room ESP32 Anomaly Detector

Runs on each room ESP32. Lightweight — only statistical checks on local sensor data.

**Responsibilities:**
- Rate-of-change detection (spike/drop)
- Baseline deviation (z-score)
- Burst detection (short high-flow pulses)
- Exports anomaly flags via ESP-NOW payload

**Data flow:**

```
┌─────────────────────────────────────────────────────┐
│                 ROOM ESP32                           │
│                                                      │
│  Flow Sensor (GPIO 26)                              │
│       │                                              │
│       ▼                                              │
│  SensorManager.readAll()                            │
│       │                                              │
│       ├──► flowRate[0] ──► AnomalyDetector          │
│       │                        │                     │
│       │    ┌───────────────────┤                     │
│       │    │                   │                     │
│       │    ▼                   ▼                     │
│       │  RateOfChange     BaselineTracker           │
│       │  (spike/drop)     (z-score)                 │
│       │    │                   │                     │
│       │    ▼                   ▼                     │
│       │  burstTracker     zscore > 3.0?             │
│       │  (short pulses)      │                      │
│       │    │                 │                      │
│       │    ▼                 ▼                      │
│       │    └───── anomaly_flags ──────► ESP-NOW     │
│       │                              (to Main ESP32)│
│       │                                              │
│  LocalRules.checkAll()                              │
│       │                                              │
│       ▼                                              │
│  leak_alert flag (also sent via ESP-NOW)            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**ESP-NOW payload (room → main) — updated with anomaly flags:**

| Field | Type | Description |
|-------|------|-------------|
| `room_id` | uint8_t | Room number (1-3) |
| `ts` | uint32_t | Timestamp (millis or NTP) |
| `pulses` | uint32_t | Pulse count this interval |
| `flow_rate_lpm` | float | Current flow rate (L/min) |
| `volume_ml` | uint32_t | Cumulative volume (ml) |
| `leak_alert` | bool | Leak detection flag (from local_rules) |
| `anomaly_spike` | bool | Rate-of-change spike detected |
| `anomaly_baseline` | bool | Z-score > 3.0 deviation |
| `anomaly_burst` | bool | Short burst detected |
| `anomaly_flags` | uint8_t | Bitmask: bit0=spike, bit1=baseline, bit2=burst |

---

### 4.2 Main ESP32 Anomaly Detector

Aggregates room anomaly flags and runs cross-room checks.

**Responsibilities:**
- Receive room anomaly flags via ESP-NOW
- Mass balance check (inlet vs. sum of rooms)
- Time-pattern analysis (night/weekend usage)
- Push aggregated anomaly data to Firebase

**Data flow:**

```
┌──────────────────────────────────────────────────────────────┐
│                      MAIN ESP32                               │
│                                                               │
│  ESP-NOW Receiver                                            │
│       │                                                       │
│       ├──► Room 1 data (pulses, flow, leak_alert, anomaly_flags)│
│       ├──► Room 2 data                                        │
│       └──► Room 3 data                                        │
│               │                                               │
│               ▼                                               │
│  Aggregator (every 5 sec)                                    │
│       │                                                       │
│       ├──► Mass Balance Check                                │
│       │       inlet_volume vs. sum(room_volumes)              │
│       │       → balance_flag                                  │
│       │                                                       │
│       ├──► Time-Pattern Check                                │
│       │       current_hour vs. period_baseline                │
│       │       → time_anomaly_flag                             │
│       │                                                       │
│       ├──► Cross-Room Correlation                            │
│       │       IF 2+ rooms have anomaly flags simultaneously  │
│       │       → multi_room_flag (investigate shared pipe)    │
│       │                                                       │
│       └──► Build Firebase payload                             │
│               │                                               │
│               ▼                                               │
│  Firebase RTDB Push                                           │
│       /rooms/{room_id}/anomaly                               │
│       /anomaly/global                                        │
│       /alerts/{alert_id}                                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Firebase RTDB Data Structure

### 5.1 Per-Room Anomaly Data

```
/tapflow/
├── rooms/
│   ├── 1/
│   │   ├── data/
│   │   │   ├── flow_rate_lpm: 2.34
│   │   │   ├── volume_ml: 456
│   │   │   └── ts: 1703123456789
│   │   ├── anomaly/                    ◄── NEW
│   │   │   ├── spike: false
│   │   │   ├── baseline: false
│   │   │   ├── burst: false
│   │   │   ├── zscore: 0.45
│   │   │   ├── rate_of_change: 0.12
│   │   │   └── ts: 1703123456789
│   │   └── alerts/
│   │       └── {alert_id}/
│   │           ├── type: "anomaly_spike"
│   │           ├── severity: "warning"
│   │           ├── value: 8.5
│   │           ├── threshold: 5.0
│   │           ├── ts: 1703123456789
│   │           └── acknowledged: false
│   ├── 2/
│   │   ├── data/...
│   │   ├── anomaly/...
│   │   └── alerts/...
│   └── 3/
│       ├── data/...
│       ├── anomaly/...
│       └── alerts/...
├── anomaly/                             ◄── NEW (global cross-room)
│   ├── mass_balance/
│   │   ├── inlet_ml: 12500
│   │   ├── rooms_total_ml: 11200
│   │   ├── balance_ml: 1300
│   │   ├── balance_pct: 10.4
│   │   └── ts: 1703123456789
│   ├── time_pattern/
│   │   ├── period: "night"
│   │   ├── usage_ml: 350
│   │   ├── baseline_ml: 50
│   │   ├── deviation_pct: 600
│   │   └── ts: 1703123456789
│   ├── multi_room/
│   │   ├── rooms_active: [1, 2]
│   │   ├── flagged: true
│   │   └── ts: 1703123456789
│   └── trend/
│       ├── slope_lpm: 0.3
│       ├── weekly_increase_pct: 15
│       └── last_check: 1703123456789
├── baselines/                           ◄── NEW (learned patterns)
│   ├── periods/
│   │   ├── night/
│   │   │   ├── avg_ml: 50
│   │   │   └── std_ml: 20
│   │   ├── morning/
│   │   │   ├── avg_ml: 800
│   │   │   └── std_ml: 200
│   │   ├── daytime/
│   │   │   ├── avg_ml: 2000
│   │   │   └── std_ml: 500
│   │   └── evening/
│   │       ├── avg_ml: 1500
│   │       └── std_ml: 400
│   └── daily/
│       ├── 2026-07-14: { room1: 3200, room2: 1800, room3: 2100 }
│       └── ...
└── alerts/
    ├── active/
    │   └── {alert_id}/
    │       ├── type: "anomaly_mass_balance"
    │       ├── severity: "warning"
    │       ├── rooms: [1, 2, 3]
    │       ├── detail: "10.4% unaccounted water"
    │       ├── ts: 1703123456789
    │       └── acknowledged: false
    └── history/
        └── {alert_id}/
            ├── ...
            └── resolved_at: 1703124000000
```

---

## 6. Main ESP32 → Firebase Push Format

### 6.1 Anomaly Data Frame (every 5 sec)

```json
{
  "device_id": "tapflow-main",
  "ts": 1703123456789,
  "type": "anomaly",
  "rooms": [
    {
      "room_id": 1,
      "flow_rate_lpm": 2.34,
      "volume_ml": 456,
      "anomaly": {
        "spike": false,
        "baseline": false,
        "burst": false,
        "zscore": 0.45,
        "rate_of_change": 0.12
      },
      "leak_alert": false
    },
    {
      "room_id": 2,
      "flow_rate_lpm": 0.0,
      "volume_ml": 0,
      "anomaly": {
        "spike": false,
        "baseline": false,
        "burst": false,
        "zscore": 0.0,
        "rate_of_change": 0.0
      },
      "leak_alert": false
    },
    {
      "room_id": 3,
      "flow_rate_lpm": 8.5,
      "volume_ml": 1200,
      "anomaly": {
        "spike": true,
        "baseline": true,
        "burst": false,
        "zscore": 4.2,
        "rate_of_change": 6.8
      },
      "leak_alert": false
    }
  ],
  "global_anomaly": {
    "mass_balance_pct": 10.4,
    "mass_balance_flag": true,
    "time_period": "night",
    "time_anomaly_flag": true,
    "multi_room_flag": false
  }
}
```

### 6.2 Anomaly Alert Frame (on detection)

```json
{
  "device_id": "tapflow-main",
  "ts": 1703123456789,
  "type": "alert",
  "category": "anomaly",
  "severity": "warning",
  "room_id": 3,
  "anomaly_type": "spike",
  "detail": "Flow rate spike: 8.5 L/min (threshold: 5.0 L/min/sec)",
  "value": 8.5,
  "threshold": 5.0,
  "zscore": 4.2,
  "action": "notify"
}
```

### 6.3 Trend Update Frame (daily)

```json
{
  "device_id": "tapflow-main",
  "ts": 1703209800000,
  "type": "trend",
  "room_id": 1,
  "daily_volume_ml": 3200,
  "7day_avg_ml": 2800,
  "7day_std_ml": 400,
  "slope_lpm": 0.3,
  "weekly_increase_pct": 15,
  "flag": true,
  "message": "Room 1 consumption trending upward: +15% week-over-week"
}
```

---

## 7. Alert Severity Levels

| Level | Color | Trigger | Response |
|-------|-------|---------|----------|
| **info** | Blue | Z-score 2.0–3.0, minor deviation | Log only |
| **warning** | Yellow | Z-score > 3.0, spike detected, burst, mass balance > 10% | Dashboard notification + log |
| **critical** | Red | Mass balance > 20%, multi-room anomaly, trend > 30% increase | Dashboard alert + push notification + recommend shutoff |
| **emergency** | Red + Flash | Anomaly coincides with leak detection | Emergency shutoff + all alerts |

### Severity Escalation Rules

```
┌─────────────────────────────────────────────────────────────────┐
│  ESCALATION: Warning → Critical                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  IF anomaly persists for > 5 minutes:                           │
│     severity = warning → critical                               │
│                                                                 │
│  IF anomaly persists for > 15 minutes:                          │
│     severity = critical → emergency                             │
│     → Trigger shutoff recommendation                            │
│                                                                 │
│  IF anomaly coincides with leak_alert:                          │
│     severity = emergency (immediate)                            │
│     → Trigger emergency shutoff                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Configuration Thresholds

All thresholds are defined in `config.h` on the ESP32 and can be overridden via Firebase commands from the dashboard.

### Room ESP32 Thresholds

| Parameter | Default | Unit | Config Key |
|-----------|---------|------|------------|
| Spike threshold | 5.0 | L/min/sec | `ANOMALY_SPIKE_THRESHOLD` |
| Z-score anomaly | 3.0 | — | `ANOMALY_ZSCORE_ANOMALY` |
| Z-score warning | 2.0 | — | `ANOMALY_ZSCORE_WARNING` |
| Baseline window | 60 | readings | `ANOMALY_BASELINE_WINDOW` |
| Baseline warmup | 12 | readings | `ANOMALY_BASELINE_WARMUP` |
| Burst min rate | 2.0 | L/min | `ANOMALY_BURST_MIN_RATE` |
| Burst max duration | 10 | sec | `ANOMALY_BURST_MAX_DURATION` |
| Burst max volume | 200 | ml | `ANOMALY_BURST_MAX_VOLUME` |

### Main ESP32 Thresholds

| Parameter | Default | Unit | Config Key |
|-----------|---------|------|------------|
| Mass balance warning | 10 | % | `ANOMALY_BALANCE_WARNING_PCT` |
| Mass balance anomaly | 20 | % | `ANOMALY_BALANCE_ANOMALY_PCT` |
| Min volume for balance | 5000 | ml | `ANOMALY_BALANCE_MIN_VOLUME` |
| Multi-room threshold | 2 | rooms | `ANOMALY_MULTIROOM_THRESHOLD` |
| Night hours start | 22 | hour | `ANOMALY_NIGHT_START_HOUR` |
| Night hours end | 5 | hour | `ANOMALY_NIGHT_END_HOUR` |

### Dashboard Overrides (Firebase)

Users can adjust thresholds from the web dashboard. Changes are written to Firebase and picked up by the main ESP32 via stream.

```
/tapflow/config/anomaly/
├── spike_threshold: 5.0
├── zscore_anomaly: 3.0
├── balance_warning_pct: 10
├── balance_anomaly_pct: 20
├── night_start_hour: 22
└── night_end_hour: 5
```

---

## 9. Integration with Leak Detection

Anomaly detection and leak detection are **complementary systems** that share data:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DETECTION OVERLAP MATRIX                     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Signal                    │ Leak Detection │ Anomaly Detection │
│  ──────────────────────────┼────────────────┼───────────────────│
│  No RFID + Flow            │ ✅ Rule 1      │ ✅ Z-score spike  │
│  Session ended + Flow      │ ✅ Rule 2      │ ✅ Baseline dev   │
│  Solenoid OFF + Flow       │ ✅ Rule 3      │ — (hardware)      │
│  Continuous flow > 30 min  │ ✅ Rule 4      │ ✅ Trend detect   │
│  Drip 0.1–0.5 L/min > 5m  │ ✅ Rule 5      │ ✅ Burst detect   │
│  Night flow, no session    │ ✅ Rule 6      │ ✅ Time-pattern   │
│  Sudden flow spike         │ —              │ ✅ Rate-of-change │
│  Gradual consumption rise  │ —              │ ✅ Trend detect   │
│  Mass balance mismatch     │ —              │ ✅ Balance check  │
│  Short burst < 10 sec      │ —              │ ✅ Burst detect   │
│  Sensor noise/debris       │ —              │ ✅ Baseline dev   │
│                                                                 │
│  When BOTH flag:  leak_detector overrides anomaly_detector      │
│  Anomaly alone:   warning level only                            │
│  Leak alone:      emergency level                               │
└─────────────────────────────────────────────────────────────────┘
```

### Priority Order

1. **Leak detection rules** run first (critical, immediate shutoff)
2. **Anomaly detection** runs second (warning, logging, trending)
3. If leak detection triggers → anomaly flags are **suppressed** (redundant)
4. If anomaly triggers but no leak → anomaly alert is the **primary signal**

---

## 10. Validation Checklist

Before deploying anomaly detection, verify:

- [ ] **Rate-of-change:** Simulate sudden faucet open → spike detected within 1 reading
- [ ] **Baseline deviation:** Run normal flow for 5 min, then increase by 3x → z-score > 3.0
- [ ] **Burst detection:** Open faucet for 3 sec → burst flagged; open for 30 sec → no burst flag
- [ ] **Mass balance:** Run 10L through inlet, verify room totals sum within 10%
- [ ] **Time-pattern:** Set clock to 2 AM, flow without RFID → night anomaly flagged
- [ ] **Trend detection:** (Cloud) Inject 7 days of increasing data → slope flagged
- [ ] **ESP-NOW payload:** Room ESP32 sends anomaly_flags → main ESP32 receives and decodes
- [ ] **Firebase push:** Main ESP32 writes to `/anomaly/` path → visible in Firebase Console
- [ ] **Dashboard:** Next.js receives anomaly data → shows in real-time feed
- [ ] **Threshold override:** Change threshold from dashboard → ESP32 picks up new value
- [ ] **No false positives:** Normal faucet use for 30 min → zero anomaly alerts
- [ ] **Escalation:** Warning persists 5 min → escalates to critical

---

## Related Guides

| Guide | Relationship |
|-------|-------------|
| [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md) | Advanced leak rules that complement anomaly detection |
| [module-integration-guide.md](./module-integration-guide.md) | How all ESP32 modules wire together |
| [web-dashboard-alerts-guide.md](./web-dashboard-alerts-guide.md) | Dashboard UI for anomaly visualization |
| [system-architecture.md](./system-architecture.md) | Overall system design |
| [esp32-firmware-complete-guide.md](./esp32-firmware-complete-guide.md) | Base firmware modules |
