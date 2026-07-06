# [DB] 커넥션 풀 — Writer/Reader 엔드포인트 분리, 풀 사이즈 상한 (Aurora 커넥션 보호)

# Aurora Writer/Reader 분리 연결
# 쓰기는 Writer 인스턴스(CronJob 전용), 읽기는 Reader 인스턴스(FastAPI Pod 전용)로 나눠서
# Reader의 읽기 부하가 Writer에 영향을 주지 않도록 하고, 읽기 트래픽을 여러 Reader로 분산시키기 위함이다.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base  # 구버전 방식

load_dotenv()

DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME     = os.getenv("DB_NAME", "worldcup")
DB_WRITER   = os.getenv("DB_WRITER_HOST", "localhost")
DB_READER   = os.getenv("DB_READER_HOST", "localhost")

WRITER_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_WRITER}/{DB_NAME}"
READER_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_READER}/{DB_NAME}"

writer_engine = create_engine(WRITER_URL, pool_size=5,  pool_pre_ping=True)
reader_engine = create_engine(READER_URL, pool_size=10, pool_pre_ping=True)

WriterSession = sessionmaker(autocommit=False, autoflush=False, bind=writer_engine)
ReaderSession = sessionmaker(autocommit=False, autoflush=False, bind=reader_engine)

# SQLAlchemy 1.x 방식 Base (DeclarativeBase는 2.0+에서만 사용 가능)
Base = declarative_base()

def get_reader_db():
    db = ReaderSession()
    try:
        yield db
    finally:
        db.close()

