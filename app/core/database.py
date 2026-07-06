# [DB] 커넥션 풀 — Writer/Reader 엔드포인트 분리, 풀 사이즈 상한 (Aurora 커넥션 보호)
# [DB] 커넥션 풀 — Writer/Reader 엔드포인트 분리, 풀 사이즈 상한

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


def make_database_url(host: str):
    user = quote_plus(settings.DB_USER)
    password = quote_plus(settings.DB_PASSWORD)

    return (
        f"postgresql://{user}:{password}"
        f"@{host}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


reader_engine = create_engine(
    make_database_url(settings.DB_READER_HOST),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

writer_engine = create_engine(
    make_database_url(settings.DB_WRITER_HOST),
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=3,
)

ReaderSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=reader_engine,
)

WriterSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=writer_engine,
)

Base = declarative_base()


def get_db():
    db = ReaderSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_reader_db():
    yield from get_db()


def get_writer_db():
    db = WriterSessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    try:
        with reader_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False