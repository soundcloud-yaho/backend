# [스키마] matches/teams 테이블 모델 + API 응답 JSON 형식

# 프론트엔드와 합의 필요, 임의 변경 금지
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.core.database import Base

# ── ORM 모델 (DB 테이블) ──────────────────────────────
class Team(Base):
    __tablename__ = "teams"
    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)
    short_name = Column(String(50))
    crest_url  = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Match(Base):
    __tablename__ = "matches"
    id           = Column(Integer, primary_key=True)
    match_date   = Column(DateTime, nullable=False)
    status       = Column(String(20), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score   = Column(Integer)
    away_score   = Column(Integer)
    stage        = Column(String(50))
    matchday     = Column(Integer)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())
    home_team    = relationship("Team", foreign_keys=[home_team_id])
    away_team    = relationship("Team", foreign_keys=[away_team_id])

# ── Pydantic 스키마 (API 응답) ────────────────────────
class TeamSchema(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    crest_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class MatchSchema(BaseModel):
    id: int
    match_date: datetime
    status: str
    stage: Optional[str] = None
    matchday: Optional[int] = None
    home_team: TeamSchema
    away_team: TeamSchema
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class PaginatedMatchSchema(BaseModel):
    total:   int
    page:    int
    limit:   int
    matches: List[MatchSchema]  # Python 3.6은 list[...] 불가 → List[...] 사용