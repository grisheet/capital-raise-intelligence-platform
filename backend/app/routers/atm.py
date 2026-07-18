from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_db
from app.models import AtmProgram, Issuer
from app import schemas

router = APIRouter(prefix="/atm", tags=["atm"])


@router.get("/", response_model=List[schemas.AtmProgramRead])
async def list_atm_programs(
    status: Optional[str] = Query(None),
    issuer_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(AtmProgram)
    if status:
        q = q.where(AtmProgram.status == status)
    if issuer_id:
        q = q.where(AtmProgram.issuer_id == issuer_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{atm_program_id}", response_model=schemas.AtmProgramRead)
async def get_atm_program(atm_program_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AtmProgram).where(AtmProgram.atm_program_id == atm_program_id)
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="ATM program not found")
    return program
