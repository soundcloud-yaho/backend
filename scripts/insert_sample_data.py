# insert_sample_data.py // 샘플 데이터 집어넣기

from datetime import datetime

from app.core.database import Base, writer_engine, WriterSessionLocal
from app.models.schemas import Team, Match


# 테이블 없으면 생성
Base.metadata.create_all(bind=writer_engine)

db = WriterSessionLocal()

try:
    korea = Team(name="Korea", short_name="KOR", crest_url=None)
    japan = Team(name="Japan", short_name="JPN", crest_url=None)
    brazil = Team(name="Brazil", short_name="BRA", crest_url=None)
    germany = Team(name="Germany", short_name="GER", crest_url=None)

    db.add_all([korea, japan, brazil, germany])
    db.commit()

    db.refresh(korea)
    db.refresh(japan)
    db.refresh(brazil)
    db.refresh(germany)

    match1 = Match(
        match_date=datetime(2026, 7, 3, 20, 0, 0),
        home_team_id=korea.id,
        away_team_id=japan.id,
        home_score=2,
        away_score=1,
        status="FINISHED",
        stage="Group Stage",
        matchday=1,
    )

    match2 = Match(
        match_date=datetime(2026, 7, 4, 20, 0, 0),
        home_team_id=brazil.id,
        away_team_id=germany.id,
        home_score=None,
        away_score=None,
        status="SCHEDULED",
        stage="Group Stage",
        matchday=1,
    )

    db.add_all([match1, match2])
    db.commit()

    print("샘플 데이터 삽입 완료")

except Exception as e:
    db.rollback()
    print(f"샘플 데이터 삽입 실패: {e}")

finally:
    db.close()