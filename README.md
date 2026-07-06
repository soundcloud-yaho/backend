# worldcup-backend

Sound_Cloud 프로젝트의 백엔드 레포. FastAPI REST API 서버와 외부 데이터 동기화 잡을 포함한다.

이 레포는 **이미지를 만들어 ECR에 저장하는 것까지만** 책임진다. 실제 배포(클러스터에 반영)는 `worldcup-infra`의 `k8s/manifests/backend/`에서 이미지 태그를 갱신하는 커밋으로 이루어진다.

---

## 아키텍처 상 위치

```
ALB → FastAPI Pod (Spot Worker 노드그룹, target-type: ip)
         ├─ GET /matches, ?date=, ?team=  → Aurora Reader (읽기 전용)
         └─ (별도 CronJob) 동기화 잡      → football-data.org → Aurora Writer (UPSERT)
```

- FastAPI Pod는 **읽기만** 담당한다. 사용자 트래픽이 아무리 몰려도 Aurora 쓰기 경로에는 영향을 주지 않는다.
- 동기화 CronJob은 사용자 요청 경로와 완전히 분리된 별도 잡이다. 외부 API가 장애가 나도 서비스는 마지막 동기화 데이터로 계속 응답한다.
- Pod는 stateless — Spot 회수로 노드가 바뀌어도 잃는 상태가 없다.

---

## 모듈 구성

| 경로 | 역할 |
|---|---|
| `app/main.py` | FastAPI 앱 엔트리포인트, 라우터 등록, `/healthz`(Liveness) · `/readyz`(Readiness) |
| `app/routers/matches.py` | REST API 3종 — `GET /matches`, `?date=`, `?team=` |
| `app/core/config.py` | 환경변수 · K8s Secret 로드 (DB 접속정보, football-data API 키) |
| `app/core/database.py` | SQLAlchemy 커넥션 풀 — **Writer/Reader 엔드포인트 분리**, 풀 사이즈 상한으로 Aurora 커넥션 초과 방지 |
| `app/models/schemas.py` | `matches` / `teams` 테이블 모델 + API 응답 JSON 스키마 (프론트와 합의된 계약, 임의 변경 금지) |
| `sync/sync_matches.py` | football-data.org 1시간 주기 폴링 → Aurora Writer UPSERT. 무료 티어 한도(분당 10회) 준수 |
| `tests/test_api.py` | API 응답 스키마 검증 |

---

## 배포 흐름

1. `master` 브랜치에 push
2. CI(`.github/workflows/build-push.yaml`)가 Docker 이미지 빌드 → ECR에 `backend:<git-sha-7자리>` 태그로 push
3. **자동 배포는 별도작업 필요**
4. 실제 배포하려면 `worldcup-infra` 레포의 `k8s/manifests/backend/deployment.yaml`에서 이미지 태그를 방금 만든 SHA로 수정해 커밋 → ArgoCD가 감지해 롤아웃

---

## 환경변수 / Secret

로컬 개발 시 `.env` 파일 사용, 클러스터에서는 K8s Secret으로 주입된다. Secret 자체는 git에 절대 커밋하지 않는다 (`worldcup-infra/k8s/manifests/backend/SECRETS.md`에 필요한 키 이름만 문서화).

| 변수 | 용도 |
|---|---|
| `DB_WRITER_HOST` / `DB_READER_HOST` | Aurora 엔드포인트 (분리) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | DB 접속 정보 |
| `FOOTBALL_DATA_API_KEY` | football-data.org API 키 |

---

## 로컬 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```


```bash
docker test
# backend terminal에서 
# docker network 생성
docker network create football-net

# postgres container 생성
docker run -d \
  --name football-postgres \
  --network football-net \
  -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=football_db \
  postgres:15

# image build
docker build -t football-backend:local .

# backend container 생성
docker run -d \
  --name football-backend \
  --network football-net \
  -p 8000:8000 \
  -e APP_NAME="Football Match API" \
  -e DB_HOST=football-postgres \
  -e DB_PORT=5432 \
  -e DB_NAME=football_db \
  -e DB_USER=postgres \
  -e DB_PASSWORD=password \
  -e FOOTBALL_API_KEY="849ede26d4d84d96aecb7757457a042e" \
  football-backend:local

# create table
docker exec -it football-backend python -m scripts.create_tables

# 경기 데이터 동기화
docker exec -it football-backend python -m sync.sync_matches

# API 확인하기

curl http://localhost:8000/health
curl http://localhost:8000/matches
curl "http://localhost:8000/matches?team=Switzerland"

```

