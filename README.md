# Capital Raise Intelligence Platform

A production-grade platform for monitoring public-company secondary offerings, convertible debt, ATM programs, and private placements. Built on the thesis that **dilution risk is emergent** — it lives in the *sequence* of SEC filings, not in any single document.

## Overview

Existing tools (SEC EDGAR full-text search, filing alert services) surface documents, not events. This platform's core differentiation is the **raise event graph**: filings are ingested, entity-resolved to issuers, classified by form/content, and collapsed into `raise_events` that represent the economic transaction, not the paperwork.

On top of that event graph we compute:
- **Dilution-risk scoring** — a deterministic, explainable score per issuer combining active overhang (ATM capacity, shelf capacity, convertible-at-current-price dilution, warrant overhang) with behavioral signals (financing frequency, discount severity, structure toxicity).
- **Event-study analytics** — pre/post price and volume behavior around raise events, aggregated by raise type and by issuer.

**Primary users:** event-driven traders, capital-markets analysts, distressed-credit/equity researchers, short-sellers, IR teams doing competitive monitoring.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | FastAPI + Pydantic v2 + SQLAlchemy 2 (async) |
| Database | PostgreSQL 15 (core + derived schemas) |
| Analytics | Python (pandas, numpy) — scheduled workers |
| Ingestion | Python workers polling SEC EDGAR EFTS |

## Project Structure

```
capital-raise-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── db.py                      # Async engine + session factory
│   │   ├── models.py                  # SQLAlchemy ORM (core schema)
│   │   ├── models_derived.py          # SQLAlchemy ORM (derived schema)
│   │   ├── schemas.py                 # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── dashboard.py           # Overview metrics + chart series
│   │   │   ├── companies.py           # Company detail + financing history
│   │   │   ├── atm.py                 # ATM programs monitor
│   │   │   ├── convertibles.py        # Convertible instruments monitor
│   │   │   ├── placements.py          # Private placements monitor
│   │   │   ├── filings.py             # Raw filings explorer
│   │   │   ├── watchlists.py          # User watchlists
│   │   │   ├── raise_events.py        # Raise events screener
│   │   │   └── meta.py                # Metadata endpoints
│   │   └── analytics/
│   │       ├── event_grouping.py      # 3-layer filing→event grouping
│   │       ├── dilution_scoring.py    # Deterministic weighted scoring
│   │       └── event_study.py         # Pre/post event analytics
│   ├── ingestion/
│   │   ├── edgar_poller.py            # SEC EDGAR EFTS polling
│   │   └── raise_event_repository.py  # Dynamic-filter query builder
│   ├── db/
│   │   └── schema.sql                 # Full PostgreSQL schema
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts              # Typed API client
│   │   ├── components/
│   │   │   └── DataTable.tsx          # Dense sortable data table
│   │   └── pages/
│   │       └── RaiseScreener.tsx      # Main screener page
│   ├── package.json
│   └── tsconfig.json
├── BLUEPRINT.md                       # Architecture diagram + roadmap
├── PROJECT_STRUCTURE.md               # Folder layout + naming conventions
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create the database
psql -U postgres -c "CREATE DATABASE capital_raise;"
psql -U postgres -d capital_raise -f db/schema.sql

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

## Core Design Decisions

### Event Grouping (the hardest part)

`analytics/event_grouping.py` implements a three-layer strategy:
1. **Deterministic linking** — shared S-3/424B registration file numbers
2. **Scored heuristic fallback** — date proximity + term matching with `MIN_HEURISTIC_CONFIDENCE` threshold
3. **`needs_review` outcome** — for ambiguous cases instead of silently guessing

Confidence scores persist on every filing→event link so the UI can surface low-confidence groupings for analyst review.

### Schema Design

`db/schema.sql` splits into:
- **`core` schema** — system of record (issuers, filings, raise_events, convertible_instruments, private_placements, atm_programs, price_history)
- **`derived` schema** — append-only, fully recomputable analytics (dilution_metrics, company_risk_scores, event_study_results, materialized views)

This separation means the derived schema can be fully dropped and recomputed from core without data loss.

### Dilution Scoring

`analytics/dilution_scoring.py` is a deterministic, weighted, capped-and-normalized model:
- 9 named factors summing to 100, plus a bounded recency multiplier
- Returns a full factor breakdown, not just a number — so the UI can explain a score
- Designed to be auditable and tunable without retraining ML models

### Event-Study Analytics

`analytics/event_study.py` anchors:
- **Reaction windows** on announcement date
- **Post-event windows** on closing date

Computing raw/benchmark/excess return, realized volatility, and volume ratio per window.

## Roadmap

### MVP (Weeks 1–8)
- Ingestion for 424B, S-1, S-3, 8-K forms (US issuers only)
- Entity resolution via CIK/Ticker mapping
- Dilution scoring v1 (weighted rule-based, explainable)
- FastAPI endpoints: dashboard, raise events list/detail, companies list/detail, screener
- React: Overview Dashboard, Raise Screener, Company Page, Raise Event Detail

### Phase 2 (Weeks 9–16)
- ATM Monitor, Convertible Monitor, Private Placement Monitor, Shelf Overhang Tracker
- Watchlists + Alerts (email/webhook)
- Benchmark-relative returns, intraday price ingestion
- Historical backfill (2–3 years lookback)
- NLP-assisted term extraction for complex convertibles

## License

MIT
