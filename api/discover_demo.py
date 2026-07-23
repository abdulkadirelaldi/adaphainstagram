"""Tek komutlu keşif demosu — `python -m api.discover_demo`.

SEC-6 fixture setiyle (~20 işletme) keşif akışını uçtan uca çalıştırır: **canlı çağrı
yok** (kural 6), adaptörlere fixture yanıtı veren sahte HTTP client'ları enjekte edilir.
Gerçek postgres + redis kullanır (worker'ı atlar; aynı `run_discovery` çekirdeğini
doğrudan çağırır).

Akışı **iki kez** koşar: ikinci koşuda cache'li hesaplar için dış çağrı yapılmadığını
(client çağrı sayacı) ve çift snapshot oluşmadığını gösterir (maliyet disiplini).

Gerekli ortam: `DATABASE_URL`, `REDIS_URL`. Migration uygulanmış olmalı.
"""

import asyncio
import sys

from sqlalchemy import func, select, text

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.cache import create_redis
from api.config import get_settings
from api.db import create_engine, create_session_factory
from api.fixture_mode import (
    load_fixture,
    make_apify_client,
    make_bd_client,
    make_places_client,
)
from api.models import Business, Post, Snapshot
from api.services import run_discovery


def _emit(message: str) -> None:
    """Demo çıktısı — CLI raporu stdout'a. (logging değil; bu bir komut çıktısı.)"""
    sys.stdout.write(message + "\n")


class _CallCounter:
    """Sahte client çağrılarını sayar — cache kanıtı için. `on_call` olarak geçilir."""

    def __init__(self) -> None:
        self.count = 0

    def reset(self) -> None:
        self.count = 0

    def __call__(self) -> None:
        self.count += 1


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    redis = create_redis(settings)

    places_raw = load_fixture("places_response.json")
    bd_profiles = load_fixture("ig_business_discovery.json")["profiles"]
    apify_profiles = load_fixture("apify_profile.json")["profiles"]

    places_calls = _CallCounter()
    bd_calls = _CallCounter()
    apify_calls = _CallCounter()

    # Temiz demo durumu: tabloları ve cache anahtarlarını sıfırla (tekrarlanabilirlik).
    async with session_factory() as session:
        await session.execute(text("TRUNCATE businesses CASCADE"))
        await session.commit()
    async for key in redis.scan_iter("radar:snapshot:*"):
        await redis.delete(key)

    async def run_once(label: str) -> None:
        places_calls.reset()
        bd_calls.reset()
        apify_calls.reset()
        places_c = make_places_client(places_raw, places_calls)
        bd_c = make_bd_client(bd_profiles, bd_calls)
        apify_c = make_apify_client(apify_profiles, apify_calls)
        try:
            summary = await run_discovery(
                DiscoveryQuery(query="samsun işletmeleri"),
                places=PlacesAdapter(client=places_c),
                profile_primary=BusinessDiscoveryAdapter(client=bd_c),
                profile_fallback=ApifyAdapter(client=apify_c),
                session_factory=session_factory,
                redis=redis,
                cache_ttl_seconds=settings.snapshot_cache_ttl_seconds,
            )
        finally:
            await places_c.aclose()
            await bd_c.aclose()
            await apify_c.aclose()

        async with session_factory() as session:
            biz = await session.scalar(select(func.count()).select_from(Business))
            with_handle = await session.scalar(
                select(func.count()).where(Business.ig_handle.is_not(None))
            )
            snaps = await session.scalar(select(func.count()).select_from(Snapshot))
            posts = await session.scalar(select(func.count()).select_from(Post))
            apify_snaps = await session.scalar(
                select(func.count()).where(Snapshot.source == "apify")
            )

        _emit(f"\n=== {label} ===")
        _emit(f"  özet: {summary.as_dict()}")
        _emit(
            f"  DB: businesses={biz}, ig_handle dolu={with_handle}, "
            f"snapshots={snaps} (apify={apify_snaps}), posts={posts}"
        )
        _emit(
            f"  dış çağrı: places={places_calls.count}, "
            f"business_discovery={bd_calls.count}, apify={apify_calls.count}"
        )

    await run_once("1. KOŞU (cache boş)")
    await run_once("2. KOŞU (cache dolu — dış profil çağrısı olmamalı)")

    await redis.aclose()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
