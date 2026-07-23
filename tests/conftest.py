"""Radar test paketi — ortak fixture'lar ve ağ muhafızı.

`CLAUDE.md` kural 6: hiçbir test canlı Instagram, Apify veya Places çağrısı yapmaz.
Bu kural burada yorum olarak değil, çalışan bir muhafız olarak duruyor: dışarı giden
her soket bağlantısı testi düşürür. Bir testin dış çağrı yapmadığını iddia etmek
yerine kanıtlıyoruz.
"""

from __future__ import annotations

import json
import os
import socket
from collections.abc import AsyncIterator, Buffer, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# `socket.socket.connect` ve arkadaşlarının kabul ettiği adres tipi. Muhafız
# fonksiyonları birebir bu imzayı taşımalı, yoksa mypy strict atamayı reddeder.
type SocketAddress = tuple[Any, ...] | str | Buffer

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Yerel adresler serbest: CI'daki postgres/redis servis konteynerleri ve
# httpx.ASGITransport bunları kullanır. Dış dünya kapalı.
_ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})  # noqa: S104


class NetworkCallBlockedError(AssertionError):
    """Bir test dış ağa çıkmaya çalıştı — CLAUDE.md kural 6 ihlali."""


def _host_of(address: Any) -> str | None:
    """Soket adresinden host'u çıkarır; AF_UNIX gibi tuple olmayanlar için None."""
    if isinstance(address, tuple) and address:
        return str(address[0])
    return None


def _assert_local(address: Any) -> None:
    host = _host_of(address)
    if host is not None and host not in _ALLOWED_HOSTS:
        raise NetworkCallBlockedError(
            f"Test dış ağa çıkmaya çalıştı: {address!r}. "
            "CLAUDE.md kural 6 — testler tests/fixtures/ altındaki sabit JSON'ları "
            "kullanır, canlı Instagram/Apify/Places çağrısı yapmaz. "
            "Gerçek bir HTTP istemcisi gerekiyorsa mock'la veya respx kullan."
        )


@pytest.fixture(autouse=True, scope="session")
def _block_outbound_network() -> Iterator[None]:
    """Tüm test oturumu boyunca dışarı giden soket bağlantılarını engeller."""
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_create_connection = socket.create_connection

    def guarded_connect(self: socket.socket, address: SocketAddress) -> None:
        _assert_local(address)
        real_connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: SocketAddress) -> int:
        _assert_local(address)
        return real_connect_ex(self, address)

    def guarded_create_connection(address: Any, *args: Any, **kwargs: Any) -> socket.socket:
        _assert_local(address)
        return real_create_connection(address, *args, **kwargs)

    socket.socket.connect = guarded_connect  # type: ignore[method-assign,assignment]
    socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign,assignment]
    socket.create_connection = guarded_create_connection
    try:
        yield
    finally:
        socket.socket.connect = real_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = real_connect_ex  # type: ignore[method-assign]
        socket.create_connection = real_create_connection


@pytest.fixture
def fixtures_dir() -> Path:
    """`tests/fixtures/` dizininin yolu."""
    return FIXTURES_DIR


@pytest.fixture
def load_fixture() -> Any:
    """İsimle sabit JSON fixture yükler: `load_fixture("ig_profile_active")`."""

    def _load(name: str) -> Any:
        path = FIXTURES_DIR / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Fixture bulunamadı: {path}. Fixture'lar tests/fixtures/ altında "
                "sabit JSON olarak durur."
            )
        return json.loads(path.read_text(encoding="utf-8"))

    return _load


# --- Veritabanı + Redis fixture'ları (SEC-5 entegrasyon testleri) --------------
#
# Yalnızca YEREL postgres/redis'e bağlanır — kural 6 dış Instagram/Apify/Places
# çağrısını yasaklar, yerel altyapıyı değil (ağ muhafızı localhost'a izin verir).
# CI'da servis konteynerleri (postgres 16 + redis 7) ve DATABASE_URL/REDIS_URL env
# ile koşar; yerelde varsayılan URL'lere düşer. Bağlanılamazsa test SKIP edilir —
# DB'siz makinede süit yeşil kalır, ama CI'da ve DB'li makinede gerçekten koşar.


def _test_db_url() -> str:
    url = os.environ.get("RADAR_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if url:
        return url
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "postgres"
    return f"postgresql+asyncpg://{user}@localhost:5432/radar_sec5_test"


def _test_redis_url() -> str:
    return (
        os.environ.get("RADAR_TEST_REDIS_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/15"
    )


@pytest_asyncio.fixture
async def db_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Temiz şemalı test DB'sine bağlı bir session fabrikası verir.

    Şema `Base.metadata.create_all` ile kurulur (alembic değil — testin ihtiyacı
    tablolar; migration ayrı doğrulanır). Her testten önce `TRUNCATE ... CASCADE`
    ile temizlenir. Bağlanılamazsa test atlanır.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from api.models.base import Base

    url = _test_db_url()
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("TRUNCATE businesses CASCADE"))
    except Exception as exc:
        # asyncpg auth/bağlantı hataları SQLAlchemyError sarmalına girmeyebilir
        # (InvalidAuthorizationSpecificationError vb.); erişilemezlik = testi atla.
        await engine.dispose()
        pytest.skip(f"Test veritabanına bağlanılamadı ({_test_db_url()}): {exc!r}")

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def test_redis() -> AsyncIterator[Redis]:
    """Temiz `radar:*` anahtar uzayı olan bir Redis client'ı verir.

    Yalnızca `radar:*` anahtarları silinir (flushdb değil) — paylaşılan bir redis'te
    başka veriyi ezmemek için. Bağlanılamazsa test atlanır.
    """
    from redis.asyncio import Redis

    redis: Redis = Redis.from_url(_test_redis_url())
    try:
        await redis.ping()
    except Exception as exc:
        await redis.aclose()
        pytest.skip(f"Test redis'e bağlanılamadı ({_test_redis_url()}): {exc!r}")

    async def _clear() -> None:
        async for key in redis.scan_iter("radar:*"):
            await redis.delete(key)

    await _clear()
    try:
        yield redis
    finally:
        await _clear()
        await redis.aclose()
