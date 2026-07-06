# [API] GET /matches, /matches?date=, /matches?team= — Reader 엔드포인트로 조회

# 매치 관련 API 라우터
from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_reader_db
from TEAM3.backend.app.models.schemas2 import Match, MatchSchema, PaginatedMatchSchema, Team

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=List[MatchSchema])
def get_matches(
    date: Optional[date] = None,
    team: Optional[str] = None,
    db: Session = Depends(get_reader_db),
):
    """날짜/팀 이름으로 매치 목록을 조회한다. 조건이 없으면 전체를 반환한다."""
    try:
        query = db.query(Match)

        # 날짜 필터: 해당 날짜의 00:00 ~ 다음날 00:00 사이의 경기만 조회
        if date is not None:
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.filter(Match.utc_date >= start, Match.utc_date < end)

        # 팀 이름 필터: 홈/원정 팀 중 이름이 부분 일치하는 경기 조회
        if team is not None:
            query = query.join(
                Team, or_(Match.home_team_id == Team.id, Match.away_team_id == Team.id)
            ).filter(Team.name.ilike(f"%{team}%"))

        return query.order_by(Match.utc_date.asc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=PaginatedMatchSchema)
def get_all_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_reader_db),
):
    """페이지네이션된 전체 매치 목록을 조회한다."""
    try:
        offset = (page - 1) * limit

        total = db.query(Match).count()
        matches = (
            db.query(Match)
            .order_by(Match.utc_date.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return PaginatedMatchSchema(total=total, page=page, limit=limit, matches=matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
