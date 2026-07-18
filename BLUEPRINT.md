# Capital Raise Intelligence Platform — Blueprint

## Vision

A production-ready analytics platform that ingests, normalises, and analyses
public-company capital-raise events (ATM programmes, convertible notes, equity
placements, and shelf/S-3 filings) sourced primarily from SEC EDGAR. The
platform surfaces dilution risk scores, event-study abnormal returns, and
screener dashboards through a FastAPI backend consumed by a React frontend.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│  Dashboard · Screener · Company Detail · Watchlists      │
└───────────────────────┬──────────────────────────────────┘
                        │ REST / JSON
┌───────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│  Routers: dashboard · companies · atm · convertibles     │
│           placements · filings · watchlists              │
│           raise_events · meta                            │
│  Analytics: event_grouping · dilution_scoring            │
│             event_study                                  │
└───────────────────────┬──────────────────────────────────┘
                        │ SQLAlchemy ORM
┌───────────────────────▼──────────────────────────────────┐
│              PostgreSQL Database                         │
│  Core tables + Derived / materialised tables             │
└──────────────────────────────────────────────────────────┘
                        ▲
          ┌─────────────┘
┌─────────┴──────────────────┐
│   Ingestion Layer          │
│   SEC EDGAR (EFTS + XBRL)  │
└────────────────────────────┘
```

---

## Data Model

### Core Tables (SQLAlchemy — `models.py`)

| Table | Description |
|---|---|
| `companies` | Master company register (ticker, CIK, sector, exchange) |
| `atm_programs` | At-the-market offering programmes |
| `convertible_notes` | Convertible note / bond issuances |
| `equity_placements` | Registered direct & PIPE transactions |
| `shelf_registrations` | S-3 / shelf registration statements |
| `sec_filings` | Raw SEC filing metadata (8-K, S-3, 424B, etc.) |
| `raise_events` | Normalised canonical raise event record |
| `price_history` | Daily OHLCV + benchmark returns |
| `watchlists` | User-defined company watchlists |
| `watchlist_companies` | Many-to-many join |

### Derived Tables (SQLAlchemy — `models_derived.py`)

| Table | Description |
|---|---|
| `dilution_scores` | Composite dilution-risk scores per company |
| `event_study_results` | Abnormal returns and CARs per raise event |
| `event_groups` | Clustered / grouped raise events |
| `dashboard_snapshots` | Pre-aggregated dashboard metrics |

---

## Analytics Modules

### `event_grouping.py`
- Clusters raise events by proximity in time and deal type.
- Outputs `EventGroup` objects with member event IDs and group-level metrics.
- Configurable gap threshold (default 90 days) and minimum group size.

### `dilution_scoring.py`
- Computes a 0–10 composite dilution risk score per company.
- Sub-scores: dilution risk · deal frequency · discount aggressiveness ·
  warrant usage · ATM utilisation.
- Configurable weights (`_WEIGHTS`) and normalisation caps.
- Outputs risk tier: `low` / `medium` / `high` / `critical`.

### `event_study.py`
- Market-model event study using OLS estimation window.
- Computes day-relative abnormal returns and cumulative abnormal returns (CARs).
- Summary windows: CAR(-5,+1), CAR(0,+5), CAR(0,+20).
- Batch helper `run_batch_event_study()` for portfolio-level analysis.

---

## API Endpoints

| Router | Prefix | Key Endpoints |
|---|---|---|
| dashboard | `/api/dashboard` | summary metrics, recent events |
| companies | `/api/companies` | list, detail, search |
| atm | `/api/atm` | ATM programme list and detail |
| convertibles | `/api/convertibles` | convertible note list and detail |
| placements | `/api/placements` | equity placement list and detail |
| filings | `/api/filings` | SEC filing list and detail |
| watchlists | `/api/watchlists` | CRUD watchlists |
| raise_events | `/api/raise-events` | canonical event list, screener |
| meta | `/api/meta` | sectors, exchanges, deal types |

---

## Ingestion Pipeline

### `ingestion/sec_edgar.py`
- Fetches full-text search results from EDGAR EFTS API.
- Downloads and parses 8-K, S-3, 424B3 filings.
- Normalises into `sec_filings` and `raise_events` tables.
- Scheduled via cron / APScheduler (configurable cadence).

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.110+ |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 15+ |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Frontend framework | React 18 + TypeScript |
| Charting | Recharts / Plotly |
| Data fetching | React Query (TanStack) |
| HTTP client | Axios |
| Styling | Tailwind CSS |
| Testing (backend) | pytest + httpx |
| Testing (frontend) | Vitest + Testing Library |
| Containerisation | Docker + docker-compose |

---

## Development Setup

```bash
# Clone
git clone https://github.com/grisheet/capital-raise-intelligence-platform.git
cd capital-raise-intelligence-platform

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## Roadmap

- [ ] SEC EDGAR ingestion scheduler (APScheduler)
- [ ] Alembic migration scripts
- [ ] React frontend scaffolding
- [ ] Authentication (JWT / OAuth2)
- [ ] Alerting engine (price + dilution thresholds)
- [ ] Export to CSV / Excel
- [ ] WebSocket live updates
- [ ] Deployment (Railway / Render / AWS)
