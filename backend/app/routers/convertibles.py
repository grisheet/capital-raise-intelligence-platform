from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_db
from app.models import ConvertibleInstrument
from app import schemas

router = APIRouter(prefix="/convertibles", tags=["convertibles"])


@router.get("/", response_model=List[schemas.ConvertibleInstrumentRead])
async def list_convertibles(
    status: Optional[str] = Query(None),
    issuer_id: Optional[int] = Query(None),
    instrument_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(ConvertibleInstrument)
    if status:
        q = q.where(ConvertibleInstrument.status == status)
    if issuer_id:
        q = q.where(ConvertibleInstrument.issuer_id == issuer_id)
    if instrument_type:
        q = q.where(ConvertibleInstrument.instrument_type == instrument_type)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{instrument_id}", response_model=schemas.ConvertibleInstrumentRead)
async def get_convertible(instrument_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ConvertibleInstrument).where(
            ConvertibleInstrument.instrument_id == instrument_id
        )
    )
    instrument = result.scalar_one_or_none()
    if not instrument:
        raise HTTPException(status_code=404, detail="Convertible instrument not found")
    return instrument
