# [동기화] football-data.org 1시간 폴링 -> Aurora Writer UPSERT. 분당 10회 한도 준수

from datetime import datetime
from app.core.database import WriterSessionLocal
from app.models.tables import Team, Match
from app.services.football_api import fetch_matches


def parse_datetime(utc_date: str):
    return datetime.fromisoformat(utc_date.replace("Z", "+00:00"))


def get_or_create_team(db, team_data):
    external_id = team_data.get("id")
    name = team_data.get("name")
    flag_url = team_data.get("crest")

    team = db.query(Team).filter(Team.external_id == external_id).first()

    if team:
        team.name = name
        team.flag_url = flag_url
        return team

    team = Team(
        external_id=external_id,
        name=name,
        country=None,
        flag_url=flag_url
    )

    db.add(team)
    db.flush()

    return team


def upsert_match(db, match_data):
    external_id = match_data.get("id")
    utc_date = match_data.get("utcDate")
    status = match_data.get("status")

    home_team_data = match_data.get("homeTeam", {})
    away_team_data = match_data.get("awayTeam", {})

    score = match_data.get("score", {})
    full_time = score.get("fullTime", {})

    home_score = full_time.get("home")
    away_score = full_time.get("away")

    home_team = get_or_create_team(db, home_team_data)
    away_team = get_or_create_team(db, away_team_data)

    match = db.query(Match).filter(Match.external_id == external_id).first()

    if match:
        match.match_date = parse_datetime(utc_date)
        match.home_team_id = home_team.id
        match.away_team_id = away_team.id
        match.home_score = home_score
        match.away_score = away_score
        match.status = status
        return "updated"

    match = Match(
        external_id=external_id,
        match_date=parse_datetime(utc_date),
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        home_score=home_score,
        away_score=away_score,
        status=status
    )

    db.add(match)
    return "created"


def sync_matches():
    db = WriterSessionLocal()

    created_count = 0
    updated_count = 0

    try:
        data = fetch_matches()
        matches = data.get("matches", [])

        for match_data in matches:
            result = upsert_match(db, match_data)

            if result == "created":
                created_count += 1
            elif result == "updated":
                updated_count += 1

        db.commit()

        print("경기 데이터 동기화 완료")
        print(f"생성: {created_count}건")
        print(f"갱신: {updated_count}건")

    except Exception as e:
        db.rollback()
        print(f"경기 데이터 동기화 실패: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    sync_matches()