# [엔트리] FastAPI 앱 생성, 라우터 등록, /healthz(Liveness) /readyz(Readiness) 엔드포인트

# FastAPI 애플리케이션 진입점
from fastapi import FastAPI

from app.core.database import Base, writer_engine
from TEAM3.backend.app.routers import matches2

app = FastAPI(title="2026 FIFA 월드컵 API", version="2.0.0")

# 앱 시작 시 정의된 ORM 모델 기준으로 테이블이 없으면 자동 생성
Base.metadata.create_all(bind=writer_engine)

app.include_router(matches2.router)


@app.get("/healthz")
def healthz():
    # Liveness Probe: 프로세스가 살아있는지 확인. 실패(응답 없음/에러)가 반복되면
    # Kubernetes가 컨테이너가 죽었다고 판단하고 파드를 재시작한다.
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # Readiness Probe: 트래픽을 받을 준비가 되었는지 확인. 실패하면
    # Kubernetes가 해당 파드를 서비스 대상(로드밸런서)에서 일시적으로 제외한다.
    return {"status": "ready"}
