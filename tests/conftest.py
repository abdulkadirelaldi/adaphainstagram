"""Radar test paketi — ortak fixture'lar ve ağ muhafızı.

`CLAUDE.md` kural 6: hiçbir test canlı Instagram, Apify veya Places çağrısı yapmaz.
Bu kural burada yorum olarak değil, çalışan bir muhafız olarak duruyor: dışarı giden
her soket bağlantısı testi düşürür. Bir testin dış çağrı yapmadığını iddia etmek
yerine kanıtlıyoruz.
"""

from __future__ import annotations

import json
import socket
from collections.abc import Buffer, Iterator
from pathlib import Path
from typing import Any

import pytest

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
