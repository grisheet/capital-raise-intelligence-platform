from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from typing import List

from app.db import get_db
from app.models import Issuer, RaiseEvent

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/sectors", response_model=List[str])
async def list_sectors(db: AsyncSession = Depends(get_db)):
    """Return all distinct sectors present in the issuers table."""
    result = await db.execute(
        select(distinct(Issuer.sector)).where(Issuer.sector.isnot(None)).order_by(Issuer.sector)
    )
    return [row[0] for row in result.all()]


@router.get("/raise-types", response_model=List[str])
async def list_raise_types(db: AsyncSession = Depends(get_db)):
    """Return all distinct raise types."""
    result = await db.execute(
        select(distinct(RaiseEvent.raise_type)).where(RaiseEvent.raise_type.isnot(None)).order_by(RaiseEvent.raise_type)
    )
    return [row[0] for row in result.all()]


@router.get("/structure-classes", response_model=List[str])
async def list_structure_classes(db: AsyncSession = Depends(get_db)):
    """Return all distinct structure classes."""
    result = await db.execute(
        select(distinct(RaiseEvent.structure_class))
        .where(RaiseEvent.structure_class.isnot(None))
        .order_by(RaiseEvent.structure_class)
    )
    return [row[0] for row in result.all()]


@router.get("/exchanges", response_model=List[str])
async def list_exchanges(db: AsyncSession = Depends(get_db)):
    """Return all distinct exchanges."""
    result = await db.execute(
        select(distinct(Issuer.exchange)).where(Issuer.exchange.isnot(None)).order_by(Issuer.exchange)
    )
    return [row[0] for row in result.all()]
