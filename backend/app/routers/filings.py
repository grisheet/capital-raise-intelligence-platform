from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date

from app.db import get_db
from app.models import Filing, Issuer
from app import schemas

router = APIRouter(prefix="/filings", tags=["filings"])


@router.get("/", response_model=List[schemas.FilingRead])
async def list_filings(
    issuer_id: Optional[int] = Query(None),
    form_type: Optional[str] = Query(None),
    filed_after: Optional[date] = Query(None),
    filed_before: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(Filing)
    if issuer_id:
        q = q.where(Filing.issuer_id == issuer_id)
    if form_type:
        q = q.where(Filing.form_type == form_type)
    if filed_after:
        q = q.where(Filing.filing_date >= filed_after)
    if filed_before:
        q = q.where(Filing.filing_date <= filed_before)
    q = q.order_by(Filing.filing_date.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{filing_id}", response_model=schemas.FilingRead)
async def get_filing(filing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Filing).where(Filing.filing_id == filing_id)
    )
    filing = result.scalar_one_or_none()
    if not filing:
        raise HTTPException(status_code=404, detail="Filing not found")
    return filing
