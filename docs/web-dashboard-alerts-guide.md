# Web Dashboard Alerts Guide — TapFlow

> **Purpose:** Next.js dashboard implementation for real-time anomaly detection + leak detection visualization, alert management, and threshold configuration.
> **Builds on:** [anomaly-detection-guide.md](./anomaly-detection-guide.md), [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md), [module-integration-guide.md](./module-integration-guide.md)

---

## Table of Contents

1. [Dashboard Overview](#1-dashboard-overview)
2. [Tech Stack](#2-tech-stack)
3. [Firebase Integration](#3-firebase-integration)
4. [Page Layout & Navigation](#4-page-layout--navigation)
5. [Components](#5-components)
6. [Real-Time Alert Feed](#6-real-time-alert-feed)
7. [Room Status Cards](#7-room-status-cards)
8. [Flow Rate Charts](#8-flow-rate-charts)
9. [Anomaly Score Gauge](#9-anomaly-score-gauge)
10. [Trend Analysis Panel](#10-trend-analysis-panel)
11. [Threshold Configuration Panel](#11-threshold-configuration-panel)
12. [Alert History & Audit Log](#12-alert-history--audit-log)
13. [Push Notifications](#13-push-notifications)
14. [Responsive Design](#14-responsive-design)
15. [Validation Checklist](#15-validation-checklist)

---

## 1. Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAPFLOW DASHBOARD LAYOUT                     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Header: TapFlow | Status: Online | Last update: 2s ago  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐  │
│  │  Room 1     │  Room 2     │  Room 3     │  System Status  │  │
│  │  Bathroom   │  Kitchen    │  Shower     │  Main ESP32     │  │
│  │  Flow: 2.3  │  Flow: 0.0  │  Flow: 1.1  │  Inlet: 3.4    │  │
│  │  Vol: 456ml │  Vol: 0ml   │  Vol: 210ml │  Balance: 98%  │  │
│  │  Status: ✅ │  Status: ✅ │  Status: ✅ │  WiFi: ✅       │  │
│  │  Leak: None │  Leak: None │  Leak: None │  ESP-NOW: 3/3  │  │
│  │  Anomaly: 0 │  Anomaly: 0 │  Anomaly: 0 │  Uptime: 2d 4h │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────┬───────────────────────┐  │
│  │  Flow Rate Chart (real-time)     │  Anomaly Score Gauge  │  │
│  │  ┌─────────────────────────────┐ │  ┌───────────────────┐│  │
│  │  │  ╱╲    ╱╲                  │ │  │     ┌─────┐       ││  │
│  │  │ ╱  ╲╱╱  ╲    ╱╲           │ │  │    ╱       ╲      ││  │
│  │  │╱        ╲╱╱  ╲  ╲╱╲       │ │  │   │  0.45  │     ││  │
│  │  │              ╲╱    ╲      │ │  │    ╲       ╱      ││  │
│  │  │                     ╲     │ │  │     └─────┘       ││  │
│  │  └─────────────────────────────┘ │  │   Normal         ││  │
│  │  Room 1 | Room 2 | Room 3 | Inlet│  │   z-score: 0.45  ││  │
│  └───────────────────────────────────┴───────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Alert Feed (real-time)                                   │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 🔴 EMERGENCY | Room 2 | Solenoid stuck open        │  │  │
│  │  │    Flow: 2.3 L/min with solenoid OFF               │  │  │
│  │  │    Detected: 2 min ago | [Acknowledge] [Shutoff]   │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ ⚠️ WARNING  | Room 1 | Anomaly spike detected      │  │  │
│  │  │    Flow rate spike: 8.5 L/min (threshold: 5.0)     │  │  │
│  │  │    z-score: 4.2 | Detected: 5 min ago | [Dismiss]  │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ ℹ️ INFO     | System | Mass balance OK              │  │  │
│  │  │    Balance: 2.1% (within normal range)              │  │  │
│  │  │    Detected: 15 min ago | [Dismiss]                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Trend Analysis (7-day)                                  │  │
│  │  Room 1: ▲ +12% week-over-week | Room 2: — 0%          │  │
│  │  Room 3: ▼ -5% week-over-week  | Total: ▲ +8%          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Settings: Thresholds | Calibration | Alerts | Account   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | Next.js 14+ (App Router) | React framework with SSR |
| **Language** | TypeScript | Type safety |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Recharts | Real-time flow rate + trend charts |
| **Firebase SDK** | firebase (JS SDK v10+) | Client-side Firebase integration |
| **Auth** | Firebase Authentication | Email/password + Google sign-in |
| **Database** | Firebase Realtime Database | Real-time data sync |
| **Hosting** | Vercel | Auto-deploy from Git |
| **Notifications** | Web Notifications API + Firebase Cloud Messaging | Push alerts |
| **State** | React hooks (useState, useEffect) | Component state |
| **Date/Time** | date-fns | Timestamp formatting |

### Firebase Config (`.env.local`)

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

---

## 3. Firebase Integration

### 3.1 Firebase Initialization

```typescript
// lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const db = getDatabase(app);
export const auth = getAuth(app);
```

### 3.2 Real-Time Listeners

```typescript
// hooks/useRoomData.ts
import { ref, onValue, off } from 'firebase/database';
import { db } from '@/lib/firebase';

// Listen to room sensor data (updates every 5 sec)
export function useRoomData(roomId: number) {
  const [data, setData] = useState<RoomData | null>(null);

  useEffect(() => {
    const roomRef = ref(db, `rooms/${roomId}/data`);
    const unsub = onValue(roomRef, (snapshot) => {
      setData(snapshot.val());
    });
    return () => off(roomRef, 'value', unsub);
  }, [roomId]);

  return data;
}

// Listen to room anomaly data
export function useRoomAnomaly(roomId: number) {
  const [anomaly, setAnomaly] = useState<RoomAnomaly | null>(null);

  useEffect(() => {
    const anomalyRef = ref(db, `rooms/${roomId}/anomaly`);
    const unsub = onValue(anomalyRef, (snapshot) => {
      setAnomaly(snapshot.val());
    });
    return () => off(anomalyRef, 'value', unsub);
  }, [roomId]);

  return anomaly;
}

// Listen to active alerts (real-time feed)
export function useActiveAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    const alertsRef = ref(db, 'alerts/active');
    const unsub = onValue(alertsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setAlerts(Object.entries(data).map(([id, alert]) => ({
          id,
          ...alert as AlertData,
        })));
      } else {
        setAlerts([]);
      }
    });
    return () => off(alertsRef, 'value', unsub);
  }, []);

  return alerts;
}

// Listen to global anomaly data
export function useGlobalAnomaly() {
  const [global, setGlobal] = useState<GlobalAnomaly | null>(null);

  useEffect(() => {
    const globalRef = ref(db, 'anomaly/global');
    const unsub = onValue(globalRef, (snapshot) => {
      setGlobal(snapshot.val());
    });
    return () => off(globalRef, 'value', unsub);
  }, []);

  return global;
}
```

### 3.3 Data Types

```typescript
// types/index.ts
export interface RoomData {
  flow_rate_lpm: number;
  volume_ml: number;
  ts: number;
}

export interface RoomAnomaly {
  spike: boolean;
  baseline: boolean;
  burst: boolean;
  zscore: number;
  rate_of_change: number;
  ts: number;
}

export interface Alert {
  id: string;
  type: 'leak' | 'anomaly' | 'combined';
  rule: string;
  severity: 'info' | 'warning' | 'alert' | 'critical' | 'emergency';
  room_id: number;
  device_id: string;
  ts: number;
  detail: string;
  flow_rate_lpm: number;
  threshold: number;
  anomaly_context?: {
    zscore: number;
    spike: boolean;
    burst: boolean;
  };
  acknowledged: boolean;
  resolved: boolean;
  resolved_at: number | null;
}

export interface GlobalAnomaly {
  mass_balance: {
    inlet_ml: number;
    rooms_total_ml: number;
    balance_ml: number;
    balance_pct: number;
    ts: number;
  };
  time_pattern: {
    period: string;
    usage_ml: number;
    baseline_ml: number;
    deviation_pct: number;
    ts: number;
  };
  multi_room: {
    rooms_active: number[];
    flagged: boolean;
    ts: number;
  };
  trend: {
    slope_lpm: number;
    weekly_increase_pct: number;
    last_check: number;
  };
}

export interface SystemStatus {
  device_id: string;
  uptime_sec: number;
  free_heap: number;
  wifi_rssi: number;
  sensors_ok: boolean;
  espnow_rooms_online: number;
  firebase_connected: boolean;
}
```

---

## 4. Page Layout & Navigation

### 4.1 App Router Structure

```
app/
├── layout.tsx              Root layout (auth, nav)
├── page.tsx                Dashboard home
├── login/
│   └── page.tsx            Firebase Auth login
├── rooms/
│   └── [id]/
│       └── page.tsx        Individual room detail
├── alerts/
│   ├── page.tsx            Active alerts
│   └── history/
│       └── page.tsx        Alert history
├── trends/
│   └── page.tsx            Trend analysis charts
├── settings/
│   ├── page.tsx            Threshold configuration
│   └── calibration/
│       └── page.tsx        Sensor calibration
└── api/
    └── config/
        └── route.ts        API for threshold updates
```

### 4.2 Navigation Sidebar

```tsx
// components/Navigation.tsx
const navItems = [
  { label: 'Dashboard', href: '/', icon: '🏠' },
  { label: 'Rooms', href: '/rooms', icon: '🚿' },
  { label: 'Alerts', href: '/alerts', icon: '🔔', badge: activeAlertCount },
  { label: 'Trends', href: '/trends', icon: '📈' },
  { label: 'Settings', href: '/settings', icon: '⚙️' },
];
```

---

## 5. Components

### 5.1 Component Tree

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPONENT TREE                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  <DashboardLayout>                                              │
│    ├── <AuthProvider>                                           │
│    │   ├── <Navigation />                                       │
│    │   │   ├── <NavItems />                                     │
│    │   │   └── <AlertBadge count={activeAlerts.length} />       │
│    │   │                                                       │
│    │   ├── <Header>                                             │
│    │   │   ├── <SystemStatus />                                 │
│    │   │   ├── <LastUpdate />                                   │
│    │   │   └── <ConnectionStatus />                             │
│    │   │                                                       │
│    │   ├── <RoomCardsGrid>                                      │
│    │   │   ├── <RoomCard roomId={1} />                          │
│    │   │   │   ├── <FlowRateDisplay />                          │
│    │   │   │   ├── <VolumeDisplay />                            │
│    │   │   │   ├── <LeakStatus />                               │
│    │   │   │   ├── <AnomalyIndicator />                         │
│    │   │   │   └── <SessionStatus />                            │
│    │   │   ├── <RoomCard roomId={2} />                          │
│    │   │   └── <RoomCard roomId={3} />                          │
│    │   │                                                       │
│    │   ├── <SystemStatusCard />                                 │
│    │   │   ├── <InletFlowRate />                                │
│    │   │   ├── <MassBalanceGauge />                             │
│    │   │   ├── <ESPNowStatus />                                 │
│    │   │   └── <FirebaseStatus />                               │
│    │   │                                                       │
│    │   ├── <MainContent>                                        │
│    │   │   ├── <FlowRateChart />                                │
│    │   │   │   ├── <ChartLine roomId={1} />                     │
│    │   │   │   ├── <ChartLine roomId={2} />                     │
│    │   │   │   ├── <ChartLine roomId={3} />                     │
│    │   │   │   └── <ChartLine inlet />                          │
│    │   │   │                                                   │
│    │   │   └── <AnomalyScoreGauge />                            │
│    │   │       ├── <GaugeRing />                                │
│    │   │       ├── <ZScoreDisplay />                            │
│    │   │       └── <AnomalyLabel />                             │
│    │   │                                                       │
│    │   ├── <AlertFeed />                                        │
│    │   │   └── <AlertCard />                                    │
│    │   │       ├── <SeverityBadge />                            │
│    │   │       ├── <AlertDetail />                              │
│    │   │       ├── <AlertActions />                             │
│    │   │       │   ├── <AcknowledgeButton />                    │
│    │   │       │   ├── <ShutoffButton />                        │
│    │   │       │   └── <DismissButton />                        │
│    │   │       └── <AlertTimestamp />                           │
│    │   │                                                       │
│    │   ├── <TrendPanel />                                       │
│    │   │   ├── <WeeklyComparison />                             │
│    │   │   ├── <TrendChart />                                   │
│    │   │   └── <TrendAlerts />                                  │
│    │   │                                                       │
│    │   └── <ThresholdConfig />                                  │
│    │       ├── <SpikeThresholdSlider />                         │
│    │       ├── <ZScoreThresholdSlider />                        │
│    │       ├── <BalanceThresholdSliders />                      │
│    │       └── <SaveConfigButton />                             │
│    │                                                           │
│    └── <Footer />                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Real-Time Alert Feed

### 6.1 Alert Feed Component

```tsx
// components/AlertFeed.tsx
'use client';
import { useActiveAlerts } from '@/hooks/useRoomData';
import { AlertCard } from './AlertCard';

export function AlertFeed() {
  const alerts = useActiveAlerts();

  // Sort by severity (emergency first) then by timestamp (newest first)
  const sorted = alerts.sort((a, b) => {
    const severityOrder = { emergency: 0, critical: 1, alert: 2, warning: 3, info: 4 };
    const sevDiff = severityOrder[a.severity] - severityOrder[b.severity];
    if (sevDiff !== 0) return sevDiff;
    return b.ts - a.ts;
  });

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Active Alerts</h2>
      {sorted.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          ✅ No active alerts — all systems normal
        </div>
      ) : (
        sorted.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))
      )}
    </div>
  );
}
```

### 6.2 Alert Card Component

```tsx
// components/AlertCard.tsx
'use client';
import { ref, update } from 'firebase/database';
import { db } from '@/lib/firebase';
import { SeverityBadge } from './SeverityBadge';
import { formatDistanceToNow } from 'date-fns';

interface AlertCardProps {
  alert: Alert;
}

export function AlertCard({ alert }: AlertCardProps) {
  const handleAcknowledge = async () => {
    await update(ref(db, `alerts/active/${alert.id}`), {
      acknowledged: true,
      acknowledged_at: Date.now(),
    });
  };

  const handleShutoff = async () => {
    // Send shutoff command via Firebase
    await update(ref(db, `commands/tapflow-main`), {
      cmd: 'shutoff',
      room_id: alert.room_id,
      ts: Date.now(),
    });
    await handleAcknowledge();
  };

  const handleDismiss = async () => {
    // Move to history
    await update(ref(db, `alerts/history/${alert.id}`), {
      ...alert,
      resolved: true,
      resolved_at: Date.now(),
    });
    // Remove from active
    await update(ref(db, `alerts/active/${alert.id}`), null);
  };

  const borderColor = {
    emergency: 'border-red-500 bg-red-50',
    critical: 'border-red-400 bg-red-50',
    alert: 'border-orange-400 bg-orange-50',
    warning: 'border-yellow-400 bg-yellow-50',
    info: 'border-blue-400 bg-blue-50',
  }[alert.severity];

  return (
    <div className={`border-l-4 ${borderColor} rounded-r-lg p-4 shadow-sm`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={alert.severity} />
            <span className="text-sm font-medium text-gray-600">
              Room {alert.room_id} — {alert.type}
            </span>
          </div>
          <p className="text-sm text-gray-800 mb-1">{alert.detail}</p>
          <p className="text-xs text-gray-500">
            Detected {formatDistanceToNow(alert.ts)} ago
            {alert.anomaly_context && (
              <span> | z-score: {alert.anomaly_context.zscore.toFixed(2)}</span>
            )}
          </p>
        </div>
        <div className="flex gap-2 ml-4">
          {!alert.acknowledged && (
            <button
              onClick={handleAcknowledge}
              className="px-3 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
            >
              Acknowledge
            </button>
          )}
          {(alert.severity === 'emergency' || alert.severity === 'critical') && (
            <button
              onClick={handleShutoff}
              className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
            >
              Emergency Shutoff
            </button>
          )}
          <button
            onClick={handleDismiss}
            className="px-3 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 6.3 Severity Badge

```tsx
// components/SeverityBadge.tsx
const severityConfig = {
  emergency: { label: '🚨 EMERGENCY', color: 'bg-red-600 text-white', pulse: true },
  critical:  { label: '🔴 CRITICAL',  color: 'bg-red-500 text-white', pulse: true },
  alert:     { label: '🟠 ALERT',     color: 'bg-orange-500 text-white', pulse: false },
  warning:   { label: '⚠️ WARNING',   color: 'bg-yellow-500 text-black', pulse: false },
  info:      { label: 'ℹ️ INFO',      color: 'bg-blue-500 text-white', pulse: false },
};

export function SeverityBadge({ severity }: { severity: string }) {
  const config = severityConfig[severity as keyof typeof severityConfig];
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold ${config.color} ${
      config.pulse ? 'animate-pulse' : ''
    }`}>
      {config.label}
    </span>
  );
}
```

---

## 7. Room Status Cards

### 7.1 Room Card Component

```tsx
// components/RoomCard.tsx
'use client';
import { useRoomData, useRoomAnomaly } from '@/hooks/useRoomData';

interface RoomCardProps {
  roomId: number;
  roomName: string;
}

export function RoomCard({ roomId, roomName }: RoomCardProps) {
  const data = useRoomData(roomId);
  const anomaly = useRoomAnomaly(roomId);

  const statusColor = !data ? 'text-gray-400' :
    data.flow_rate_lpm > 0 ? 'text-blue-500' : 'text-green-500';

  const anomalyLevel = anomaly ? (
    anomaly.spike ? '🔴 Spike' :
    anomaly.baseline ? '⚠️ Deviation' :
    anomaly.burst ? '⚡ Burst' :
    '✅ Normal'
  ) : '—';

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-lg">Room {roomId}</h3>
        <span className="text-sm text-gray-500">{roomName}</span>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-600">Flow Rate:</span>
          <span className={`font-mono ${statusColor}`}>
            {data?.flow_rate_lpm.toFixed(1) ?? '—'} L/min
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Volume:</span>
          <span className="font-mono">
            {data?.volume_ml ?? '—'} ml
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Anomaly:</span>
          <span className="text-sm">{anomalyLevel}</span>
        </div>

        {anomaly && anomaly.zscore > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-600">Z-Score:</span>
            <span className={`font-mono text-sm ${
              anomaly.zscore > 3 ? 'text-red-500' :
              anomaly.zscore > 2 ? 'text-yellow-500' : 'text-green-500'
            }`}>
              {anomaly.zscore.toFixed(2)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 8. Flow Rate Charts

### 8.1 Real-Time Flow Chart

```tsx
// components/FlowRateChart.tsx
'use client';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface FlowDataPoint {
  time: string;
  room1: number;
  room2: number;
  room3: number;
  inlet: number;
}

export function FlowRateChart() {
  const [data, setData] = useState<FlowDataPoint[]>([]);

  useEffect(() => {
    // Poll Firebase every 5 sec for flow rate history
    // Store last 60 readings (5 min of data)
    const interval = setInterval(() => {
      // Fetch from Firebase or use onValue listener
      // Append new data point, remove oldest if > 60
      setData(prev => {
        const newPoint = getCurrentFlowRates(); // from Firebase listeners
        const updated = [...prev, newPoint];
        return updated.slice(-60); // keep last 60 points
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold mb-4">Flow Rate (Real-Time)</h3>
      <LineChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis label={{ value: 'L/min', angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="room1" stroke="#3B82F6" name="Room 1" dot={false} />
        <Line type="monotone" dataKey="room2" stroke="#10B981" name="Room 2" dot={false} />
        <Line type="monotone" dataKey="room3" stroke="#F59E0B" name="Room 3" dot={false} />
        <Line type="monotone" dataKey="inlet" stroke="#EF4444" name="Inlet" dot={false} strokeWidth={2} />
      </LineChart>
    </div>
  );
}
```

### 8.2 Anomaly Markers on Chart

Add visual markers when anomalies are detected:

```tsx
// Add to FlowRateChart
{data.map((point, index) =>
  point.anomalySpike && (
    <ReferenceDot
      key={`spike-${index}`}
      x={point.time}
      y={point.room1}
      r={6}
      fill="red"
      stroke="red"
    />
  )
)}
```

---

## 9. Anomaly Score Gauge

### 9.1 Gauge Component

```tsx
// components/AnomalyScoreGauge.tsx
'use client';
import { useGlobalAnomaly } from '@/hooks/useRoomData';

export function AnomalyScoreGauge() {
  const global = useGlobalAnomaly();

  // Compute composite anomaly score (0-100)
  const score = computeAnomalyScore(global);

  const color = score > 70 ? '#EF4444' :
                score > 40 ? '#F59E0B' : '#10B981';

  const label = score > 70 ? 'High Risk' :
                score > 40 ? 'Moderate' : 'Normal';

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold mb-4">Anomaly Score</h3>
      <div className="flex items-center justify-center">
        <svg width="200" height="120" viewBox="0 0 200 120">
          {/* Gauge background */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="12"
          />
          {/* Gauge fill */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeDasharray={`${(score / 100) * 251.2} 251.2`}
          />
          {/* Score text */}
          <text x="100" y="85" textAnchor="middle" className="text-2xl font-bold">
            {score.toFixed(0)}
          </text>
          <text x="100" y="105" textAnchor="middle" className="text-sm" fill="#6B7280">
            {label}
          </text>
        </svg>
      </div>
      <div className="mt-4 space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Mass Balance:</span>
          <span>{global?.mass_balance?.balance_pct?.toFixed(1) ?? '—'}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Time Pattern:</span>
          <span>{global?.time_pattern?.period ?? '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Multi-Room:</span>
          <span>{global?.multi_room?.flagged ? '⚠️ Yes' : '✅ No'}</span>
        </div>
      </div>
    </div>
  );
}

function computeAnomalyScore(global: GlobalAnomaly | null): number {
  if (!global) return 0;
  let score = 0;

  // Mass balance contribution (0-40 points)
  const balance = Math.abs(global.mass_balance?.balance_pct ?? 0);
  if (balance > 20) score += 40;
  else if (balance > 10) score += 20;
  else if (balance > 5) score += 10;

  // Time pattern contribution (0-30 points)
  const timeDev = Math.abs(global.time_pattern?.deviation_pct ?? 0);
  if (timeDev > 200) score += 30;
  else if (timeDev > 100) score += 15;
  else if (timeDev > 50) score += 5;

  // Multi-room contribution (0-20 points)
  if (global.multi_room?.flagged) score += 20;

  // Trend contribution (0-10 points)
  const trend = Math.abs(global.trend?.weekly_increase_pct ?? 0);
  if (trend > 30) score += 10;
  else if (trend > 15) score += 5;

  return Math.min(score, 100);
}
```

---

## 10. Trend Analysis Panel

### 10.1 Weekly Comparison

```tsx
// components/TrendPanel.tsx
'use client';
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface WeeklyData {
  room: string;
  thisWeek: number;
  lastWeek: number;
  change: number;
}

export function TrendPanel() {
  const [data, setData] = useState<WeeklyData[]>([]);

  useEffect(() => {
    // Fetch from Firebase: /baselines/daily/ for last 14 days
    // Compute this week vs last week per room
    fetchWeeklyComparison().then(setData);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold mb-4">Weekly Consumption Trend</h3>

      <BarChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="room" />
        <YAxis label={{ value: 'Liters', angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="lastWeek" fill="#93C5FD" name="Last Week" />
        <Bar dataKey="thisWeek" fill="#3B82F6" name="This Week" />
      </BarChart>

      <div className="mt-4 space-y-2">
        {data.map((d) => (
          <div key={d.room} className="flex items-center justify-between text-sm">
            <span>{d.room}</span>
            <span className={d.change > 15 ? 'text-red-500 font-semibold' :
                            d.change < -5 ? 'text-green-500' : 'text-gray-600'}>
              {d.change > 0 ? '▲' : d.change < 0 ? '▼' : '—'}
              {' '}{Math.abs(d.change).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 10.2 Trend Alert Detection

```tsx
// Alert when weekly increase > 15%
{data.map((d) =>
  d.change > 15 && (
    <div key={`trend-alert-${d.room}`}
         className="bg-yellow-50 border border-yellow-200 rounded p-3 mt-2">
      ⚠️ {d.room} consumption increased {d.change.toFixed(1)}% this week.
      Possible slow leak — recommend inspection.
    </div>
  )
)}
```

---

## 11. Threshold Configuration Panel

### 11.1 Settings Component

```tsx
// components/ThresholdConfig.tsx
'use client';
import { useState, useEffect } from 'react';
import { ref, get, set } from 'firebase/database';
import { db } from '@/lib/firebase';

interface Thresholds {
  spike_threshold: number;
  zscore_anomaly: number;
  zscore_warning: number;
  balance_warning_pct: number;
  balance_anomaly_pct: number;
  night_start_hour: number;
  night_end_hour: number;
  continuous_flow_min: number;
  drip_min_rate: number;
  drip_max_rate: number;
  drip_min_time: number;
}

export function ThresholdConfig() {
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const configRef = ref(db, 'config/anomaly');
    get(configRef).then((snapshot) => {
      if (snapshot.exists()) {
        setThresholds(snapshot.val());
      }
    });
  }, []);

  const handleSave = async () => {
    if (!thresholds) return;
    setSaving(true);
    const configRef = ref(db, 'config/anomaly');
    await set(configRef, thresholds);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  if (!thresholds) return <div>Loading...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-lg font-semibold mb-4">Detection Thresholds</h2>

      <div className="space-y-4">
        <ThresholdSlider
          label="Spike Threshold"
          value={thresholds.spike_threshold}
          min={1} max={20} step={0.5}
          unit="L/min/sec"
          onChange={(v) => setThresholds({ ...thresholds, spike_threshold: v })}
        />
        <ThresholdSlider
          label="Z-Score Anomaly"
          value={thresholds.zscore_anomaly}
          min={1.5} max={5} step={0.1}
          unit=""
          onChange={(v) => setThresholds({ ...thresholds, zscore_anomaly: v })}
        />
        <ThresholdSlider
          label="Mass Balance Warning"
          value={thresholds.balance_warning_pct}
          min={5} max={30} step={1}
          unit="%"
          onChange={(v) => setThresholds({ ...thresholds, balance_warning_pct: v })}
        />
        <ThresholdSlider
          label="Mass Balance Anomaly"
          value={thresholds.balance_anomaly_pct}
          min={10} max={50} step={1}
          unit="%"
          onChange={(v) => setThresholds({ ...thresholds, balance_anomaly_pct: v })}
        />
        <ThresholdSlider
          label="Continuous Flow Limit"
          value={thresholds.continuous_flow_min}
          min={10} max={120} step={5}
          unit="minutes"
          onChange={(v) => setThresholds({ ...thresholds, continuous_flow_min: v })}
        />
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-4 py-2 rounded font-medium ${
            saved ? 'bg-green-500 text-white' :
            saving ? 'bg-gray-300' : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {saved ? '✅ Saved' : saving ? 'Saving...' : 'Save Configuration'}
        </button>
        {saved && (
          <span className="text-sm text-green-600">
            Changes applied to ESP32 within 10 seconds
          </span>
        )}
      </div>
    </div>
  );
}

function ThresholdSlider({ label, value, min, max, step, unit, onChange }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm text-gray-500">{value} {unit}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full"
      />
    </div>
  );
}
```

---

## 12. Alert History & Audit Log

### 12.1 History Page

```tsx
// app/alerts/history/page.tsx
'use client';
import { useState, useEffect } from 'react';
import { ref, query, orderByChild, limitToLast, onValue } from 'firebase/database';
import { db } from '@/lib/firebase';

export default function AlertHistory() {
  const [history, setHistory] = useState<Alert[]>([]);
  const [filter, setFilter] = useState('all'); // all, leak, anomaly

  useEffect(() => {
    const historyRef = query(
      ref(db, 'alerts/history'),
      orderByChild('ts'),
      limitToLast(100)
    );
    const unsub = onValue(historyRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setHistory(Object.entries(data).map(([id, alert]) => ({
          id, ...alert as AlertData,
        })));
      }
    });
    return () => unsub();
  }, []);

  const filtered = filter === 'all' ? history :
    history.filter(a => a.type === filter);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Alert History</h1>

      <div className="flex gap-2 mb-4">
        {['all', 'leak', 'anomaly'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm ${
              filter === f ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {filtered.map((alert) => (
          <div key={alert.id} className="bg-white rounded shadow p-3 text-sm">
            <div className="flex justify-between">
              <span className="font-medium">{alert.rule}</span>
              <span className="text-gray-500">
                {new Date(alert.ts).toLocaleString()}
              </span>
            </div>
            <p className="text-gray-600 mt-1">{alert.detail}</p>
            {alert.resolved_at && (
              <p className="text-green-600 text-xs mt-1">
                Resolved: {new Date(alert.resolved_at).toLocaleString()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 13. Push Notifications

### 13.1 Browser Notifications

```typescript
// lib/notifications.ts
export function requestNotificationPermission() {
  if ('Notification' in window) {
    Notification.requestPermission();
  }
}

export function sendNotification(title: string, body: string, severity: string) {
  if (Notification.permission === 'granted') {
    const icon = severity === 'emergency' ? '🚨' :
                 severity === 'critical' ? '🔴' :
                 severity === 'warning' ? '⚠️' : 'ℹ️';

    new Notification(`${icon} ${title}`, {
      body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'tapflow-alert',   // replaces previous notification
      renotify: true,          // vibrate on replacement
    });
  }
}
```

### 13.2 Firebase Cloud Messaging (FCM)

```typescript
// lib/fcm.ts
import { getMessaging, getToken } from 'firebase/messaging';

export async function setupFCM() {
  const messaging = getMessaging();
  const token = await getToken(messaging, {
    vapidKey: 'your-vapid-key',
  });
  // Send token to Firebase RTDB for server-side push
  // /users/{uid}/fcmToken = token
  return token;
}
```

---

## 14. Responsive Design

### 14.1 Breakpoints

| Breakpoint | Layout |
|------------|--------|
| Mobile (< 640px) | Single column, stacked cards, collapsible nav |
| Tablet (640–1024px) | 2-column grid, side nav |
| Desktop (> 1024px) | 3-column grid, full nav, charts side-by-side |

### 14.2 Mobile-First Components

```tsx
// Room cards: 1 col on mobile, 3 col on desktop
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  <RoomCard roomId={1} roomName="Bathroom" />
  <RoomCard roomId={2} roomName="Kitchen" />
  <RoomCard roomId={3} roomName="Shower" />
</div>

// Charts: full width on mobile, half width on desktop
<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
  <FlowRateChart />
  <AnomalyScoreGauge />
</div>
```

---

## 15. Validation Checklist

- [ ] **Firebase auth:** Login with email/password works, logout works
- [ ] **Real-time sync:** Flow rate changes on dashboard within 5 sec of sensor change
- [ ] **Alert feed:** New alert appears within 5 sec of Firebase write
- [ ] **Alert acknowledge:** Clicking acknowledge updates Firebase, UI reflects change
- [ ] **Emergency shutoff:** Button sends command to Firebase, ESP32 receives within 2 sec
- [ ] **Severity badges:** Correct colors and labels for all 5 severity levels
- [ ] **Pulse animation:** Emergency/critical badges pulse visually
- [ ] **Flow chart:** Real-time line chart updates every 5 sec
- [ ] **Anomaly gauge:** Score updates in real-time, color changes at thresholds
- [ ] **Trend panel:** Weekly comparison shows correct data
- [ ] **Threshold config:** Sliders work, save writes to Firebase, ESP32 picks up within 10 sec
- [ ] **Alert history:** Past alerts visible, filterable by type
- [ ] **Push notifications:** Browser notification appears on alert (if permission granted)
- [ ] **Responsive:** Works on mobile (single column), tablet (2 col), desktop (3 col)
- [ ] **Error states:** Firebase offline → shows "reconnecting" banner
- [ ] **Loading states:** Skeleton loaders while Firebase data loads
- [ ] **Empty states:** "No active alerts" shown when alert feed is empty
- [ ] **Auth protection:** Unauthenticated users redirected to login
- [ ] **Room offline badge:** Room shows "offline" when ESP-NOW data stops

---

## Related Guides

| Guide | Relationship |
|-------|-------------|
| [anomaly-detection-guide.md](./anomaly-detection-guide.md) | Anomaly data consumed by dashboard |
| [leak-detection-advanced-guide.md](./leak-detection-advanced-guide.md) | Leak alerts displayed by dashboard |
| [module-integration-guide.md](./module-integration-guide.md) | ESP32 modules that produce dashboard data |
| [system-architecture.md](./system-architecture.md) | Overall system design |
| [setup.md](./setup.md) | Firebase + Vercel deployment steps |
