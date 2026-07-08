# [DB] 커넥션 풀 — Writer/Reader 엔드포인트 분리, 풀 사이즈 상한

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


def make_database_url(host: str) -> str:
    user = quote_plus(settings.DB_USER)
    password = quote_plus(settings.DB_PASSWORD)

    return (
        f"postgresql://{user}:{password}"
        f"@{host}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_database_url(url_env_name: str, host_value: str | None, fallback_name: str) -> str:
    """
    1순위: WRITABLE_URL / READONLY_URL 전체 URL 사용
    2순위: DB_WRITER_HOST / DB_READER_HOST + DB_USER 조합
    """
    url = os.getenv(url_env_name)

    if url:
        return url

    if host_value:
        return make_database_url(host_value)

    raise RuntimeError(
        f"{url_env_name} 또는 {fallback_name} 환경변수가 필요합니다."
    )


WRITABLE_URL = get_database_url(
    "WRITABLE_URL",
    getattr(settings, "DB_WRITER_HOST", None),
    "DB_WRITER_HOST",
)

READONLY_URL = get_database_url(
    "READONLY_URL",
    getattr(settings, "DB_READER_HOST", None),
    "DB_READER_HOST",
)


writer_engine = create_engine(
    WRITABLE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=3,
)

reader_engine = create_engine(
    READONLY_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
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