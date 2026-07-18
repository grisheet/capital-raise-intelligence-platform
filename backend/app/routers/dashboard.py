from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List

from app.db import get_db
from app.models import Issuer, RaiseEvent, AtmProgram, Filing
from app.models_derived import CompanyRiskScore
from app import schemas

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Return high-level dashboard statistics for the last 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)

    # Total deals & proceeds in last 30 days
    result = await db.execute(
        select(
            func.count(RaiseEvent.raise_event_id).label("deal_count"),
            func.coalesce(func.sum(RaiseEvent.gross_proceeds), 0).label("total_proceeds"),
            func.avg(RaiseEvent.discount_to_market).label("avg_discount"),
        ).where(RaiseEvent.announced_date >= cutoff.date())
    )
    row = result.one()

    # Active ATM programs
    atm_result = await db.execute(
        select(func.count(AtmProgram.atm_program_id)).where(
            AtmProgram.status == "active"
        )
    )
    active_atm = atm_result.scalar_one_or_none() or 0

    # Largest gross proceeds deals
    largest_q = await db.execute(
        select(
            RaiseEvent.raise_event_id,
            Issuer.ticker,
            Issuer.company_name,
            RaiseEvent.raise_type,
            RaiseEvent.gross_proceeds,
            RaiseEvent.announced_date,
            RaiseEvent.discount_to_market,
        )
        .join(Issuer, RaiseEvent.issuer_id == Issuer.issuer_id)
        .where(RaiseEvent.announced_date >= cutoff.date())
        .order_by(RaiseEvent.gross_proceeds.desc().nullslast())
        .limit(10)
    )
    largest = [
        schemas.RaiseEventSummary(
            raise_event_id=r.raise_event_id,
            ticker=r.ticker,
            company_name=r.company_name,
            raise_type=r.raise_type,
            gross_proceeds=r.gross_proceeds,
            announced_date=r.announced_date,
            discount_to_market=r.discount_to_market,
        )
        for r in largest_q.all()
    ]

    # Highest risk issuers
    risk_q = await db.execute(
        select(
            Issuer.issuer_id,
            Issuer.ticker,
            Issuer.company_name,
            Issuer.sector,
            Issuer.market_cap,
        )
        .join(CompanyRiskScore, CompanyRiskScore.issuer_id == Issuer.issuer_id)
        .order_by(CompanyRiskScore.composite_risk_score.desc().nullslast())
        .limit(10)
    )
    high_risk = [
        schemas.IssuerSummary(
            issuer_id=r.issuer_id,
            ticker=r.ticker,
            company_name=r.company_name,
            sector=r.sector,
            market_cap=r.market_cap,
        )
        for r in risk_q.all()
    ]

    # Sector activity
    sector_q = await db.execute(
        select(
            Issuer.sector,
            func.count(RaiseEvent.raise_event_id).label("deal_count"),
            func.coalesce(func.sum(RaiseEvent.gross_proceeds), 0).label("total_proceeds"),
            func.avg(RaiseEvent.discount_to_market).label("avg_discount"),
        )
        .join(Issuer, RaiseEvent.issuer_id == Issuer.issuer_id)
        .where(
            and_(
                RaiseEvent.announced_date >= cutoff.date(),
                Issuer.sector.isnot(None),
            )
        )
        .group_by(Issuer.sector)
        .order_by(func.count(RaiseEvent.raise_event_id).desc())
        .limit(10)
    )
    sectors = [
        schemas.SectorActivity(
            sector=r.sector,
            deal_count=r.deal_count,
            total_proceeds=float(r.total_proceeds),
            avg_discount=r.avg_discount,
        )
        for r in sector_q.all()
    ]

    # Recent filings
    filings_q = await db.execute(
        select(
            Filing.filing_id,
            Issuer.ticker,
            Filing.form_type,
            Filing.filing_date,
            Filing.description,
        )
        .join(Issuer, Filing.issuer_id == Issuer.issuer_id)
        .order_by(Filing.filing_date.desc())
        .limit(20)
    )
    recent_filings = [
        schemas.RecentFilingItem(
            filing_id=r.filing_id,
            ticker=r.ticker,
            form_type=r.form_type,
            filing_date=r.filing_date,
            description=r.description,
        )
        for r in filings_q.all()
    ]

    return schemas.DashboardStats(
        total_deals_30d=row.deal_count,
        total_proceeds_30d=float(row.total_proceeds),
        avg_discount_30d=row.avg_discount,
        active_atm_programs=active_atm,
        largest_gross_proceeds=largest,
        highest_risk_issuers=high_risk,
        sectors_most_active=sectors,
        recent_filings=recent_filings,
    )
