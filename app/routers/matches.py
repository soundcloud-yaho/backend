from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_reader_db
from app.models.schemas import Match, MatchSchema, PaginatedMatchSchema, Team

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=List[MatchSchema])
async def get_matches(
    date: Optional[date] = None,
    team: Optional[int] = None,
    db: AsyncSession = Depends(get_reader_db),
):
    try:
        stmt = select(Match).options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )

        if date is not None:
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)
            stmt = stmt.where(Match.match_date >= start, Match.match_date < end)

        if team is not None:
            stmt = stmt.where(
                or_(Match.home_team_id == team, Match.away_team_id == team)
            )

        stmt = stmt.order_by(Match.match_date.asc())
        result = await db.execute(stmt)
        return result.unique().scalars().all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=PaginatedMatchSchema)
async def get_all_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_reader_db),
):
    try:
        offset = (page - 1) * limit

        total_result = await db.execute(select(func.count()).select_from(Match))
        total = total_result.scalar()

        stmt = (
            select(Match)
            .options(joinedload(Match.home_team), joinedload(Match.away_team))
            .order_by(Match.match_date.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        matches = result.unique().scalars().all()

        return PaginatedMatchSchema(total=total, page=page, limit=limit, matches=matches)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today", response_model=List[MatchSchema])
async def get_today_matches(
    db: AsyncSession = Depends(get_reader_db),
):
    try:
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        stmt = (
            select(Match)
            .options(joinedload(Match.home_team), joinedload(Match.away_team))
            .where(Match.match_date >= start, Match.match_date < end)
            .order_by(Match.match_date.asc())
        )
        result = await db.execute(stmt)
        return result.unique().scalars().all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{match_id}", response_model=MatchSchema)
async def get_match_by_id(
    match_id: int,
    db: AsyncSession = Depends(get_reader_db),
):
    stmt = (
        select(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .where(Match.id == match_id)
    )
    result = await db.execute(stmt)
    match = result.unique().scalar_one_or_none()

    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return match