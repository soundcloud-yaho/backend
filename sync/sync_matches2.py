# [동기화] football-data.org 1시간 폴링 -> Aurora Writer UPSERT. 분당 10회 한도 준수

# 1시간 주기로 football-data.org에서 월드컵 경기 데이터를 가져와 DB에 동기화하는 배치 스크립트
# football-data.org 무료 플랜은 분당 10회 호출 제한이 있으므로 준수해야 한다 (본 스크립트는 1회 호출만 수행)
from datetime import datetime

import httpx

from app.core.config import get_settings
from app.core.database import WriterSession
from TEAM3.backend.app.models.schemas2 import Match, Team

FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions/WC/matches"


def sync_worldcup_matches():
    settings = get_settings()
    db = WriterSession()  # 쓰기 작업이므로 Reader가 아닌 Writer DB 세션 사용

    try:
        response = httpx.get(
            FOOTBALL_DATA_URL,
            headers={"X-Auth-Token": settings.football_data_api_key},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        for match_data in data.get("matches", []):
            # 매치를 저장하기 전에 팀을 먼저 저장해야 한다.
            # matches.home_team_id / away_team_id가 teams.id를 참조하는 외래키라
            # 팀이 없는 상태로 매치를 저장하면 외래키 제약조건 오류가 발생한다.
            home_team = _upsert_team(db, match_data["homeTeam"])
            away_team = _upsert_team(db, match_data["awayTeam"])

            # 팀이 미정인 경기는 건너뜀
            if not home_team or not away_team:
                continue

            db.flush()  # 신규 팀의 id를 매치 저장 전에 확정

            _upsert_match(db, match_data, home_team.id, away_team.id)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"월드컵 경기 동기화 실패: {e}")
        raise
    finally:
        db.close()


def _upsert_team(db, team_data):
    # 팀 이름이 없으면 (토너먼트 대진 미정) 건너뜁니다
    if not team_data.get("name") or not team_data.get("id"):
        return None   # ← 미정처리 추가

    # teams 테이블 UPSERT: 있으면 name/crest_url 업데이트, 없으면 새로 INSERT
    team = db.query(Team).filter(Team.id == team_data["id"]).first()
    if team:
        team.name = team_data.get("name")
        team.crest_url = team_data.get("crest")
    else:
        team = Team(
            id=team_data["id"],
            name=team_data.get("name"),
            short_name=team_data.get("shortName"),
            crest_url=team_data.get("crest"),
        )
        db.add(team)
    return team


def _upsert_match(db, match_data, home_team_id, away_team_id):
    # matches 테이블 UPSERT: 있으면 status/score 업데이트, 없으면 새로 INSERT
    full_time = match_data.get("score", {}).get("fullTime", {})
    home_score = full_time.get("home")
    away_score = full_time.get("away")

    match = db.query(Match).filter(Match.id == match_data["id"]).first()
    if match:
        match.status = match_data.get("status")
        match.home_score = home_score
        match.away_score = away_score
    else:
        match = Match(
            id=match_data["id"],
            utc_date=datetime.strptime(match_data["utcDate"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S"),
            status=match_data.get("status"),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            stage=match_data.get("stage"),
            matchday=match_data.get("matchday"),
        )
        db.add(match)


if __name__ == "__main__":
    sync_worldcup_matches()
