# [설정] 환경변수/K8s Secret 로드 — DB 접속정보, football-data API 키

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Football Match API")

    DB_WRITER_HOST: str = os.getenv("DB_WRITER_HOST", os.getenv("DB_HOST", "localhost"))
    DB_READER_HOST: str = os.getenv("DB_READER_HOST", os.getenv("DB_HOST", "localhost"))

    DB_HOST: str = os.getenv("DB_HOST", DB_READER_HOST)
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "football_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")

    FOOTBALL_DATA_API_KEY: str = os.getenv(
        "FOOTBALL_DATA_API_KEY",
        os.getenv("FOOTBALL_API_KEY", "")
    )


settings = Settings()