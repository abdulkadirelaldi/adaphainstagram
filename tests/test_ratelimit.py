"""SEC-12 blok 2 — rate limit (api/ratelimit.py, Faz 6 sertleştirme).

Sınır aşımında `429` + `Retry-After`; sınır altında normal; sayaç sıfırlanınca tekrar
geçer; redis yoksa fail-open. Bağımlılık doğrudan sahte Request + gerçek yerel redis'le
sürülür (kural 6 — yerel redis, dış çağrı yok). Sınır monkeypatch'le kontrol edilir.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Request

import api.ratelimit as ratelimit
from api.ratelimit import rate_limited

# rate_limited("bucket") bu imzada bir bağımlılık döndürür.
Dep = Callable[[Request], Awaitable[None]]


class _Request:
    """FastAPI Request'in rate_limited'ın kullandığı yüzeyi: app.state.redis + client.host."""

    def __init__(self, redis: Any, host: str = "203.0.113.7") -> None:
        self.app = SimpleNamespace(state=SimpleNamespace(redis=redis))
        self.client = SimpleNamespace(host=host)


async def _hit(dep: Dep, request: _Request) -> None:
    """Bağımlılığı sahte Request'le çağırır (tip köprüsü tek noktada)."""
    await dep(cast(Request, request))


@pytest.fixture
def limit_3(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dakikalık sınırı 3'e sabitler (get_settings'i monkeypatch — DB/env gerekmez)."""
    monkeypatch.setattr(ratelimit, "get_settings", lambda: SimpleNamespace(rate_limit_per_minute=3))


async def test_sinir_altinda_gecer_asimda_429(test_redis: Any, limit_3: None) -> None:
    dep = rate_limited("audit")
    request = _Request(test_redis)
    # İlk 3 istek geçer.
    for _ in range(3):
        await _hit(dep, request)
    # 4. istek 429 + Retry-After.
    with pytest.raises(HTTPException) as exc:
        await _hit(dep, request)
    assert exc.value.status_code == 429
    headers = exc.value.headers or {}
    assert "Retry-After" in headers
    retry = int(headers["Retry-After"])
    assert 0 < retry <= 60


async def test_bucket_bagimsiz(test_redis: Any, limit_3: None) -> None:
    """Farklı bucket'lar ayrı sayılır — keşif sınırı denetim sınırını tüketmez."""
    discovery = rate_limited("discovery")
    audit = rate_limited("audit")
    request = _Request(test_redis)
    for _ in range(3):
        await _hit(discovery, request)
    # discovery doldu ama audit hâlâ boş.
    await _hit(audit, request)  # patlamamalı


async def test_sayac_sifirlaninca_tekrar_geciyor(test_redis: Any, limit_3: None) -> None:
    """Pencere sıfırlanınca (anahtar düşünce) istek tekrar geçer."""
    dep = rate_limited("audit")
    request = _Request(test_redis, host="198.51.100.9")
    for _ in range(3):
        await _hit(dep, request)
    with pytest.raises(HTTPException):
        await _hit(dep, request)
    # Pencere sonu: sayaç anahtarını düşür (TTL dolmuş gibi).
    async for key in test_redis.scan_iter("radar:ratelimit:*"):
        await test_redis.delete(key)
    await _hit(dep, request)  # yeniden geçer


async def test_farkli_istemci_ayri_sayilir(test_redis: Any, limit_3: None) -> None:
    """Sınır istemci-IP başına — bir istemci diğerinin kotasını tüketmez."""
    dep = rate_limited("audit")
    a = _Request(test_redis, host="192.0.2.1")
    b = _Request(test_redis, host="192.0.2.2")
    for _ in range(3):
        await _hit(dep, a)
    with pytest.raises(HTTPException):
        await _hit(dep, a)
    # Farklı IP hâlâ geçer.
    await _hit(dep, b)


async def test_redis_yoksa_fail_open(limit_3: None) -> None:
    """Redis yoksa (hermetik test) sınır UYGULANMAZ — uç normal çalışır."""
    dep = rate_limited("audit")
    request = _Request(None)  # app.state.redis None
    for _ in range(10):
        await _hit(dep, request)  # hiçbir zaman 429 değil
