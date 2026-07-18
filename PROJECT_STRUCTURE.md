# Project Structure

Complete annotated file tree for the Capital Raise Intelligence Platform.

```
capital-raise-intelligence-platform/
├── BLUEPRINT.md                  # Architecture, data model & API reference
├── PROJECT_STRUCTURE.md          # This file
├── README.md                     # Quick-start and overview
├── backend/
│   ├── requirements.txt           # Python dependencies
│   ├── alembic.ini                # Alembic migration config (planned)
│   ├── alembic/                   # Migration versions (planned)
│   └── app/
│       ├── main.py                # FastAPI application entry-point
│       ├── db.py                  # SQLAlchemy engine + session factory
│       ├── models.py              # Core ORM table definitions
│       ├── models_derived.py      # Derived / materialised table definitions
│       ├── schemas.py             # Pydantic request / response schemas
│       ├── analytics/
│       │   ├── __init__.py        # Public analytics API surface
│       │   ├── event_grouping.py  # Cluster raise events by type & time
│       │   ├── dilution_scoring.py# Composite 0-10 dilution risk score
│       │   └── event_study.py     # Market-model CAR / abnormal-return engine
│       ├── ingestion/
│       │   ├── __init__.py        # Ingestion package init
│       │   └── sec_edgar.py       # SEC EDGAR EFTS + filing downloader
│       └── routers/
│           ├── __init__.py        # Router registration helper
│           ├── dashboard.py       # GET /api/dashboard  – summary metrics
│           ├── companies.py       # GET /api/companies  – company registry
│           ├── atm.py             # GET /api/atm         – ATM programmes
│           ├── convertibles.py    # GET /api/convertibles– convertible notes
│           ├── placements.py      # GET /api/placements  – equity placements
│           ├── filings.py         # GET /api/filings     – SEC filings
│           ├── watchlists.py      # CRUD /api/watchlists – user watchlists
│           ├── raise_events.py    # GET /api/raise-events– canonical events
│           └── meta.py            # GET /api/meta        – ref data
├── frontend/                      # React 18 + TypeScript (planned)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/               # Axios client + React Query hooks
│       ├── components/        # Shared UI components
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Screener.tsx
│       │   ├── CompanyDetail.tsx
│       │   └── Watchlists.tsx
│       └── store/             # Zustand global state (planned)
└── db/
    └── schema.sql             # Raw DDL (reference; Alembic is canonical)
```

---

## Key Design Decisions

### Core vs Derived Models

`models.py` contains tables populated directly by the ingestion layer:
- `companies`, `atm_programs`, `convertible_notes`, `equity_placements`
- `shelf_registrations`, `sec_filings`, `raise_events`, `price_history`
- `watchlists`, `watchlist_companies`

`models_derived.py` contains tables populated by analytics jobs:
- `dilution_scores` — refreshed after each ingestion run
- `event_study_results` — computed on demand or scheduled
- `event_groups` — re-clustered when new raise events arrive
- `dashboard_snapshots` — pre-aggregated for fast dashboard loads

### Router Organisation

Each router is a thin FastAPI `APIRouter` that:
1. Accepts query parameters for filtering / pagination.
2. Queries the database via SQLAlchemy session dependency.
3. Returns Pydantic-validated response models from `schemas.py`.
4. Calls analytics functions when scores or study results are requested.

### Analytics Layer

All analytics modules are **pure Python** with no FastAPI or SQLAlchemy imports—
they operate on plain dataclasses / dicts and are independently testable.
Routers hydrate inputs from the DB and persist outputs back after calling the
analytics functions.

### Ingestion Layer

`sec_edgar.py` uses the public EDGAR full-text search API (EFTS) with no API
key required. Rate limiting is handled with exponential back-off. Each run:
1. Searches for new 8-K, S-3, 424B3, and SC 13G filings since last run.
2. Downloads filing index + documents.
3. Normalises into `sec_filings` rows.
4. Derives `raise_events` from filing metadata.
5. Triggers dilution score refresh for affected companies.

---

## Module Dependency Graph

```
main.py
  └── routers/*
        ├── db.py  (session)
        ├── models.py / models_derived.py
        ├── schemas.py
        └── analytics/*
              ├── event_grouping.py
              ├── dilution_scoring.py
              └── event_study.py

ingestion/sec_edgar.py
  ├── db.py
  ├── models.py
  └── analytics/dilution_scoring.py
```
