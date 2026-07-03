# [엔트리] FastAPI 앱 생성, 라우터 등록, /healthz(Liveness) /readyz(Readiness) 엔드포인트

from fastapi import FastAPI
from app.routers import matches
from app.core.config import settings # config.py 불러오기

app = FastAPI(
    title="Football Match API",
    description="축구 경기 데이터를 조회하는 FastAPI 서버",
    version="1.0.0"
)

app.include_router(matches.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }

@app.get("/healthz")
def healthz():
    return {
        "status": "ok"
    }


@app.get("/readyz")
def readyz():
    db_ok = check_db_connection()

    if db_ok:
        return {"status": "ready"}

    return {"status": "not ready"}