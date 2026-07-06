# [설정] 환경변수/K8s Secret 로드 — DB 접속정보, football-data API 키

# config.py: 환경변수를 한 곳에서 읽어 관리
# 다른 파일에서 os.getenv를 직접 쓰지 않고 이 파일만 사용합니다
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    db_writer_host:       str = os.getenv("DB_WRITER_HOST", "localhost")
    db_reader_host:       str = os.getenv("DB_READER_HOST", "localhost")
    db_name:              str = os.getenv("DB_NAME", "worldcup")
    db_user:              str = os.getenv("DB_USER", "postgres")
    db_password:          str = os.getenv("DB_PASSWORD", "password")
    football_data_api_key: str = os.getenv("FOOTBALL_DATA_API_KEY", "")

def get_settings() -> Settings:
    return Settings()
