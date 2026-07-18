from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_db
from app.models import Issuer
from app.models_derived import DilutionMetrics, CompanyRiskScore
from app import schemas

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[schemas.IssuerRead])
async def list_companies(
    sector: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(Issuer).where(Issuer.is_active == True)
    if sector:
        q = q.where(Issuer.sector == sector)
    if ticker:
        q = q.where(Issuer.ticker.ilike(f"%{ticker}%"))
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{issuer_id}", response_model=schemas.IssuerRead)
async def get_company(issuer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Issuer).where(Issuer.issuer_id == issuer_id)
    )
    issuer = result.scalar_one_or_none()
    if not issuer:
        raise HTTPException(status_code=404, detail="Issuer not found")
    return issuer


@router.get("/{issuer_id}/dilution", response_model=schemas.DilutionMetricsRead)
async def get_dilution_metrics(issuer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DilutionMetrics)
        .where(DilutionMetrics.issuer_id == issuer_id)
        .order_by(DilutionMetrics.as_of_date.desc())
        .limit(1)
    )
    metrics = result.scalar_one_or_none()
    if not metrics:
        raise HTTPException(status_code=404, detail="Dilution metrics not found")
    return metrics


@router.get("/{issuer_id}/risk", response_model=schemas.CompanyRiskScoreRead)
async def get_risk_score(issuer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompanyRiskScore)
        .where(CompanyRiskScore.issuer_id == issuer_id)
        .order_by(CompanyRiskScore.as_of_date.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Risk score not found")
    return score
