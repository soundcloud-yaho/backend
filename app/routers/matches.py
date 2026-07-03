# [API] GET /matches, /matches?date=, /matches?team= — Reader 엔드포인트로 조회

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.schemas import MatchListResponse # 스키마 불러오기
from app import crud

router = APIRouter(
    prefix="/matches",
    tags=["matches"]
)


@router.get("", response_model=MatchListResponse)
def get_matches(
    date: Optional[str] = None,
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    matches = crud.get_matches(db, date=date, team=team)

    return {
        "count": len(matches),
        "matches": matches
    }