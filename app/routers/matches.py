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
            query = query.filter(
                or_(
                    Match.home_team_id == team,
                    Match.away_team_id == team,
                )
            )

        return query.order_by(Match.match_date.asc()).all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))