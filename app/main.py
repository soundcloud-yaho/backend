# [엔트리] FastAPI 앱 생성, 라우터 등록, /healthz(Liveness) /readyz(Readiness) 엔드포인트

from fastapi import FastAPI

from app.core.database import Base, writer_engine
from app.routers import matches

app = FastAPI(
    title="2026 FIFA 월드컵 API",
    description="축구 경기 데이터를 조회하는 FastAPI 서버",
    version="2.0.0",
)

# 앱 시작 시 정의된 ORM 모델 기준으로 테이블이 없으면 자동 생성
Base.metadata.create_all(bind=writer_engine)

app.include_router(matches.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}