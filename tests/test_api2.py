# [테스트] API 3종 응답 스키마 검증


# API 엔드포인트 테스트
# 실행 방법: pytest tests/
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import app.core.database as database

# main.py는 임포트되는 순간 Base.metadata.create_all()로 실제 DB 연결을 시도한다.
# 테스트에서는 실제 DB 없이 동작해야 하므로, 앱을 임포트하기 전에 create_all을 Mock 처리한다.
with patch.object(database.Base.metadata, "create_all"):
    from TEAM3.backend.app.main2 import app


def _get_mock_reader_db():
    # 실제 DB 세션 대신 Mock 세션을 주입해서 DB 연결 없이 API 로직만 테스트한다.
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    yield mock_db


app.dependency_overrides[database.get_reader_db] = _get_mock_reader_db

client = TestClient(app)


def test_health():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_matches_empty():
    response = client.get("/matches", params={"date": "2099-01-01"})
    assert response.status_code == 200
    assert response.json() == []
