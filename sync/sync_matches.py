# [동기화] football-data.org 1시간 폴링 -> Aurora Writer UPSERT. 분당 10회 한도 준수

from datetime import datetime

import httpx

from app.core.config import settings
from app.core.database import WriterSessionLocal
from app.models.schemas import Match, Team

FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions/WC/matches"


def sync_worldcup_matches():
    db = WriterSessionLocal()

    created_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        print("[SYNC] 월드컵 경기 동기화를 시작합니다.")
        print(f"[SYNC] 요청 URL: {FOOTBALL_DATA_URL}")

        response = httpx.get(
            FOOTBALL_DATA_URL,
            headers={"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY},
            timeout=30.0,
        )

        print(f"[SYNC] football-data.org 응답 코드: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        matches = data.get("matches", [])
        print(f"[SYNC] 수집된 경기 수: {len(matches)}건")

        if not matches:
            print("[SYNC] 수집된 경기 데이터가 없습니다. DB 저장 없이 종료합니다.")
            return

        for match_data in matches:
            home_team = _upsert_team(db, match_data.get("homeTeam", {}))
            away_team = _upsert_team(db, match_data.get("awayTeam", {}))

            if not home_team or not away_team:
                skipped_count += 1
                continue

            db.flush()

            result = _upsert_match(db, match_data, home_team.id, away_team.id)

            if result == "created":
                created_count += 1
            elif result == "updated":
                updated_count += 1

        db.commit()

        print("[SYNC] 월드컵 경기 동기화 완료")
        print(f"[SYNC] 생성: {created_count}건")
        print(f"[SYNC] 갱신: {updated_count}건")
        print(f"[SYNC] 건너뜀: {skipped_count}건")
        print("[SYNC] DB 반영이 정상적으로 완료되었습니다.")

    except Exception as e:
        db.rollback()
        print("[SYNC] 월드컵 경기 동기화 실패")
        print(f"[SYNC] 실패 원인: {e}")
        print("[SYNC] DB 변경사항은 rollback 처리되었습니다.")
        raise

    finally:
        db.close()
        print("[SYNC] DB 세션을 종료했습니다.")


def _upsert_team(db, team_data):
    if not team_data.get("name") or not team_data.get("id"):
        return None

    team = db.query(Team).filter(Team.id == team_data["id"]).first()

    if team:
        team.name = team_data.get("name")
        team.short_name = team_data.get("shortName")
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
    full_time = match_data.get("score", {}).get("fullTime", {})
    home_score = full_time.get("home")
    away_score = full_time.get("away")

    match = db.query(Match).filter(Match.id == match_data["id"]).first()

    match_date = datetime.fromisoformat(
        match_data["utcDate"].replace("Z", "+00:00")
    )

    if match:
        match.match_date = match_date
        match.status = match_data.get("status")
        match.home_team_id = home_team_id
        match.away_team_id = away_team_id
        match.home_score = home_score
        match.away_score = away_score
        match.stage = match_data.get("stage")
        match.matchday = match_data.get("matchday")
        return "updated"

    match = Match(
        id=match_data["id"],
        match_date=match_date,
        status=match_data.get("status"),
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=home_score,
        away_score=away_score,
        stage=match_data.get("stage"),
        matchday=match_data.get("matchday"),
    )
    db.add(match)

    return "created"


if __name__ == "__main__":
    sync_worldcup_matches()