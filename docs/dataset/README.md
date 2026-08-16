# Sample Datasets — XGBoost & Isolation Forest

> **Location:** `docs/dataset/` — part of the WMLDAD smart water monitoring project.
> These are **synthetic sample datasets** that let you prototype, train, and test the
> ML pipeline from [`docs/ml-complete-guide.md`](../ml-complete-guide.md) **before**
> you have weeks of real water-usage data. They mirror the exact 9-feature schema the
> RPi backend (`rpi/ml_inference.py`) feeds the models at inference time.

---

## 1. Files in This Folder

| File | Rows | Purpose |
|------|------|---------|
| `xgboost_sample_dataset.csv` | 3,000 | **Supervised** training data for the XGBoost 3-class classifier (`normal` / `minor_leak` / `major_leak`). Every row has a ground-truth `label`. |
| `isolation_forest_sample_dataset.csv` | 2,040 | **Unsupervised** training data for Isolation Forest: 2,000 normal readings + 40 injected anomalies. The `known_anomaly` column exists **only for evaluation** — Isolation Forest is fitted with no labels. |
| `generate_sample_data.py` | — | Deterministic, stdlib-only generator (seed = 42). Re-run it to regenerate the CSVs byte-for-byte. |
| `README.md` | — | This explanation. |

The XGBoost file's 2,550 `normal` rows and the Isolation Forest file's 2,000 normal rows
are drawn from the **same** normal-usage distribution, so the two models see consistent
"what normal looks like" data.

---

## 2. Feature Schema (shared by both files)

Every row has the same 9 features — these are the exact features documented in
[`ml-complete-guide.md` § Feature Set](../ml-complete-guide.md) and extracted by
`rpi/ml_inference.py`:

| # | Column | Type | Realistic Range | What it means | How the ESP32/RPi computes it |
|---|--------|------|-----------------|---------------|-------------------------------|
| 1 | `flow_rate` | float (L/min) | 0–40 | Instantaneous flow at this fixture | `(pulses × 60) / (PPL × interval_s)` |
| 2 | `duration_seconds` | int | 5–3600+ | Seconds water has been flowing continuously | Accumulated on the ESP32 |
| 3 | `hour_of_day` | int | 0–23 | Hour of the reading (derived from `timestamp`) | From NTP / RPi clock |
| 4 | `day_of_week` | int | 0–6 (Mon=0) | Day of the reading | From timestamp |
| 5 | `fixture_id` | int | 0–3 | 0=inlet, 1=bidet, 2=kitchen, 3=shower | GPIO→sensor mapping |
| 6 | `inlet_ratio` | float | ~0.8–4.0 | Inlet rate ÷ fixture rate. ~1.0 = balanced | `inlet_rate / fixture_rate` |
| 7 | `rate_variance` | float | 0–10 | Variance of the last 10 flow readings | Rolling buffer on RPi |
| 8 | `is_night_time` | bool | 0/1 | 1 when hour ≥ 22 or hour < 5 | From hour |
| 9 | `pulse_trend` | float | −∞ to +∞ | Slope of the last 5 pulse counts | Linear fit over rolling buffer |

> **Why timestamps are included:** `timestamp` is the first column in both files but is
> **not a model feature** — it exists so you can (a) see the data as a realistic
> 30-day time series (July 1–30, 2026, Asia/Manila `+08:00`), and (b) do a proper
> **temporal split** (train on early days, validate on later days) as the ML guide
> insists — never a random shuffle for time-series data.
>
> `hour_of_day`, `day_of_week`, and `is_night_time` are **derived from the timestamp**
> when the data is generated, so they are always internally consistent with the date.

---

## 3. Why the Data Looks the Way It Does

### 3.1 Class balance: 85% normal / 10% minor / 5% major

Real homes are almost always fine — leaks are rare events. The 85/10/5 split matches
the guide's `generate_synthetic_data.py`. This imbalance is **deliberate and
instructive**: it's why the guide trains XGBoost with **class weights** and why
precision/recall per class (not raw accuracy) are the evaluation metrics. A model that
predicts "normal" for everything would score 85% accuracy while missing every leak.

### 3.2 Normal usage (`label = 0` / `known_anomaly = 0`)

Normal water use is **conditioned on the fixture and the time of day**:

| Fixture | Flow (L/min) | Duration | Why |
|---------|--------------|----------|-----|
| 0 — inlet | ~N(6.0, 2.5), clip 0.3–15 | 30 s – ~4 min | Aggregate of everything; most variable |
| 1 — bidet | ~N(2.5, 0.8), clip 0.8–5 | 8 s – ~1.5 min | Short, low-flow bursts |
| 2 — kitchen | ~N(6.0, 1.5), clip 2–10 | 20 s – ~3 min | Medium bursts |
| 3 — shower | ~N(9.0, 2.0), clip 4–14 | 1 – ~9 min | Long, high-flow sessions |

- **Time of day:** normal usage clusters in the morning (6–9) and evening (17–21)
  rush hours; night readings (22–5) are rare (~5% of rows) and **scaled to 30% flow**
  — people rarely use much water at 3 a.m.
- **`inlet_ratio` 1.00–1.15:** the inlet sensor reads slightly more than any single
  fixture (the other fixtures' usage adds up). A ratio far above this is suspicious.
- **`rate_variance` is high** (5–35% of flow): real usage surges and settles.
- **`pulse_trend` wanders** (σ ≈ 1.2): usage starts and stops.

### 3.3 Minor leak (`label = 1`): drip / slow leak, 0.1–0.5 L/min

- **Flow is fixed in a tight band 0.1–0.5 L/min** — the documented drip range.
- **Duration is long** (10 min to 1 h+, exponential with mean 30 min): a drip doesn't stop.
- **Hours are uniform (0–23):** leaks run 24/7 — they don't care about rush hour.
  This is a key differentiator vs. normal usage, and it's why `is_night_time` and
  `hour_of_day` are useful features.
- **`rate_variance` is tiny** (0.5–5% of flow): a trickle is steady.
- **`pulse_trend` ≈ 0:** flat, sustained pulses.
- `inlet_ratio` 1.00–1.30: a slight imbalance may be present (part of the leak flow is
  "invisible" at the fixture if the leak is on the supply side).

### 3.4 Major leak (`label = 2`): burst / stuck valve, 8–25 L/min

- **Flow 8–25 L/min** — far above any normal single-fixture use.
- **Duration** minutes to hours (exponential, mean 10 min + 2 min minimum).
- **Hours uniform** — a burst at 2 a.m. is still a burst.
- **Steady variance and flat trend**, same rationale as the minor leak.

### 3.5 The injected anomalies in the Isolation Forest file

Isolation Forest needs **no labels to train**, but you can't tell if it works without
some known-bad rows. The last 40 rows are injected anomalies — 10 of each type — that
deviate from normal in ≥ 1 dimension:

| Type | Signature | Why it's anomalous |
|------|-----------|--------------------|
| **Night burst** | 15–30 L/min at 1–4 a.m. | High flow at an hour where normal flow is near zero |
| **Hidden leak** | `fixture_id=0`, `inlet_ratio` 2.0–4.0 | Inlet flows but fixtures read almost nothing |
| **Ultra-slow drip** | 0.02–0.08 L/min for 12+ h at night | Below the physical minimum any tap produces |
| **Sensor spike** | 30–45 L/min for seconds | Beyond YF-S201's rated range (~30 L/min) — glitch/fault |

---

## 4. What Each Dataset Is Used For

### 4.1 XGBoost (`xgboost_sample_dataset.csv`) — supervised classification

Train a 3-class classifier: `normal (0)` / `minor_leak (1)` / `major_leak (2)`.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

df = pd.read_csv("xgboost_sample_dataset.csv", parse_dates=["timestamp"])
df = df.sort_values("timestamp")                 # temporal order!

features = ["flow_rate","duration_seconds","hour_of_day","day_of_week",
            "fixture_id","inlet_ratio","rate_variance","is_night_time","pulse_trend"]
X, y = df[features], df["label"]

# TEMPORAL split (never random-shuffle time series)
cut = int(len(df) * 0.8)
X_train, X_val = X.iloc[:cut], X.iloc[cut:]
y_train, y_val = y.iloc[:cut], y.iloc[cut:]

scaler = StandardScaler().fit(X_train)
X_train_s, X_val_s = scaler.transform(X_train), scaler.transform(X_val)

model = xgb.XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.1,
    scale_pos_weight=None,           # use class_weight='balanced' logic instead
    eval_metric="mlogloss", use_label_encoder=False)
model.fit(X_train_s, y_train,
          sample_weight=compute_class_weights(y_train))   # 85/10/5 imbalance!

model.save_model("xgboost_model.json")   # -> copy to rpi/models/
import joblib; joblib.dump(scaler, "scaler.pkl")
```

### 4.2 Isolation Forest (`isolation_forest_sample_dataset.csv`) — unsupervised anomaly detection

Trained on **normal data only** (the guide's rule). The `known_anomaly` column is used
**only to score the result afterwards** — it is never passed to the model.

```python
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

df = pd.read_csv("isolation_forest_sample_dataset.csv", parse_dates=["timestamp"])
features = ["flow_rate","duration_seconds","hour_of_day","day_of_week",
            "fixture_id","inlet_ratio","rate_variance","is_night_time","pulse_trend"]

# Train on the normal rows ONLY (contamination=0 because input is clean)
train = df[df["known_anomaly"] == 0]
iso = IsolationForest(n_estimators=200, contamination=0.01,
                      random_state=42, n_jobs=-1)
iso.fit(train[features])
joblib.dump(iso, "isolation_forest.pkl")

# Score EVERYTHING, then check whether the injected anomalies stand out
df["score"] = iso.score_samples(df[features])
df["pred"] = iso.predict(df[features])        # 1 = normal, -1 = anomaly

# Pick a threshold from the validation normal data (e.g. 99th percentile of
# score_samples on a normal-only holdout), NOT from the anomalies.
thr = df[df["known_anomaly"] == 0]["score"].quantile(0.01)
print("anomaly recall:",
      (df[(df["known_anomaly"] == 1) & (df["score"] < thr)].shape[0] / 40))
```

### 4.3 How the two models cooperate (from `docs/flowchart.md` §5)

1. RPi receives a reading, extracts the 9 features.
2. **XGBoost** predicts a class; if confidence is high enough → alert or normal.
3. If XGBoost is **uncertain** (low confidence), **Isolation Forest** decides:
   is this reading anomalous? This catches *unknown* failure modes XGBoost was never
   trained on — exactly the job of an unsupervised model.

---

## 5. Relationship to Real Data & the Production Pipeline

These files are a **bootstrap** so you can develop the pipeline immediately. Per the
ML guide:

- **Real data replaces this sample.** Run the ESP32 + RPi for 2+ weeks, simulate leaks
  weekly (see "Leak Simulation Protocol" in the guide), and export readings from SQLite
  (`rpi/data_logger.py`). The `timestamp` column makes merging/validation straightforward.
- **Retrain daily** on the RPi (cron/systemd) as real data accumulates — the guide's
  "Monitoring & Retraining" section.
- **Deployment:** `xgboost_model.json`, `isolation_forest.pkl`, `scaler.pkl`, plus
  `iso_threshold.pkl` and `feature_cols.pkl` → `rpi/models/`. The model **must** see
  features in the exact order shown in §2.

---

## 6. Caveats & Known Inconsistencies in the Docs

- **Synthetic ≠ real.** Real turbulence, air pockets, water pressure variation, and
  sensor aging will shift the distributions. Treat this sample as a starting point,
  not ground truth.
- **Sample size:** 3,000 / 2,040 rows vs. the guide's ≥ 50,000 target. Enough to
  prototype and verify the pipeline; not enough for production-grade accuracy.
- **Feature naming drift in the docs:** the ML guide's generator script uses
  `duration` / `is_night`, while the canonical feature table and `ml_inference.py`
  use `duration_seconds` / `is_night_time`. These CSVs follow the **canonical names**
  used by the deployed code. When training, make sure `feature_cols.pkl` matches
  the order here.
- **`fixture_id`:** these CSVs use 0–3 (0=inlet, 1=bidet, 2=kitchen, 3=shower), matching
  the feature table. The guide's generator sketch uses 1–4 with a "toilet" fixture —
  this project has no toilet, so stick to 0–3.

---

## 7. Regenerating the Data

```bash
cd docs/dataset
python generate_sample_data.py
```

The script is seeded (`random.seed(42)`) and uses only the Python standard library,
so the output CSVs are deterministic across machines and Python versions.
