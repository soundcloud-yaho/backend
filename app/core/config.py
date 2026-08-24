import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.APP_NAME: str = os.getenv("APP_NAME", "Football Match API")

        # 모든 DB 연결은 단일 RDS endpoint를 사용한다.
        self.DB_HOST: str = os.getenv("DB_HOST", "")
        self.DB_PORT: str = os.getenv("DB_PORT", "5432")
        self.DB_NAME: str = os.getenv("DB_NAME", "")
        self.DB_USER: str = os.getenv("DB_USER", "")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

        self.FOOTBALL_DATA_API_KEY: str = os.getenv("FOOTBALL_DATA_API_KEY", "")


settings = Settings()
