import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from testee_common.http import health


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(health.health_router(None))

    return TestClient(app)


def database(monkeypatch, up: bool):
    async def ping(engine):
        if not up:
            raise ConnectionError("database is down")

    monkeypatch.setattr(health, "ping", ping)


def test_a_service_that_answers_is_healthy(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_once_the_database_answers(client, monkeypatch):
    database(monkeypatch, up=True)

    assert client.get("/ready").json() == {"status": "ready"}


def test_not_ready_while_the_database_is_down(client, monkeypatch):
    database(monkeypatch, up=False)

    assert client.get("/ready").status_code == 503
