import os
from urllib.parse import quote_plus
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings


def make_database_url(host: str, driver: str = "postgresql") -> str:
    user = quote_plus(settings.DB_USER)
    password = quote_plus(settings.DB_PASSWORD)
    return f"{driver}://{user}:{password}@{host}:{settings.DB_PORT}/{settings.DB_NAME}"


def get_database_url(url_env_name: str, host_value: Optional[str], fallback_name: str, driver: str = "postgresql") -> str:
    url = os.getenv(url_env_name)
    if url:
        return url
    if host_value:
        return make_database_url(host_value, driver)
    raise RuntimeError(f"{url_env_name} 또는 {fallback_name} 환경변수가 필요합니다.")


WRITABLE_URL = get_database_url(
    "WRITABLE_URL",
    getattr(settings, "DB_WRITER_HOST", None),
    "DB_HOST 또는 DB_WRITER_HOST",
)
writer_engine = create_engine(
    WRITABLE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=3,
)
WriterSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=writer_engine,
)


# 조회 API는 같은 RDS endpoint에 비동기 드라이버로 연결한다.
READONLY_URL = get_database_url(
    "READONLY_URL",
    getattr(settings, "DB_READER_HOST", None),
    "DB_HOST 또는 DB_READER_HOST",
    driver="postgresql+asyncpg",
)
reader_engine = create_async_engine(
    READONLY_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_timeout=5,
)
ReaderSessionLocal = async_sessionmaker(
    bind=reader_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


Base = declarative_base()


async def get_reader_db():
    async with ReaderSessionLocal() as db:
        yield db


def get_writer_db():
    db = WriterSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def check_db_connection():
    try:
        async with reader_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
