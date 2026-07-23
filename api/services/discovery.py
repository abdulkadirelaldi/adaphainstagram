"""Keşif akışı orkestrasyonu (SPEC §1) — job'ın çalıştırdığı çekirdek.

Places keşfi → işletme upsert → IG handle eşleme → profil çekimi (7 gün cache'li,
BD→Apify fallback) → snapshot/posts persist. Bu fonksiyon HTTP client'ları ve
bağımlılıkları **enjekte alır**: worker gerçek adaptörleri, demo fixture'lı sahte
client'ları geçer. Böylece aynı akış canlı çağrı yapmadan (kural 6) test edilir.

Maliyet disiplini (CLAUDE.md): profil çekmeden önce Redis'te `ig_handle` için taze
(< 7 gün) bir işaret varsa dış çağrı yapılmaz, hesap atlanır. Cache anahtarı burada
sarılır — çağıranın bilmesi gerekmez.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.base import (
    DiscoveryQuery,
    DiscoverySource,
    ProfileSource,
    ProfileUnavailableError,
)
from api.core import extract_ig_handle
from api.persistence import (
    persist_profile,
    place_id_to_id,
    set_ig_handle,
    upsert_businesses,
)
from api.services.profile import fetch_profile
from api.services.scoring import score_discovered

logger = logging.getLogger(__name__)

# Cache anahtar deseni: bir hesabın snapshot'ının taze olduğunu işaretler. Değer
# önemsiz ("1"); varlığı + TTL'i (7 gün) yeterli.
_CACHE_KEY = "radar:snapshot:{handle}"

# İlerleme callback'i: (işlenen, toplam). Job bunu Redis'e yazıp GET /jobs okur.
ProgressCallback = Callable[[int, int], Awaitable[None]]


class DiscoverySummary:
    """Bir keşif koşusunun sonucu."""

    def __init__(self) -> None:
        self.discovered = 0
        self.handles_matched = 0
        self.snapshots_written = 0
        self.cache_skipped = 0
        self.fallback_used = 0
        self.profile_unavailable = 0
        self.scored = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "discovered": self.discovered,
            "handles_matched": self.handles_matched,
            "snapshots_written": self.snapshots_written,
            "cache_skipped": self.cache_skipped,
            "fallback_used": self.fallback_used,
            "profile_unavailable": self.profile_unavailable,
            "scored": self.scored,
        }


def _cache_key(handle: str) -> str:
    return _CACHE_KEY.format(handle=handle)


async def run_discovery(
    query: DiscoveryQuery,
    *,
    places: DiscoverySource,
    profile_primary: ProfileSource,
    profile_fallback: ProfileSource,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Redis,
    cache_ttl_seconds: int,
    reference_now: datetime | None = None,
    on_progress: ProgressCallback | None = None,
) -> DiscoverySummary:
    """Keşif akışını uçtan uca yürütür ve özet döndürür.

    `reference_now` skorlama fazına geçer (fixture/testte `REFERENCE_NOW`); verilmezse
    üretim yolu `now(UTC)` kullanır. Saf skorlama motoru takvim gününe bağlı değil —
    referansı buradan alır.
    """
    ref_now = reference_now if reference_now is not None else datetime.now(UTC)
    summary = DiscoverySummary()

    # 1) Keşif + upsert.
    items = await places.discover(query)
    summary.discovered = len(items)
    async with session_factory() as session:
        await upsert_businesses(session, items)
        await session.commit()

    # 2) Handle eşleme (yalnız açık instagram URL'sinden; NULL kalanlar taranmaz).
    handle_by_place = {item.place_id: extract_ig_handle(item.raw) for item in items}
    matched = {pid: h for pid, h in handle_by_place.items() if h is not None}
    summary.handles_matched = len(matched)

    async with session_factory() as session:
        for place_id, handle in matched.items():
            await set_ig_handle(session, place_id, handle)
        await session.commit()
        id_by_place = await place_id_to_id(session, list(matched))

    # 3) Handle'lı her işletme için profil çek (cache'li, fallback'li) + persist.
    total = len(matched)
    processed = 0
    for place_id, handle in matched.items():
        processed += 1
        business_id = id_by_place.get(place_id)
        if business_id is None:  # pragma: no cover - upsert sonrası olmamalı
            continue

        key = _cache_key(handle)
        if await redis.exists(key):
            # Taze snapshot var — dış çağrı yok (maliyet disiplini).
            summary.cache_skipped += 1
            logger.info("cache isabeti, atlanıyor: %s", handle)
            if on_progress is not None:
                await on_progress(processed, total)
            continue

        try:
            profile = await fetch_profile(
                handle, primary=profile_primary, fallback=profile_fallback
            )
        except ProfileUnavailableError:
            # Hem BD hem Apify veri vermedi — hesap taranamadı, snapshot yok.
            summary.profile_unavailable += 1
            logger.info("profil alınamadı (BD+Apify boş): %s", handle)
            if on_progress is not None:
                await on_progress(processed, total)
            continue

        if profile.source == "apify":
            summary.fallback_used += 1

        async with session_factory() as session:
            await persist_profile(session, business_id, profile)
            await session.commit()
        summary.snapshots_written += 1

        # Snapshot yazıldı — cache'i 7 gün TTL ile işaretle.
        await redis.set(key, "1", ex=cache_ttl_seconds)

        if on_progress is not None:
            await on_progress(processed, total)

    # 4) Skorlama — snapshot yazımından sonraki SON faz (TASKS "Triyaj tetikleme
    # kararı"). Job `done` olduğunda DB'de skorlanmış işletmeler durur; panel bunları
    # gösterir. Ayrı bir "skorla" ucu yok.
    summary.scored = await score_discovered(session_factory, ref_now)

    return summary
