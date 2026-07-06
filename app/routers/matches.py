# [API] GET /matches, /matches?date=, /matches?team= — Reader 엔드포인트로 조회

from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_reader_db
from app.models.schemas import Match, MatchSchema, PaginatedMatchSchema, Team

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=List[MatchSchema])
def get_matches(
    date: Optional[date] = None,
    team: Optional[str] = None,
    db: Session = Depends(get_reader_db),
):
    try:
        query = db.query(Match)

        if date is not None:
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.filter(Match.match_date >= start, Match.match_date < end)

        if team is not None:
            query = query.join(
                Team,
                or_(Match.home_team_id == Team.id, Match.away_team_id == Team.id),
            ).filter(Team.name.ilike(f"%{team}%"))

        return query.order_by(Match.match_date.asc()).all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=PaginatedMatchSchema)
def get_all_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_reader_db),
):
    try:
        offset = (page - 1) * limit

        total = db.query(Match).count()
        matches = (
            db.query(Match)
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