# [스키마] matches/teams 테이블 모델 + API 응답 JSON 형식

from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class MatchResponse(BaseModel):
    match_id: int
    date: date
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str

#/matches의 응답은 count랑 matches배열로 준다
# matches안에는 경기 id, 날짜, 홈팀, 원정팀, 점수, 상태가 들어간다
class MatchListResponse(BaseModel):
    count: int
    matches: List[MatchResponse]