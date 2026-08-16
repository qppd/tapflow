#!/usr/bin/env python3
"""
Generate the sample datasets in this folder.

Produces:
  xgboost_sample_dataset.csv             -> 3,000 labeled rows (normal / minor_leak / major_leak)
  isolation_forest_sample_dataset.csv    -> 2,040 unlabeled rows (2,000 normal + 40 injected
                                            anomalies, flagged by the known_anomaly column)

The data models the exact 9-feature schema documented in
docs/ml-complete-guide.md (Feature Set) and mirrors the synthetic-generation
strategy of the guide's `generate_synthetic_data.py`, extended with realistic
per-fixture usage patterns and timestamps.

Stdlib only (random + csv + datetime) so it runs anywhere without numpy/pandas.
Seed is fixed (42) so the CSVs are reproducible byte-for-byte.

Usage:
    python generate_sample_data.py
"""

import csv
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------------
SEED = 42
START_DATE = datetime(2026, 7, 1, 0, 0, 0)   # 30-day window, July 2026
DAYS = 30
TZ_SUFFIX = "+08:00"                          # Asia/Manila (project is PH-based)

FEATURES = [
    "flow_rate",        # L/min
    "duration_seconds", # seconds of continuous flow
    "hour_of_day",      # 0-23
    "day_of_week",      # 0=Mon .. 6=Sun
    "fixture_id",       # 0=inlet, 1=bidet, 2=kitchen, 3=bathroom_shower
    "inlet_ratio",      # inlet_rate / fixture_rate
    "rate_variance",    # variance of last 10 readings
    "is_night_time",    # 1 if hour>=22 or hour<5
    "pulse_trend",      # slope of last 5 pulse counts
]

FIXTURE_NAMES = {0: "inlet", 1: "bidet", 2: "kitchen", 3: "bathroom_shower"}

# Class distribution (matches ml-complete-guide: 85/10/5)
XGB_NORMAL, XGB_MINOR, XGB_MAJOR = 2550, 300, 150
IF_NORMAL, IF_ANOMALIES = 2000, 40          # 10 rows x 4 anomaly types

random.seed(SEED)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def clip(value, lo, hi):
    return max(lo, min(hi, value))


def exp(mean):
    """Exponential sample with the given mean."""
    return random.expovariate(1.0 / mean)


def gauss(mu, sigma):
    return random.gauss(mu, sigma)


def rnd(x, nd=2):
    return round(x, nd)


# ---------------------------------------------------------------------------
# Timestamp / time-of-day
# ---------------------------------------------------------------------------
def pick_hour(label_is_normal, force_hour=None):
    """Realistic hour-of-day. Normal usage clusters in daytime/evening hours;
    leaks are time-independent (they run 24/7), so their hour is flat."""
    if force_hour is not None:
        return force_hour
    if not label_is_normal:
        return random.randint(0, 23)
    hours = list(range(24))
    weights = [0.15] * 6            # 00:00-05:59 (rare night usage)
    weights += [4.0] * 3            # 06:00-08:59 (morning rush)
    weights += [2.5] * 3            # 09:00-11:59
    weights += [2.0] * 5            # 12:00-16:59
    weights += [4.0] * 4            # 17:00-20:59 (evening rush)
    weights += [1.5] * 3            # 21:00-23:59
    return random.choices(hours, weights=weights)[0]


def make_timestamp(hour):
    day = random.randint(0, DAYS - 1)
    ts = START_DATE + timedelta(days=day, hours=hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59))
    return ts.strftime(f"%Y-%m-%dT%H:%M:%S{TZ_SUFFIX}")


def time_features(hour, ts_str):
    ts = datetime.strptime(ts_str, f"%Y-%m-%dT%H:%M:%S{TZ_SUFFIX}")
    return {
        "hour_of_day": hour,
        "day_of_week": ts.weekday(),                     # Mon=0
        "is_night_time": 1 if (hour >= 22 or hour < 5) else 0,
    }


# ---------------------------------------------------------------------------
# Normal usage (shared by both datasets)
# ---------------------------------------------------------------------------
def normal_row():
    """A row of *normal* water usage, conditioned on fixture and time of day."""
    fixture = random.randint(0, 3)
    is_night = random.random() < 0.05   # a few night readings exist but are rare

    # Per-fixture flow/duration distributions (physical, realistic):
    #   inlet  -> aggregate of everything: medium flow, variable duration
    #   bidet  -> short bursts, low flow
    #   kitchen-> medium bursts, medium flow
    #   shower -> long sessions, high flow
    if fixture == 0:      # inlet
        flow = gauss(6.0, 2.5)
        dur = exp(240.0) + 30
    elif fixture == 1:    # bidet
        flow = gauss(2.5, 0.8)
        dur = exp(45.0) + 8
    elif fixture == 2:    # kitchen
        flow = gauss(6.0, 1.5)
        dur = exp(180.0) + 20
    else:                 # bathroom_shower
        flow = gauss(9.0, 2.0)
        dur = exp(480.0) + 60

    flow = clip(flow, 0.3, 15.0)
    dur = int(clip(dur, 5, 3600))
    if is_night:
        flow *= 0.3     # night usage is lighter (ml-complete-guide behaviour)

    return {
        "fixture": fixture,
        "flow": flow,
        "dur": dur,
        "inlet_ratio": random.uniform(1.00, 1.15),       # inlet ~= fixture + 0-15%
        "rate_variance": flow * random.uniform(0.05, 0.35),  # turbulent, varying
        "pulse_trend": gauss(0.0, 1.2),                  # usage starts/stops
    }


# ---------------------------------------------------------------------------
# Leak rows (XGBoost dataset only)
# ---------------------------------------------------------------------------
def minor_leak_row():
    """Drip / slow leak: 0.1-0.5 L/min sustained for 10+ min."""
    fixture = random.randint(1, 3)      # leaks occur at fixtures, not the inlet
    flow = random.uniform(0.1, 0.5)
    return {
        "fixture": fixture,
        "flow": flow,
        "dur": int(exp(1800.0) + 600),                  # 10-60+ min
        "inlet_ratio": random.uniform(1.00, 1.30),      # slight imbalance possible
        "rate_variance": flow * random.uniform(0.005, 0.05),  # steady trickle
        "pulse_trend": gauss(0.0, 0.25),                # flat, sustained
    }


def major_leak_row():
    """Burst / stuck valve: 8-25 L/min sustained."""
    fixture = random.randint(1, 3)
    flow = random.uniform(8.0, 25.0)
    return {
        "fixture": fixture,
        "flow": flow,
        "dur": int(exp(600.0) + 120),                   # minutes to hours
        "inlet_ratio": random.uniform(1.00, 1.20),
        "rate_variance": flow * random.uniform(0.01, 0.06),  # steady high flow
        "pulse_trend": gauss(0.0, 0.4),
    }


# ---------------------------------------------------------------------------
# Anomaly rows (Isolation Forest dataset only) - injected to evaluate the
# unsupervised model. Each deviates from normal in >= 1 dimension.
# ---------------------------------------------------------------------------
def anomaly_row(kind):
    """kind: 0=night burst, 1=hidden leak imbalance, 2=ultra-slow drip,
             3=sensor spike above YF-S201 range"""
    if kind == 0:   # night burst: high flow at 01:00-04:00
        fixture = random.randint(1, 3)
        flow = random.uniform(15.0, 30.0)
        return {
            "fixture": fixture, "flow": flow,
            "dur": int(exp(600.0) + 300),
            "inlet_ratio": random.uniform(1.00, 1.10),
            "rate_variance": flow * random.uniform(0.05, 0.15),
            "pulse_trend": gauss(0.0, 0.5),
            "force_hour": random.randint(1, 4),
        }
    if kind == 1:   # hidden leak: inlet flows while fixtures read near zero
        fixture = 0
        flow = random.uniform(0.5, 2.0)
        return {
            "fixture": fixture, "flow": flow,
            "dur": int(exp(3600.0) + 3600),
            "inlet_ratio": random.uniform(2.0, 4.0),    # unmatched by fixtures
            "rate_variance": flow * random.uniform(0.01, 0.05),
            "pulse_trend": gauss(0.0, 0.2),
            "force_hour": None,
        }
    if kind == 2:   # ultra-slow drip at night: below physical minimum flow
        fixture = random.randint(1, 3)
        flow = random.uniform(0.02, 0.08)
        return {
            "fixture": fixture, "flow": flow,
            "dur": int(exp(7200.0) + 43200),            # 12+ hours
            "inlet_ratio": random.uniform(1.0, 1.5),
            "rate_variance": flow * 0.005,
            "pulse_trend": gauss(0.0, 0.1),
            "force_hour": random.randint(0, 5),         # night drip
        }
    # kind == 3: sensor spike / fault: flow beyond YF-S201 max range (~30 L/min)
    fixture = random.randint(1, 3)
    flow = random.uniform(30.0, 45.0)
    return {
        "fixture": fixture, "flow": flow,
        "dur": random.randint(5, 60),                   # brief, then sensor dies
        "inlet_ratio": random.uniform(0.8, 1.1),
        "rate_variance": flow * random.uniform(0.3, 0.6),
        "pulse_trend": gauss(5.0, 2.0),                 # sharply rising
        "force_hour": None,
    }


# ---------------------------------------------------------------------------
# Row assembly
# ---------------------------------------------------------------------------
def build_row(base, label_is_normal, force_hour=None):
    hour = pick_hour(label_is_normal, force_hour)
    ts = make_timestamp(hour)
    t = time_features(hour, ts)
    return {
        "timestamp": ts,
        "flow_rate": rnd(base["flow"]),
        "duration_seconds": int(base["dur"]),
        "hour_of_day": t["hour_of_day"],
        "day_of_week": t["day_of_week"],
        "fixture_id": int(base["fixture"]),
        "inlet_ratio": rnd(base["inlet_ratio"], 3),
        "rate_variance": rnd(base["rate_variance"], 3),
        "is_night_time": t["is_night_time"],
        "pulse_trend": rnd(base["pulse_trend"], 3),
    }


def write_csv(path, rows):
    cols = ["timestamp"] + FEATURES
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):>5} rows -> {path}")


def main():
    # --- XGBoost: 3-class supervised dataset --------------------------------
    xgb_rows = []
    for _ in range(XGB_NORMAL):
        r = build_row(normal_row(), label_is_normal=True)
        r["label"] = 0          # normal
        xgb_rows.append(r)
    for _ in range(XGB_MINOR):
        r = build_row(minor_leak_row(), label_is_normal=False)
        r["label"] = 1          # minor_leak
        xgb_rows.append(r)
    for _ in range(XGB_MAJOR):
        r = build_row(major_leak_row(), label_is_normal=False)
        r["label"] = 2          # major_leak
        xgb_rows.append(r)

    random.shuffle(xgb_rows)
    xgb_rows.sort(key=lambda r: r["timestamp"])     # enables temporal split demo

    cols = ["timestamp"] + FEATURES + ["label"]
    with open("xgboost_sample_dataset.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(xgb_rows)
    print(f"wrote {len(xgb_rows):>5} rows -> xgboost_sample_dataset.csv")

    # --- Isolation Forest: normal-only training + injected anomalies --------
    if_rows = []
    for _ in range(IF_NORMAL):
        r = build_row(normal_row(), label_is_normal=True)
        r["known_anomaly"] = 0
        if_rows.append(r)
    for kind in range(4):
        for _ in range(IF_ANOMALIES // 4):
            base = anomaly_row(kind)
            r = build_row(base, label_is_normal=False,
                          force_hour=base.pop("force_hour"))
            r["known_anomaly"] = 1
            if_rows.append(r)

    random.shuffle(if_rows)
    if_rows.sort(key=lambda r: r["timestamp"])

    cols = ["timestamp"] + FEATURES + ["known_anomaly"]
    with open("isolation_forest_sample_dataset.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(if_rows)
    print(f"wrote {len(if_rows):>5} rows -> isolation_forest_sample_dataset.csv")


if __name__ == "__main__":
    main()
