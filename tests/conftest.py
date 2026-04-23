from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).with_name("test_app.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

from app.main import app  # noqa: E402
from app.database import engine  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def auth_token(client: TestClient) -> str:
    import uuid

    response = client.post(
        "/user/init",
        json={
            "username": f"tester_{uuid.uuid4().hex[:8]}",
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["token"]
