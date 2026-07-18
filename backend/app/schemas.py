from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date


# ── Issuer ────────────────────────────────────────────────────────────────────

class IssuerBase(BaseModel):
    ticker: str
    company_name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    sic_code: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    is_active: bool = True


class IssuerCreate(IssuerBase):
    cik: str


class IssuerRead(IssuerBase):
    model_config = ConfigDict(from_attributes=True)
    issuer_id: int
    cik: str
    created_at: datetime
    updated_at: datetime


class IssuerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    issuer_id: int
    ticker: str
    company_name: str
    sector: Optional[str] = None
    market_cap: Optional[float] = None


# ── Raise Event ───────────────────────────────────────────────────────────────

class RaiseEventBase(BaseModel):
    raise_type: str
    status: str
    announced_date: Optional[date] = None
    priced_date: Optional[date] = None
    closed_date: Optional[date] = None
    gross_proceeds: Optional[float] = None
    net_proceeds: Optional[float] = None
    shares_offered: Optional[int] = None
    offer_price: Optional[float] = None
    discount_to_market: Optional[float] = None
    has_warrants: bool = False
    warrant_coverage: Optional[float] = None
    is_variable_price: bool = False
    structure_class: Optional[str] = None
    agent_name: Optional[str] = None
    sec_filing_url: Optional[str] = None
    notes: Optional[str] = None


class RaiseEventCreate(RaiseEventBase):
    issuer_id: int


class RaiseEventRead(RaiseEventBase):
    model_config = ConfigDict(from_attributes=True)
    raise_event_id: int
    issuer_id: int
    created_at: datetime


class RaiseEventSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    raise_event_id: int
    ticker: str
    company_name: str
    raise_type: str
    gross_proceeds: Optional[float] = None
    announced_date: Optional[date] = None
    discount_to_market: Optional[float] = None


# ── ATM Program ───────────────────────────────────────────────────────────────

class AtmProgramBase(BaseModel):
    program_size: Optional[float] = None
    amount_sold: Optional[float] = None
    amount_remaining: Optional[float] = None
    shares_sold: Optional[int] = None
    avg_sale_price: Optional[float] = None
    status: Optional[str] = None
    agent_name: Optional[str] = None
    inception_date: Optional[date] = None
    termination_date: Optional[date] = None


class AtmProgramCreate(AtmProgramBase):
    issuer_id: int


class AtmProgramRead(AtmProgramBase):
    model_config = ConfigDict(from_attributes=True)
    atm_program_id: int
    issuer_id: int
    created_at: datetime


# ── Convertible Instrument ────────────────────────────────────────────────────

class ConvertibleInstrumentBase(BaseModel):
    instrument_type: Optional[str] = None
    principal_amount: Optional[float] = None
    coupon_rate: Optional[float] = None
    maturity_date: Optional[date] = None
    conversion_price: Optional[float] = None
    conversion_premium: Optional[float] = None
    is_callable: bool = False
    is_puttable: bool = False
    status: Optional[str] = None


class ConvertibleInstrumentCreate(ConvertibleInstrumentBase):
    issuer_id: int


class ConvertibleInstrumentRead(ConvertibleInstrumentBase):
    model_config = ConfigDict(from_attributes=True)
    instrument_id: int
    issuer_id: int
    created_at: datetime


# ── Private Placement ─────────────────────────────────────────────────────────

class PrivatePlacementBase(BaseModel):
    placement_type: Optional[str] = None
    gross_proceeds: Optional[float] = None
    shares_issued: Optional[int] = None
    price_per_share: Optional[float] = None
    discount_to_market: Optional[float] = None
    has_warrants: bool = False
    warrant_shares: Optional[int] = None
    warrant_exercise_price: Optional[float] = None
    closing_date: Optional[date] = None
    lead_investor: Optional[str] = None


class PrivatePlacementCreate(PrivatePlacementBase):
    issuer_id: int


class PrivatePlacementRead(PrivatePlacementBase):
    model_config = ConfigDict(from_attributes=True)
    placement_id: int
    issuer_id: int
    created_at: datetime


# ── Filing ────────────────────────────────────────────────────────────────────

class FilingBase(BaseModel):
    form_type: str
    filing_date: date
    period_of_report: Optional[date] = None
    accession_number: Optional[str] = None
    sec_url: Optional[str] = None
    description: Optional[str] = None


class FilingCreate(FilingBase):
    issuer_id: int


class FilingRead(FilingBase):
    model_config = ConfigDict(from_attributes=True)
    filing_id: int
    issuer_id: int
    created_at: datetime


class RecentFilingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    filing_id: int
    ticker: str
    form_type: str
    filing_date: date
    description: Optional[str] = None


# ── Dashboard / Analytics ─────────────────────────────────────────────────────

class SectorActivity(BaseModel):
    sector: str
    deal_count: int
    total_proceeds: float
    avg_discount: Optional[float] = None


class DashboardStats(BaseModel):
    total_deals_30d: int
    total_proceeds_30d: float
    avg_discount_30d: Optional[float] = None
    active_atm_programs: int
    largest_gross_proceeds: List[RaiseEventSummary]
    highest_risk_issuers: List[IssuerSummary]
    sectors_most_active: List[SectorActivity]
    recent_filings: List[RecentFilingItem]


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistCreate(BaseModel):
    name: str
    user_id: str


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    watchlist_id: int
    user_id: str
    name: str
    created_at: datetime
    issuer_count: int = 0


# ── Screener ──────────────────────────────────────────────────────────────────

class RaiseEventScreenerParams(BaseModel):
    raise_type: Optional[str] = None
    status: Optional[str] = None
    sector: Optional[str] = None
    min_proceeds: Optional[float] = None
    max_proceeds: Optional[float] = None
    min_discount: Optional[float] = None
    max_discount: Optional[float] = None
    announced_after: Optional[date] = None
    announced_before: Optional[date] = None
    min_risk_score: Optional[float] = None
    ticker: Optional[str] = None
    has_warrants: Optional[bool] = None
    structure_class: Optional[str] = None
    is_variable_price: Optional[bool] = None
    page: int = 1
    page_size: int = 50


class PaginatedRaiseEvents(BaseModel):
    items: List[RaiseEventRead]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Dilution / Risk ───────────────────────────────────────────────────────────

class DilutionMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    metric_id: int
    issuer_id: int
    as_of_date: date
    shares_outstanding: Optional[int] = None
    shares_float: Optional[int] = None
    diluted_shares: Optional[int] = None
    dilution_pct_12m: Optional[float] = None
    atm_overhang_pct: Optional[float] = None
    warrant_overhang_pct: Optional[float] = None
    convertible_overhang_pct: Optional[float] = None
    total_overhang_pct: Optional[float] = None


class CompanyRiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score_id: int
    issuer_id: int
    as_of_date: date
    composite_risk_score: Optional[float] = None
    dilution_risk_score: Optional[float] = None
    deal_frequency_score: Optional[float] = None
    discount_aggressiveness_score: Optional[float] = None
    warrant_usage_score: Optional[float] = None
    atm_utilization_score: Optional[float] = None
    risk_tier: Optional[str] = None


# ── Event Study ───────────────────────────────────────────────────────────────

class EventStudyResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    result_id: int
    raise_event_id: int
    window_days_pre: int
    window_days_post: int
    car_pre: Optional[float] = None
    car_post: Optional[float] = None
    abnormal_return_day0: Optional[float] = None
    abnormal_return_day1: Optional[float] = None
    abnormal_return_day5: Optional[float] = None
    abnormal_return_day10: Optional[float] = None
    abnormal_return_day20: Optional[float] = None
    benchmark: Optional[str] = None
    computed_at: Optional[datetime] = None
