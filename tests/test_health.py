"""`GET /health` sözleşme testi.

Bağımlılıklar sahte: ne postgres ne redis ayakta. `CLAUDE.md` kural 6 gereği test
canlı bir servise bağlanmaz — `tests/conftest.py` içindeki ağ muhafızı zaten
dışarı çıkışı engelliyor, buradaki sahteler de yerel servise bile gitmiyor.

Yoklanan davranış `api/routes/health.py` docstring'inde söz verilen davranıştır:
sağlık ucu asla patlamaz, arıza yanıtın kendisidir.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest

from api.main import create_app
from api.schemas import ComponentStatus


class _FakeConn:
    """`SELECT 1` yoklamasını karşılar."""

    def __init__(self, *, fails: bool) -> None:
        self._fails = fails

    async def execute(self, statement: Any) -> None:
        if self._fails:
            raise ConnectionError("postgres erişilemez (sahte)")


class _FakeEngine:
    def __init__(self, *, fails: bool = False) -> None:
        self._fails = fails

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[_FakeConn]:
        if self._fails:
            raise ConnectionError("postgres erişilemez (sahte)")
        yield _FakeConn(fails=False)


class _FakeRedis:
    def __init__(self, *, fails: bool = False) -> None:
        self._fails = fails

    async def ping(self) -> bool:
        if self._fails:
            raise ConnectionError("redis erişilemez (sahte)")
        return True


class _FakeSettings:
    health_timeout_seconds: float = 3.0


def _client(*, db_fails: bool = False, redis_fails: bool = False) -> httpx.AsyncClient:
    """Uygulamayı sahte bağımlılıklarla kurar.

    `lifespan` bilinçli olarak çalıştırılmıyor: gerçek bağlantı havuzlarını açardı.
    `httpx.ASGITransport` lifespan tetiklemez, bu yüzden `app.state` elle doldurulur.
    """
    app = create_app()
    app.state.settings = _FakeSettings()
    app.state.engine = _FakeEngine(fails=db_fails)
    app.state.redis = _FakeRedis(fails=redis_fails)
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_saglikli_durumda_200_doner() -> None:
    async with _client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ComponentStatus.OK.value
    assert body["db"] == ComponentStatus.OK.value
    assert body["redis"] == ComponentStatus.OK.value


async def test_postgres_erisilemezse_503_ve_db_error() -> None:
    async with _client(db_fails=True) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == ComponentStatus.ERROR.value
    assert body["db"] == ComponentStatus.ERROR.value
    # Redis sağlamdı — bir bağımlılığın arızası diğerini kirletmemeli.
    assert body["redis"] == ComponentStatus.OK.value


async def test_redis_erisilemezse_503_ve_redis_error() -> None:
    async with _client(redis_fails=True) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == ComponentStatus.ERROR.value
    assert body["redis"] == ComponentStatus.ERROR.value
    assert body["db"] == ComponentStatus.OK.value


async def test_ikisi_de_inikken_yine_de_yanit_doner() -> None:
    """Sağlık ucu asla 500 vermez — arıza yanıtın kendisidir."""
    async with _client(db_fails=True, redis_fails=True) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["db"] == ComponentStatus.ERROR.value
    assert body["redis"] == ComponentStatus.ERROR.value


async def test_yanit_yalnizca_sozlesmedeki_alanlari_icerir() -> None:
    """CLAUDE.md kural 7: yasak metrikler hiçbir yanıta sızmamalı."""
    async with _client() as client:
        response = await client.get("/health")

    assert set(response.json()) == {"status", "db", "redis"}
