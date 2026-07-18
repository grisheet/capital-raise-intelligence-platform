from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.db import get_db
from app.models import Watchlist, WatchlistItem, Issuer
from app import schemas

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("/", response_model=List[schemas.WatchlistRead])
async def list_watchlists(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user_id)
    )
    watchlists = result.scalars().all()
    out = []
    for wl in watchlists:
        count_result = await db.execute(
            select(func.count(WatchlistItem.item_id)).where(
                WatchlistItem.watchlist_id == wl.watchlist_id
            )
        )
        count = count_result.scalar_one_or_none() or 0
        out.append(
            schemas.WatchlistRead(
                watchlist_id=wl.watchlist_id,
                user_id=wl.user_id,
                name=wl.name,
                created_at=wl.created_at,
                issuer_count=count,
            )
        )
    return out


@router.post("/", response_model=schemas.WatchlistRead, status_code=201)
async def create_watchlist(
    payload: schemas.WatchlistCreate,
    db: AsyncSession = Depends(get_db),
):
    wl = Watchlist(name=payload.name, user_id=payload.user_id)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return schemas.WatchlistRead(
        watchlist_id=wl.watchlist_id,
        user_id=wl.user_id,
        name=wl.name,
        created_at=wl.created_at,
        issuer_count=0,
    )


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Watchlist).where(Watchlist.watchlist_id == watchlist_id)
    )
    wl = result.scalar_one_or_none()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    await db.delete(wl)
    await db.commit()


@router.post("/{watchlist_id}/issuers/{issuer_id}", status_code=201)
async def add_issuer_to_watchlist(
    watchlist_id: int, issuer_id: int, db: AsyncSession = Depends(get_db)
):
    item = WatchlistItem(watchlist_id=watchlist_id, issuer_id=issuer_id)
    db.add(item)
    await db.commit()
    return {"status": "added"}


@router.delete("/{watchlist_id}/issuers/{issuer_id}", status_code=204)
async def remove_issuer_from_watchlist(
    watchlist_id: int, issuer_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.issuer_id == issuer_id,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
