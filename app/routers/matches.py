# [API] 경기 조회 API — Reader 엔드포인트 사용
# GET /matches
# GET /matches/all
# GET /matches/today
# GET /matches/{match_id}

from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_reader_db
from app.models.schemas import Match, MatchSchema, PaginatedMatchSchema, Team

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=List[MatchSchema])
def get_matches(
    date: Optional[date] = None,
    team: Optional[int] = None,
    db: Session = Depends(get_reader_db),
):
    """
    경기 목록 조회
    - /matches
    - /matches?date=2026-07-08
    - /matches?team=772
    """
    try:
        query = (
            db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
        )

        if date is not None:
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.filter(Match.match_date >= start, Match.match_date < end)

        if team is not None:
            query = (
                query.join(
                    Team,
                    or_(
                        Match.home_team_id == Team,
                        Match.away_team_id == Team,
                    ),
                )
                .filter(
                    or_(
                        Team.name.ilike(f"%{team}%"),
                        Team.short_name.ilike(f"%{team}%"),
                    )
                )
            )

        return query.order_by(Match.match_date.asc()).all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=PaginatedMatchSchema)
def get_all_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_reader_db),
):
    """
    페이지네이션 경기 목록 조회
    - /matches/all?page=1&limit=20
    """
    try:
        offset = (page - 1) * limit

        total = db.query(Match).count()

        matches = (
            db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .order_by(Match.match_date.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return PaginatedMatchSchema(
            total=total,
            page=page,
            limit=limit,
            matches=matches,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today", response_model=List[MatchSchema])
def get_today_matches(
    db: Session = Depends(get_reader_db),
):
    """
    오늘 경기 조회
    - /matches/today
    """
    try:
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        return (
            db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(Match.match_date >= start, Match.match_date < end)
            .order_by(Match.match_date.asc())
            .all()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{match_id}", response_model=MatchSchema)
def get_match_by_id(
    match_id: int,
    db: Session = Depends(get_reader_db),
):
    """
    단일 경기 조회
    - /matches/1
    """
    match = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )
        .filter(Match.id == match_id)
        .first()
    )

    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return match