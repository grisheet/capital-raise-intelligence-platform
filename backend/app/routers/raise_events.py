from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date

from app.db import get_db
from app.models import RaiseEvent, Issuer
from app.models_derived import EventStudyResult
from app import schemas

router = APIRouter(prefix="/raise-events", tags=["raise_events"])


@router.get("/", response_model=schemas.PaginatedRaiseEvents)
async def screener(
    raise_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    min_proceeds: Optional[float] = Query(None),
    max_proceeds: Optional[float] = Query(None),
    min_discount: Optional[float] = Query(None),
    max_discount: Optional[float] = Query(None),
    announced_after: Optional[date] = Query(None),
    announced_before: Optional[date] = Query(None),
    ticker: Optional[str] = Query(None),
    has_warrants: Optional[bool] = Query(None),
    structure_class: Optional[str] = Query(None),
    is_variable_price: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if raise_type:
        filters.append(RaiseEvent.raise_type == raise_type)
    if status:
        filters.append(RaiseEvent.status == status)
    if min_proceeds is not None:
        filters.append(RaiseEvent.gross_proceeds >= min_proceeds)
    if max_proceeds is not None:
        filters.append(RaiseEvent.gross_proceeds <= max_proceeds)
    if min_discount is not None:
        filters.append(RaiseEvent.discount_to_market >= min_discount)
    if max_discount is not None:
        filters.append(RaiseEvent.discount_to_market <= max_discount)
    if announced_after:
        filters.append(RaiseEvent.announced_date >= announced_after)
    if announced_before:
        filters.append(RaiseEvent.announced_date <= announced_before)
    if has_warrants is not None:
        filters.append(RaiseEvent.has_warrants == has_warrants)
    if structure_class:
        filters.append(RaiseEvent.structure_class == structure_class)
    if is_variable_price is not None:
        filters.append(RaiseEvent.is_variable_price == is_variable_price)

    base_q = select(RaiseEvent)
    if sector or ticker:
        base_q = base_q.join(Issuer, RaiseEvent.issuer_id == Issuer.issuer_id)
        if sector:
            filters.append(Issuer.sector == sector)
        if ticker:
            filters.append(Issuer.ticker.ilike(f"%{ticker}%"))

    if filters:
        base_q = base_q.where(and_(*filters))

    count_q = select(RaiseEvent.raise_event_id)
    if sector or ticker:
        count_q = count_q.join(Issuer, RaiseEvent.issuer_id == Issuer.issuer_id)
    if filters:
        count_q = count_q.where(and_(*filters))

    count_result = await db.execute(count_q)
    total = len(count_result.all())

    offset = (page - 1) * page_size
    data_q = base_q.order_by(RaiseEvent.announced_date.desc()).offset(offset).limit(page_size)
    result = await db.execute(data_q)
    items = result.scalars().all()

    return schemas.PaginatedRaiseEvents(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{raise_event_id}", response_model=schemas.RaiseEventRead)
async def get_raise_event(raise_event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RaiseEvent).where(RaiseEvent.raise_event_id == raise_event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Raise event not found")
    return event


@router.get("/{raise_event_id}/event-study", response_model=schemas.EventStudyResultRead)
async def get_event_study(raise_event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EventStudyResult)
        .where(EventStudyResult.raise_event_id == raise_event_id)
        .order_by(EventStudyResult.computed_at.desc())
        .limit(1)
    )
    study = result.scalar_one_or_none()
    if not study:
        raise HTTPException(status_code=404, detail="Event study result not found")
    return study
