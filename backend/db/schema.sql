-- =============================================================
-- Capital Raise Intelligence Platform -- PostgreSQL Schema
-- Two-schema design: core (system of record) + derived (analytics)
-- =============================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS derived;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================
-- CORE SCHEMA
-- ==============================================================

CREATE TABLE core.issuers (
    issuer_id         SERIAL PRIMARY KEY,
    uuid              UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    cik               VARCHAR(10) UNIQUE,
    primary_ticker    VARCHAR(10),
    company_name      TEXT NOT NULL,
    sector            TEXT,
    industry          TEXT,
    sic_code          VARCHAR(4),
    exchange          VARCHAR(10),
    market_cap_usd    NUMERIC(20, 2),
    shares_outstanding BIGINT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_issuers_ticker ON core.issuers(primary_ticker);
CREATE INDEX idx_issuers_cik ON core.issuers(cik);

CREATE TABLE core.filings (
    filing_id         SERIAL PRIMARY KEY,
    uuid              UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    issuer_id         INT NOT NULL REFERENCES core.issuers(issuer_id),
    accession_number  VARCHAR(25) NOT NULL UNIQUE,  -- SEC accession number, immutable key
    form_type         VARCHAR(20) NOT NULL,         -- S-3, 424B3, 8-K, etc.
    file_number       VARCHAR(20),                  -- Registration file number for linking
    filed_at          TIMESTAMPTZ NOT NULL,
    period_of_report  DATE,
    primary_doc_url   TEXT,
    full_text_url     TEXT,
    raw_content       TEXT,
    extracted_terms   JSONB,
    grouping_status   VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending|grouped|needs_review
    raise_event_id    INT,
    grouping_confidence NUMERIC(4, 3),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_filings_issuer ON core.filings(issuer_id);
CREATE INDEX idx_filings_form_type ON core.filings(form_type);
CREATE INDEX idx_filings_filed_at ON core.filings(filed_at DESC);
CREATE INDEX idx_filings_file_number ON core.filings(file_number);
CREATE INDEX idx_filings_raise_event ON core.filings(raise_event_id);

CREATE TABLE core.raise_events (
    raise_event_id      SERIAL PRIMARY KEY,
    uuid                UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    issuer_id           INT NOT NULL REFERENCES core.issuers(issuer_id),
    raise_type          VARCHAR(30) NOT NULL,  -- shelf_registration|atm_program|convertible_debt|convertible_preferred|private_placement_pipe|direct_offering|rights_offering|warrant_exercise
    status              VARCHAR(20) NOT NULL DEFAULT 'active',  -- active|launched|priced|closed|withdrawn|expired
    announcement_date   DATE,
    pricing_date        DATE,
    closing_date        DATE,
    gross_proceeds_usd  NUMERIC(20, 2),
    net_proceeds_usd    NUMERIC(20, 2),
    shares_issued       BIGINT,
    offering_price_usd  NUMERIC(10, 4),
    reference_price_usd NUMERIC(10, 4),
    discount_to_reference_pct NUMERIC(6, 3),
    underwriter         TEXT,
    confidence_score    NUMERIC(4, 3) NOT NULL DEFAULT 1.0,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_raise_events_issuer ON core.raise_events(issuer_id);
CREATE INDEX idx_raise_events_type ON core.raise_events(raise_type);
CREATE INDEX idx_raise_events_status ON core.raise_events(status);
CREATE INDEX idx_raise_events_announcement ON core.raise_events(announcement_date DESC);

CREATE TABLE core.raise_event_status_history (
    history_id      SERIAL PRIMARY KEY,
    raise_event_id  INT NOT NULL REFERENCES core.raise_events(raise_event_id),
    old_status      VARCHAR(20),
    new_status      VARCHAR(20) NOT NULL,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by      TEXT
);

CREATE TABLE core.atm_programs (
    atm_program_id              SERIAL PRIMARY KEY,
    raise_event_id              INT NOT NULL REFERENCES core.raise_events(raise_event_id),
    issuer_id                   INT NOT NULL REFERENCES core.issuers(issuer_id),
    total_authorized_usd        NUMERIC(20, 2),
    estimated_utilized_usd      NUMERIC(20, 2),
    estimated_remaining_capacity_usd NUMERIC(20, 2),
    sales_agreement_date        DATE,
    sales_agreement_expiry      DATE,
    agent_broker                TEXT,
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    supplement_count_trailing_90d INT NOT NULL DEFAULT 0,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE core.convertible_instruments (
    convertible_id              SERIAL PRIMARY KEY,
    raise_event_id              INT NOT NULL REFERENCES core.raise_events(raise_event_id),
    issuer_id                   INT NOT NULL REFERENCES core.issuers(issuer_id),
    instrument_class            VARCHAR(20) NOT NULL,  -- note|debenture|preferred_stock|warrant
    principal_amount_usd        NUMERIC(20, 2),
    issue_date                  DATE,
    maturity_date               DATE,
    coupon_rate_pct             NUMERIC(6, 3),
    initial_conversion_price_usd NUMERIC(10, 4),
    is_variable_price           BOOLEAN NOT NULL DEFAULT FALSE,
    conversion_price_floor_usd  NUMERIC(10, 4),
    conversion_premium_pct      NUMERIC(6, 3),
    has_reset_provision         BOOLEAN NOT NULL DEFAULT FALSE,
    reset_lookback_days         INT,
    make_whole_table            JSONB,
    secured_status              VARCHAR(20),  -- unsecured|senior_secured|subordinated
    structure_class             VARCHAR(20),  -- standard|aggressive|toxic
    structure_class_rationale   TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE core.private_placements (
    placement_id            SERIAL PRIMARY KEY,
    raise_event_id          INT NOT NULL REFERENCES core.raise_events(raise_event_id),
    issuer_id               INT NOT NULL REFERENCES core.issuers(issuer_id),
    placement_type          VARCHAR(30) NOT NULL,  -- pipe|registered_direct|confidential_investment
    gross_proceeds_usd      NUMERIC(20, 2),
    price_per_share_usd     NUMERIC(10, 4),
    shares_issued           BIGINT,
    warrants_issued         BIGINT,
    warrant_exercise_price  NUMERIC(10, 4),
    warrant_term_years      NUMERIC(4, 2),
    discount_pct            NUMERIC(6, 3),
    investor_type           VARCHAR(30),  -- institutional|family_office|strategic|hedge_fund
    has_lockup              BOOLEAN NOT NULL DEFAULT FALSE,
    lockup_days             INT,
    registration_rights     BOOLEAN NOT NULL DEFAULT FALSE,
    registration_deadline_days INT,
    closing_date            DATE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE core.price_history (
    price_history_id    SERIAL PRIMARY KEY,
    issuer_id           INT NOT NULL REFERENCES core.issuers(issuer_id),
    trading_date        DATE NOT NULL,
    open_usd            NUMERIC(10, 4),
    high_usd            NUMERIC(10, 4),
    low_usd             NUMERIC(10, 4),
    close_usd           NUMERIC(10, 4) NOT NULL,
    adj_close_usd       NUMERIC(10, 4),
    volume              BIGINT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(issuer_id, trading_date)
);

CREATE INDEX idx_price_history_issuer_date ON core.price_history(issuer_id, trading_date DESC);

CREATE TABLE core.watchlists (
    watchlist_id    SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    name            TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE core.watchlist_items (
    item_id         SERIAL PRIMARY KEY,
    watchlist_id    INT NOT NULL REFERENCES core.watchlists(watchlist_id) ON DELETE CASCADE,
    issuer_id       INT NOT NULL REFERENCES core.issuers(issuer_id),
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(watchlist_id, issuer_id)
);

-- ==============================================================
-- DERIVED SCHEMA (append-only, fully recomputable)
-- ==============================================================

CREATE TABLE derived.dilution_metrics (
    metric_id           SERIAL PRIMARY KEY,
    issuer_id           INT NOT NULL REFERENCES core.issuers(issuer_id),
    as_of_date          DATE NOT NULL,
    shares_outstanding  BIGINT,
    atm_overhang_shares BIGINT,
    shelf_overhang_usd  NUMERIC(20, 2),
    convertible_dilution_shares BIGINT,
    warrant_overhang_shares BIGINT,
    total_potential_dilution_pct NUMERIC(6, 3),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(issuer_id, as_of_date)
);

CREATE TABLE derived.company_risk_scores (
    score_id        SERIAL PRIMARY KEY,
    issuer_id       INT NOT NULL REFERENCES core.issuers(issuer_id),
    as_of_date      DATE NOT NULL,
    risk_score      NUMERIC(5, 2) NOT NULL,  -- 0-100
    severity        VARCHAR(10) NOT NULL,    -- low|medium|high|critical
    factor_breakdown_json JSONB NOT NULL,
    recency_multiplier NUMERIC(4, 3),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(issuer_id, as_of_date)
);

CREATE INDEX idx_risk_scores_issuer_date ON derived.company_risk_scores(issuer_id, as_of_date DESC);
CREATE INDEX idx_risk_scores_score ON derived.company_risk_scores(risk_score DESC);

CREATE TABLE derived.event_study_results (
    result_id           SERIAL PRIMARY KEY,
    raise_event_id      INT NOT NULL REFERENCES core.raise_events(raise_event_id),
    issuer_id           INT NOT NULL REFERENCES core.issuers(issuer_id),
    window_type         VARCHAR(20) NOT NULL,  -- reaction|post_event
    window_days         INT NOT NULL,
    anchor_date         DATE NOT NULL,
    raw_return_pct      NUMERIC(8, 4),
    benchmark_return_pct NUMERIC(8, 4),
    excess_return_pct   NUMERIC(8, 4),
    realized_vol_annualized NUMERIC(8, 4),
    volume_ratio        NUMERIC(8, 4),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(raise_event_id, window_type, window_days)
);

-- Materialized view: latest risk score per issuer
CREATE MATERIALIZED VIEW derived.mv_latest_risk_scores AS
SELECT DISTINCT ON (issuer_id)
    issuer_id,
    risk_score,
    severity,
    factor_breakdown_json,
    as_of_date
FROM derived.company_risk_scores
ORDER BY issuer_id, as_of_date DESC;

CREATE UNIQUE INDEX ON derived.mv_latest_risk_scores(issuer_id);

-- Materialized view: raise event summary with issuer info
CREATE MATERIALIZED VIEW derived.mv_raise_event_summary AS
SELECT
    re.raise_event_id,
    re.uuid,
    re.raise_type,
    re.status,
    re.announcement_date,
    re.pricing_date,
    re.closing_date,
    re.gross_proceeds_usd,
    re.discount_to_reference_pct,
    re.confidence_score,
    i.issuer_id,
    i.primary_ticker,
    i.company_name,
    i.sector,
    i.market_cap_usd,
    rs.risk_score,
    rs.severity
FROM core.raise_events re
JOIN core.issuers i ON i.issuer_id = re.issuer_id
LEFT JOIN derived.mv_latest_risk_scores rs ON rs.issuer_id = re.issuer_id;

CREATE INDEX ON derived.mv_raise_event_summary(announcement_date DESC);
CREATE INDEX ON derived.mv_raise_event_summary(issuer_id);
CREATE INDEX ON derived.mv_raise_event_summary(raise_type);
CREATE INDEX ON derived.mv_raise_event_summary(risk_score DESC NULLS LAST);
