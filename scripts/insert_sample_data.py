# insert_sample_data.py // 샘플 데이터 집어넣기

from datetime import datetime
from app.core.database import SessionLocal
from app.models.tables import Team, Match


db = SessionLocal()

try:
    korea = Team(name="Korea", country="South Korea", flag_url=None)
    japan = Team(name="Japan", country="Japan", flag_url=None)
    brazil = Team(name="Brazil", country="Brazil", flag_url=None)
    germany = Team(name="Germany", country="Germany", flag_url=None)

    db.add_all([korea, japan, brazil, germany])
    db.commit()

    db.refresh(korea)
    db.refresh(japan)
    db.refresh(brazil)
    db.refresh(germany)

    match1 = Match(
        external_id=1001,
        match_date=datetime(2026, 7, 3, 20, 0, 0),
        home_team_id=korea.id,
        away_team_id=japan.id,
        home_score=2,
        away_score=1,
        status="FINISHED"
    )

    match2 = Match(
        external_id=1002,
        match_date=datetime(2026, 7, 4, 20, 0, 0),
        home_team_id=brazil.id,
        away_team_id=germany.id,
        home_score=None,
        away_score=None,
        status="SCHEDULED"
    )

    db.add_all([match1, match2])
    db.commit()

    print("샘플 데이터 삽입 완료")

except Exception as e:
    db.rollback()
    print(f"샘플 데이터 삽입 실패: {e}")

finally:
    db.close()