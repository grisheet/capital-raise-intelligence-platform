from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_db
from app.models import PrivatePlacement
from app import schemas

router = APIRouter(prefix="/placements", tags=["placements"])


@router.get("/", response_model=List[schemas.PrivatePlacementRead])
async def list_placements(
    issuer_id: Optional[int] = Query(None),
    placement_type: Optional[str] = Query(None),
    has_warrants: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(PrivatePlacement)
    if issuer_id:
        q = q.where(PrivatePlacement.issuer_id == issuer_id)
    if placement_type:
        q = q.where(PrivatePlacement.placement_type == placement_type)
    if has_warrants is not None:
        q = q.where(PrivatePlacement.has_warrants == has_warrants)
    q = q.order_by(PrivatePlacement.closing_date.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{placement_id}", response_model=schemas.PrivatePlacementRead)
async def get_placement(placement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PrivatePlacement).where(PrivatePlacement.placement_id == placement_id)
    )
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Private placement not found")
    return placement
