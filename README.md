# FAILSAFE — Early-Warning System for Student Failure

> Predict, explain, and act *before* the semester slips away.
>
> Implementation of the **FAILSAFE** project from the IIT Guwahati Coding
> Club Even-Semester project booklet (page 9 of `EvenSemProjects.pdf`).

FAILSAFE is a full-stack platform that lets faculty and HODs upload
student data, get explainable risk predictions, and auto-generate
personalised intervention plans — all powered by an XGBoost model
trained on the UCI Student Performance dataset and made transparent
via SHAP.

---

## What's inside

```
EVENSEM/
├── ml/                  # Phase 1 — Data, modelling, SHAP
│   ├── src/
│   │   ├── config.py        # Feature lists, paths, thresholds
│   │   ├── data.py          # UCI download / synthetic fallback
│   │   ├── preprocess.py    # OneHot + StandardScaler ColumnTransformer
│   │   ├── train.py         # Trains and persists XGBoost + preprocessor
│   │   ├── eda.py           # Matplotlib/Seaborn EDA → ml/reports/*.png
│   │   ├── explain.py       # SHAP TreeExplainer wrapper
│   │   └── interventions.py # Rule-based intervention generator
│   ├── notebooks/eda.ipynb
│   └── requirements.txt
├── backend/             # Phase 2 — FastAPI + JWT + DB
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py        # pydantic-settings (.env driven)
│   │   ├── database.py      # SQLAlchemy 2.0 (Postgres / SQLite)
│   │   ├── models.py        # users, prediction_batches, student_predictions
│   │   ├── schemas.py
│   │   ├── security.py      # bcrypt + jose JWT
│   │   ├── deps.py
│   │   ├── inference.py     # Loads ML artefacts, exposes engine
│   │   └── routers/
│   │       ├── auth.py
│   │       └── predictions.py
│   ├── .env.example
│   └── requirements.txt
└── frontend/            # Phase 3 — React + Vite + TS
    ├── src/
    │   ├── api/             # axios client + types
    │   ├── auth/            # AuthContext + ProtectedRoute
    │   ├── components/      # AppShell, ShapBars, RiskBadge, …
    │   ├── pages/           # Login, Dashboard, Upload, Batches, BatchDetail
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

---

## Phase 1 — ML Core

The pipeline trains on the **UCI Student Performance** Math dataset
(395 students, 32 features). The target is `at_risk = G3 < 10`. We
deliberately *exclude* `G1`, `G2`, `G3` from the feature matrix so
predictions are based purely on attendance + behavioural + contextual
signals — exactly what the FAILSAFE problem statement requires.

### One-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ml/requirements.txt
# macOS only — required for XGBoost:
brew install libomp
```

### Run EDA

```bash
cd ml
python -m src.eda
# Figures land in ml/reports/0[1-5]_*.png
```

You can also open `ml/notebooks/eda.ipynb` (install jupyter separately
with `pip install jupyter`).

### Train the model

```bash
cd ml
python -m src.train
```

Outputs (under `ml/models/`):

| Artefact | Purpose |
|---|---|
| `xgb_failsafe.json` | Serialised XGBoost classifier |
| `preprocessor.joblib` | OneHotEncoder + StandardScaler ColumnTransformer |
| `shap_background.npy` | Background sample for the SHAP TreeExplainer |
| `metadata.json` | Metrics + feature schema for the backend to consume |

Sample run on the real UCI data:

```
roc_auc = 0.71  | f1 = 0.53  | accuracy = 0.68
```

### Quick demo of the explainer

```python
from ml.src.explain import FailsafeExplainer  # via inference engine
# or use the FastAPI /api/predict endpoint described below.
```

---

## Phase 2 — Backend API

FastAPI + SQLAlchemy 2.0 + JWT (HS256). Works against PostgreSQL in
production and falls back to a local SQLite file for development.

### Setup

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env       # edit DATABASE_URL etc.
```

### Run

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

- Swagger UI: <http://127.0.0.1:8765/docs>
- Health check: <http://127.0.0.1:8765/api/health>

### Switching to PostgreSQL

```env
DATABASE_URL=postgresql+psycopg2://failsafe:failsafe@localhost:5432/failsafe
```

Tables auto-create on startup via `Base.metadata.create_all`.

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | – | Create faculty/HOD account, returns JWT |
| `POST` | `/api/auth/login` | – | JSON login, returns JWT |
| `POST` | `/api/auth/token` | – | OAuth2 password flow (Swagger) |
| `GET`  | `/api/auth/me` | JWT | Current user profile |
| `POST` | `/api/predict` | JWT | Score a JSON list of student records |
| `POST` | `/api/predict/csv` | JWT | Bulk CSV upload (multipart) |
| `GET`  | `/api/batches` | JWT | List historical batches |
| `GET`  | `/api/batches/{id}` | JWT | Full batch with per-student SHAP & interventions |
| `GET`  | `/api/dashboard` | JWT | Aggregate stats + top SHAP drivers + recent batches |
| `GET`  | `/api/health` | – | Liveness + model-loaded flag |

Faculty users only see their own batches; HOD users see everything.

### Inference response (truncated)

```json
{
  "student_ref": "S001",
  "risk_score": 0.83,
  "at_risk": true,
  "risk_band": "high",
  "base_value": 0.34,
  "contributions": [
    {"feature": "failures",  "value": 1.0, "shap": 0.169},
    {"feature": "absences",  "value": 8.0, "shap": -0.124},
    {"feature": "goout",     "value": 4.0, "shap": 0.105}
  ],
  "interventions": [
    {
      "title": "Remedial coursework",
      "category": "academic",
      "detail": "1 prior subject failure. Pair with a peer mentor and assign 2x weekly remedial sessions...",
      "driver": "failures",
      "impact": 0.169
    }
  ]
}
```

---

## Phase 3 — Frontend Dashboard

React 18 + Vite + TypeScript + Recharts. No CSS framework — a
hand-tuned dark theme keeps the bundle small.

### Setup & run

```bash
cd frontend
npm install
npm run dev
```

The app starts at <http://localhost:5173>. The Vite dev server proxies
`/api/*` to `http://localhost:8765` by default; override with
`VITE_API_PROXY=http://my-backend:9000 npm run dev`.

### Production build

```bash
npm run build
npm run preview
```

### Pages

| Route | Description |
|---|---|
| `/login` | Login + register tabs (faculty / HOD) |
| `/dashboard` | Risk-band donut, risk-trend line, top SHAP drivers, recent batches |
| `/upload` | Drag-and-drop CSV portal + downloadable template |
| `/batches` | All batches the user can access |
| `/batches/:id` | Per-student drill-down: SHAP bar plot + interventions |

### CSV format

The CSV must contain the canonical UCI Student Performance columns
*minus* the grade fields (`G1`/`G2`/`G3` are stripped if present so the
prediction stays "early"). A `student_ref` column is auto-generated if
missing. The upload page has a one-click **Download template** button.

---

## End-to-end run

```bash
# 1. Train (once)
source .venv/bin/activate
cd ml && python -m src.train && cd ..

# 2. Backend
cd backend && uvicorn app.main:app --reload --port 8765 &
cd ..

# 3. Frontend
cd frontend && npm install && npm run dev
```

Then:

1. Open <http://localhost:5173>, click **Create account**, pick
   role = HOD.
2. Hit **Upload CSV** and either drop a real student CSV or click
   **Download template** to grab a sample row.
3. Watch the dashboard populate with risk bands, the trend line, and
   the top SHAP drivers.
4. Open the resulting batch — pick any student to see the colour-coded
   SHAP attributions and the auto-generated intervention plan.

---

## Tech stack summary

| Layer | Tools |
|---|---|
| **ML** | Python, pandas, scikit-learn, XGBoost, SHAP, matplotlib, seaborn |
| **API** | FastAPI, SQLAlchemy 2.0, pydantic v2, python-jose (JWT), bcrypt |
| **Storage** | PostgreSQL (prod) / SQLite (dev) |
| **Frontend** | React 18, Vite, TypeScript, axios, Recharts |

## Notes & trade-offs

- The interventions are deliberately rule-based (not LLM-generated) so
  every recommendation is auditable and ties back to a specific SHAP
  attribution.
- The model uses `scale_pos_weight` for class imbalance — the UCI
  dataset has ~33% at-risk students.
- HOD vs faculty visibility is enforced server-side in the prediction
  routers, not just hidden in the UI.
- For privacy, only model-relevant features and predictions are
  persisted — no free-text PII columns are stored unless you put them
  in the `student_ref` field.
