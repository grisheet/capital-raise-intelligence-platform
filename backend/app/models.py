"""SQLAlchemy ORM models for the core schema."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
import uuid as _uuid


class Issuer(Base):
    __tablename__ = "issuers"
    __table_args__ = {"schema": "core"}

    issuer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), default=_uuid.uuid4, unique=True)
    cik: Mapped[Optional[str]] = mapped_column(String(10), unique=True)
    primary_ticker: Mapped[Optional[str]] = mapped_column(String(10))
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(Text)
    market_cap_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    shares_outstanding: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    raise_events: Mapped[list["RaiseEvent"]] = relationship(back_populates="issuer")
    filings: Mapped[list["Filing"]] = relationship(back_populates="issuer")


class Filing(Base):
    __tablename__ = "filings"
    __table_args__ = {"schema": "core"}

    filing_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"), nullable=False)
    accession_number: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    form_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_number: Mapped[Optional[str]] = mapped_column(String(20))
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_of_report: Mapped[Optional[date]] = mapped_column(Date)
    primary_doc_url: Mapped[Optional[str]] = mapped_column(Text)
    grouping_status: Mapped[str] = mapped_column(String(20), default="pending")
    raise_event_id: Mapped[Optional[int]] = mapped_column(Integer)
    grouping_confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issuer: Mapped["Issuer"] = relationship(back_populates="filings")


class RaiseEvent(Base):
    __tablename__ = "raise_events"
    __table_args__ = {"schema": "core"}

    raise_event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"), nullable=False)
    raise_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    announcement_date: Mapped[Optional[date]] = mapped_column(Date)
    pricing_date: Mapped[Optional[date]] = mapped_column(Date)
    closing_date: Mapped[Optional[date]] = mapped_column(Date)
    gross_proceeds_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    net_proceeds_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    shares_issued: Mapped[Optional[int]] = mapped_column(BigInteger)
    offering_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reference_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    discount_to_reference_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 3))
    underwriter: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    issuer: Mapped["Issuer"] = relationship(back_populates="raise_events")


class AtmProgram(Base):
    __tablename__ = "atm_programs"
    __table_args__ = {"schema": "core"}

    atm_program_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raise_event_id: Mapped[int] = mapped_column(ForeignKey("core.raise_events.raise_event_id"))
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"))
    total_authorized_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    estimated_utilized_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    estimated_remaining_capacity_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    sales_agreement_date: Mapped[Optional[date]] = mapped_column(Date)
    agent_broker: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    supplement_count_trailing_90d: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConvertibleInstrument(Base):
    __tablename__ = "convertible_instruments"
    __table_args__ = {"schema": "core"}

    convertible_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raise_event_id: Mapped[int] = mapped_column(ForeignKey("core.raise_events.raise_event_id"))
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"))
    instrument_class: Mapped[str] = mapped_column(String(20))
    principal_amount_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    maturity_date: Mapped[Optional[date]] = mapped_column(Date)
    coupon_rate_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 3))
    initial_conversion_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    is_variable_price: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_price_floor_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    has_reset_provision: Mapped[bool] = mapped_column(Boolean, default=False)
    secured_status: Mapped[Optional[str]] = mapped_column(String(20))
    structure_class: Mapped[Optional[str]] = mapped_column(String(20))
    structure_class_rationale: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PrivatePlacement(Base):
    __tablename__ = "private_placements"
    __table_args__ = {"schema": "core"}

    placement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raise_event_id: Mapped[int] = mapped_column(ForeignKey("core.raise_events.raise_event_id"))
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"))
    placement_type: Mapped[str] = mapped_column(String(30))
    gross_proceeds_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    price_per_share_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    shares_issued: Mapped[Optional[int]] = mapped_column(BigInteger)
    warrants_issued: Mapped[Optional[int]] = mapped_column(BigInteger)
    discount_pct: Mapped[Optional[float]] = mapped_column(Numeric(6, 3))
    investor_type: Mapped[Optional[str]] = mapped_column(String(30))
    has_lockup: Mapped[bool] = mapped_column(Boolean, default=False)
    lockup_days: Mapped[Optional[int]] = mapped_column(Integer)
    registration_rights: Mapped[bool] = mapped_column(Boolean, default=False)
    closing_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint("issuer_id", "trading_date"),
        {"schema": "core"},
    )
    price_history_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"))
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    high_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    low_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    close_usd: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    adj_close_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = {"schema": "core"}
    watchlist_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    items: Mapped[list["WatchlistItem"]] = relationship(back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "issuer_id"),
        {"schema": "core"},
    )
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("core.watchlists.watchlist_id", ondelete="CASCADE"))
    issuer_id: Mapped[int] = mapped_column(ForeignKey("core.issuers.issuer_id"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")
