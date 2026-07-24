# [엔트리] FastAPI 앱 생성, 라우터 등록, 헬스체크, 지연시간 수집

import logging
import time

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, writer_engine
from app.routers import matches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_latency")

app = FastAPI(
    title="2026 FIFA 월드컵 API",
    description="축구 경기 데이터를 조회하는 FastAPI 서버",
    version="2.0.0",
)

instrumentator = Instrumentator(
    should_instrument_requests_inprogress=True,
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app)  # /metrics 엔드포인트 노출

# 프론트엔드 주소
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://rubao.store",
    "https://www.rubao.store",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Response-Time-ms"] = str(duration_ms)
    return response


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
