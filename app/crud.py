# crud.py

from sqlalchemy.orm import Session, aliased
from sqlalchemy import cast, Date
from app.models.tables import Match, Team


def get_matches(db: Session, date: str | None = None, team: str | None = None):
    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)

    query = (
        db.query(
            Match.id.label("match_id"),
            cast(Match.match_date, Date).label("date"),
            HomeTeam.name.label("home_team"),
            AwayTeam.name.label("away_team"),
            Match.home_score,
            Match.away_score,
            Match.status,
        )
        .join(HomeTeam, Match.home_team_id == HomeTeam.id)
        .join(AwayTeam, Match.away_team_id == AwayTeam.id)
    )

    if date:
        query = query.filter(cast(Match.match_date, Date) == date)

    if team:
        query = query.filter(
            (HomeTeam.name.ilike(f"%{team}%")) |
            (AwayTeam.name.ilike(f"%{team}%"))
        )

    return query.all()