"""SQLAlchemy ORM models for the derived schema (append-only analytics)."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class DilutionMetrics(Base):
    __tablename__ = "dilution_metrics"
    __table_args__ = (
        UniqueConstraint("issuer_id", "as_of_date"),
        {"schema": "derived"},
    )

    metric_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    shares_outstanding: Mapped[Optional[int]] = mapped_column(Integer)
    atm_overhang_shares: Mapped[Optional[int]] = mapped_column(Integer)
    shelf_overhang_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    convertible_dilution_shares: Mapped[Optional[int]] = mapped_column(Integer)
    warrant_overhang_shares: Mapped[Optional[int]] = mapped_column(Integer)
    total_potential_dilution_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanyRiskScore(Base):
    __tablename__ = "company_risk_scores"
    __table_args__ = (
        UniqueConstraint("issuer_id", "as_of_date"),
        {"schema": "derived"},
    )

    score_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)  # low|medium|high|critical
    factor_breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recency_multiplier: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventStudyResult(Base):
    __tablename__ = "event_study_results"
    __table_args__ = (
        UniqueConstraint("raise_event_id", "window_type", "window_days"),
        {"schema": "derived"},
    )

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raise_event_id: Mapped[int] = mapped_column(ForeignKey("core.raise_events.raise_event_id"), nullable=False)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"), nullable=False)
    window_type: Mapped[str] = mapped_column(String(20), nullable=False)  # reaction|post_event
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    raw_return_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    benchmark_return_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    excess_return_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    realized_vol_annualized: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    volume_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
