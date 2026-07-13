# [동기화]
# football-data.org 1시간 폴링 -> Aurora Writer UPSERT
# 무료 플랜 분당 10회 호출 한도 준수

from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.database import WriterSessionLocal
from app.models.schemas import Match, Team


FOOTBALL_DATA_URL = (
    "https://api.football-data.org/v4/competitions/WC/matches"
)


def sync_worldcup_matches() -> None:
    db = WriterSessionLocal()

    created_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        api_key = getattr(
            settings,
            "FOOTBALL_DATA_API_KEY",
            None,
        )

        if not api_key:
            raise RuntimeError(
                "FOOTBALL_DATA_API_KEY 환경변수가 설정되지 않았습니다."
            )

        print("[SYNC] 월드컵 경기 동기화를 시작합니다.")
        print(f"[SYNC] 요청 URL: {FOOTBALL_DATA_URL}")

        with httpx.Client(
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            response = client.get(
                FOOTBALL_DATA_URL,
                headers={
                    "X-Auth-Token": api_key,
                    "Accept": "application/json",
                },
            )

        print(
            "[SYNC] football-data.org 응답 코드: "
            f"{response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                "football-data.org 응답이 객체 형식이 아닙니다."
            )

        matches = data.get("matches") or []

        if not isinstance(matches, list):
            raise ValueError(
                "football-data.org의 matches 값이 배열이 아닙니다."
            )

        print(f"[SYNC] 수집된 경기 수: {len(matches)}건")

        if not matches:
            print(
                "[SYNC] 수집된 경기 데이터가 없습니다. "
                "DB 저장 없이 종료합니다."
            )
            return

        for match_data in matches:
            match_id = (
                match_data.get("id")
                if isinstance(match_data, dict)
                else "unknown"
            )

            try:
                if not isinstance(match_data, dict):
                    raise ValueError(
                        "경기 데이터가 객체 형식이 아닙니다."
                    )

                # 경기 한 건마다 SAVEPOINT 사용
                # 한 경기에서 오류가 발생해도 나머지는 계속 처리
                with db.begin_nested():
                    home_team_data = (
                        match_data.get("homeTeam") or {}
                    )
                    away_team_data = (
                        match_data.get("awayTeam") or {}
                    )

                    home_team = _upsert_team(
                        db,
                        home_team_data,
                    )
                    away_team = _upsert_team(
                        db,
                        away_team_data,
                    )

                    if home_team is None:
                        raise ValueError(
                            "홈팀 ID 또는 이름이 없습니다."
                        )

                    if away_team is None:
                        raise ValueError(
                            "원정팀 ID 또는 이름이 없습니다."
                        )

                    # 새로 생성된 Team의 ID를 Match에서 사용하기 위해 flush
                    db.flush()

                    result = _upsert_match(
                        db=db,
                        match_data=match_data,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                    )

                    db.flush()

                if result == "created":
                    created_count += 1
                elif result == "updated":
                    updated_count += 1

            except Exception as match_error:
                skipped_count += 1

                print(
                    f"[SYNC] 경기 건너뜀 "
                    f"(match_id={match_id}): {match_error}"
                )

                # begin_nested() 내부 오류이므로
                # 해당 경기만 rollback되고 다음 경기 처리 가능
                continue

        db.commit()

        print("[SYNC] 월드컵 경기 동기화 완료")
        print(f"[SYNC] 생성: {created_count}건")
        print(f"[SYNC] 갱신: {updated_count}건")
        print(f"[SYNC] 건너뜀: {skipped_count}건")
        print("[SYNC] DB 반영이 정상적으로 완료되었습니다.")

    except httpx.TimeoutException:
        db.rollback()
        print("[SYNC] football-data.org 요청 시간이 초과되었습니다.")
        print("[SYNC] DB 변경사항을 rollback 처리했습니다.")
        raise

    except httpx.HTTPStatusError as error:
        db.rollback()

        status_code = error.response.status_code
        response_text = error.response.text[:500]

        print("[SYNC] football-data.org API 요청에 실패했습니다.")
        print(f"[SYNC] HTTP 상태 코드: {status_code}")
        print(f"[SYNC] 응답 내용: {response_text}")
        print("[SYNC] DB 변경사항을 rollback 처리했습니다.")

        raise

    except Exception as error:
        db.rollback()

        print("[SYNC] 월드컵 경기 동기화 실패")
        print(f"[SYNC] 실패 원인: {error}")
        print("[SYNC] DB 변경사항을 rollback 처리했습니다.")

        raise

    finally:
        db.close()
        print("[SYNC] DB 세션을 종료했습니다.")


def _upsert_team(
    db: Any,
    team_data: dict[str, Any],
) -> Team | None:
    """
    football-data.org 팀 정보를 teams 테이블에 UPSERT한다.

    tla:
        MEX, KOR, QAT 같은 3자리 팀 코드

    shortName:
        Mexico, Korea Republic 같은 축약 팀 이름

    프론트에서 코드로 사용할 수 있도록 tla를 우선 저장한다.
    """

    team_id = team_data.get("id")
    team_name = team_data.get("name")

    if team_id is None or not team_name:
        return None

    short_name = (
        team_data.get("tla")
        or team_data.get("shortName")
        or team_name
    )

    crest_url = team_data.get("crest")

    team = (
        db.query(Team)
        .filter(Team.id == team_id)
        .first()
    )

    if team:
        team.name = team_name
        team.short_name = short_name

        # API에서 crest가 비어 있을 때
        # 기존 DB의 정상 URL을 None으로 덮지 않는다.
        if crest_url:
            team.crest_url = crest_url

        return team

    team = Team(
        id=team_id,
        name=team_name,
        short_name=short_name,
        crest_url=crest_url,
    )

    db.add(team)

    return team


def _upsert_match(
    db: Any,
    match_data: dict[str, Any],
    home_team_id: int,
    away_team_id: int,
) -> str:
    """
    경기 기본 정보와 최종 점수를 matches 테이블에 UPSERT한다.
    """

    match_id = match_data.get("id")
    utc_date = match_data.get("utcDate")

    if match_id is None:
        raise ValueError("경기 ID가 없습니다.")

    if not utc_date:
        raise ValueError("경기 utcDate 값이 없습니다.")

    score = match_data.get("score") or {}

    if not isinstance(score, dict):
        score = {}

    full_time = score.get("fullTime") or {}

    if not isinstance(full_time, dict):
        full_time = {}

    # 경기 전에는 점수가 None인 것이 정상
    home_score = full_time.get("home")
    away_score = full_time.get("away")

    try:
        match_date = datetime.fromisoformat(
            str(utc_date).replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError(
            f"올바르지 않은 utcDate 형식입니다: {utc_date}"
        ) from error

    status = match_data.get("status") or "SCHEDULED"
    stage = match_data.get("stage")
    matchday = match_data.get("matchday")

    match = (
        db.query(Match)
        .filter(Match.id == match_id)
        .first()
    )

    if match:
        match.match_date = match_date
        match.status = status
        match.home_team_id = home_team_id
        match.away_team_id = away_team_id
        match.home_score = home_score
        match.away_score = away_score
        match.stage = stage
        match.matchday = matchday

        return "updated"

    match = Match(
        id=match_id,
        match_date=match_date,
        status=status,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=home_score,
        away_score=away_score,
        stage=stage,
        matchday=matchday,
    )

    db.add(match)

    return "created"


if __name__ == "__main__":
    sync_worldcup_matches()