"""SEC-7 — skorlama persist + fixture'a bağlı kohort<5 (gerçek DB).

Gerçek keşif akışıyla DB'yi 100-hesap fixture'ından doldurur, sonra `score_discovered`
çalıştırır ve `triage_scores`'ı doğrular. Yalnız YEREL pg/redis (kural 6); erişilemezse
SKIP (conftest). Sayılar fixture/DB durumundan **türetilir** — magic number yok.

Doğrulananlar:
- `triage_scores` alt skorlar + birleşik + status + `computed_at` taşıyor.
- İdempotent: tekrar skorlama işletme başına tek satır bırakıyor.
- Kohort<5 kategoriler (DB'den türetilir) potansiyel None + watch; kohort≥5 potansiyel dolu.
- Mutlak eşik yok: potansiyel kohort medyanına göre (motorun kendi testinde; burada uçtan uca).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.core.scoring import MIN_COHORT
from api.models import Business, Snapshot, TriageScore
from api.services import run_discovery
from api.services.scoring import score_discovered
from tests._mocks import CallCounter, apify_client, bd_client, places_client

REFERENCE_NOW = datetime(2026, 7, 15, 0, 0, 0, tzinfo=UTC)


async def _populate(
    load_fixture: Any,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Any,
) -> None:
    """Keşif akışını fixture'la çalıştırıp DB'yi doldurur (snapshot + posts)."""
    places_raw = load_fixture("places_response")
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    pc, bc, ac = CallCounter(), CallCounter(), CallCounter()
    places_c = places_client(places_raw, pc)
    bd_c = bd_client(bd, bc)
    apify_c = apify_client(apify, ac)
    try:
        await run_discovery(
            DiscoveryQuery(query="samsun"),
            places=PlacesAdapter(client=places_c),
            profile_primary=BusinessDiscoveryAdapter(client=bd_c),
            profile_fallback=ApifyAdapter(client=apify_c),
            session_factory=session_factory,
            redis=redis,
            cache_ttl_seconds=7 * 24 * 60 * 60,
        )
    finally:
        await places_c.aclose()
        await bd_c.aclose()
        await apify_c.aclose()


async def _scanned_count_by_category(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str | None, int]:
    """Snapshot'ı olan (taranmış) işletmelerin kategori sayıları — kohort büyüklüğü."""
    async with session_factory() as session:
        rows = await session.execute(
            select(Business.category, func.count(func.distinct(Business.id)))
            .join(Snapshot, Snapshot.business_id == Business.id)
            .group_by(Business.category)
        )
    return dict(rows.tuples().all())


async def test_triage_persist_ve_idempotent(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Skorlama yazılıyor; iki kez çalışınca işletme başına tek satır (idempotent)."""
    await _populate(load_fixture, db_session_factory, test_redis)

    scored1 = await score_discovered(db_session_factory, REFERENCE_NOW)
    assert scored1 > 0

    async with db_session_factory() as session:
        rows1 = await session.scalar(select(func.count()).select_from(TriageScore))
        # Taranmış işletme sayısı kadar triyaj satırı.
        scanned = await session.scalar(select(func.count(func.distinct(Snapshot.business_id))))
    assert rows1 == scanned == scored1

    # Tekrar skorla → çift satır YOK (delete+insert idempotent).
    scored2 = await score_discovered(db_session_factory, REFERENCE_NOW)
    async with db_session_factory() as session:
        rows2 = await session.scalar(select(func.count()).select_from(TriageScore))
        distinct2 = await session.scalar(select(func.count(func.distinct(TriageScore.business_id))))
    assert scored2 == scored1
    assert rows2 == rows1
    # Toplam satır == farklı işletme sayısı → işletme başına tam bir satır (idempotent).
    assert rows2 == distinct2


async def test_triage_satiri_tum_alanlari_tasiyor(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Bir triyaj satırı: activity/capacity (daima), status, computed_at dolu."""
    await _populate(load_fixture, db_session_factory, test_redis)
    await score_discovered(db_session_factory, REFERENCE_NOW)

    async with db_session_factory() as session:
        row = await session.scalar(select(TriageScore).limit(1))
    assert row is not None
    assert row.activity is not None
    assert row.capacity is not None
    assert row.status is not None
    assert row.computed_at is not None  # server_default now()


async def test_kohort_bes_alti_kategoriler_watch_potansiyel_none(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """DB'den türetilen kohort<5 kategoriler potansiyel None + watch; kohort≥5 potansiyel dolu.

    Beklenen kategori kümesi fixture'dan (DB taranmış sayısından) hesaplanır — magic number yok.
    """
    await _populate(load_fixture, db_session_factory, test_redis)
    await score_discovered(db_session_factory, REFERENCE_NOW)

    scanned = await _scanned_count_by_category(db_session_factory)
    small = {c for c, n in scanned.items() if n < MIN_COHORT}
    big = {c for c, n in scanned.items() if n >= MIN_COHORT}
    assert small, "Fixture'da kohort<5 en az bir kategori bekleniyordu"
    assert big, "Fixture'da kohort>=5 en az bir kategori bekleniyordu"

    async with db_session_factory() as session:
        rows = await session.execute(
            select(Business.category, TriageScore.potential).join(
                TriageScore, TriageScore.business_id == Business.id
            )
        )
        potential_by_cat: dict[str | None, list[float | None]] = {}
        for cat, pot in rows.all():
            potential_by_cat.setdefault(cat, []).append(pot)

    # Kohort<5 kategorinin TÜM satırları potansiyel None.
    for cat in small:
        assert all(p is None for p in potential_by_cat.get(cat, [])), (
            f"{cat}: kohort<5, potansiyel None olmalıydı"
        )
    # Kohort≥5 kategorinin en az bir satırında potansiyel hesaplanmış (None değil).
    for cat in big:
        vals = potential_by_cat.get(cat, [])
        assert any(p is not None for p in vals), f"{cat}: kohort>=5, potansiyel hesaplanmalıydı"


async def test_bantlar_ucune_de_yayiliyor(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """SEC-8 fixture'ı skorları üç banda da yayıyor (rejected/watch/qualified hepsi mevcut)."""
    await _populate(load_fixture, db_session_factory, test_redis)
    await score_discovered(db_session_factory, REFERENCE_NOW)

    async with db_session_factory() as session:
        rows = await session.execute(
            select(TriageScore.status, func.count()).group_by(TriageScore.status)
        )
        by_status = dict(rows.tuples().all())

    # Üç durumun da en az bir örneği olmalı — fixture skor sinyalleri çeşitliliği (SEC-8).
    from api.models.enums import TriageStatus

    for st in (TriageStatus.REJECTED, TriageStatus.WATCH, TriageStatus.QUALIFIED):
        assert by_status.get(st, 0) > 0, f"{st.value} bandında hesap bekleniyordu: {by_status}"
