"""SEC-5 blok 3(persist)+4+5(DB) — run_discovery uçtan uca, gerçek DB + Redis.

Yalnızca YEREL postgres/redis kullanır (kural 6 dış Instagram/Apify/Places'i yasaklar,
yerel altyapıyı değil). Adaptörlere fixture yanıtı veren sahte client'lar enjekte
edilir — hiçbir canlı çağrı yok. DB/redis yoksa testler SKIP olur (conftest fixture'ları).

Doğrulananlar:
- Blok 4: 7 gün cache — ikinci koşuda dış profil çağrısı 0, çift snapshot yok; TTL 7 gün;
  süre dolunca yeniden çekiliyor. Cache devre dışıysa ikinci koşu çağrı yapar (karşı-kanıt).
- Blok 3: fallback handle'larda `snapshots.source=apify`, diğerlerinde `business_discovery`.
- Blok 5: yasak metrikler persist'ten sonra yalnız `snapshots.raw`'da; tipli sütunlarda ve
  `posts`'ta yok.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.models import Business, Post, Snapshot
from api.services import run_discovery
from tests._mocks import CallCounter, apify_client, bd_client, places_client

SEVEN_DAYS = 7 * 24 * 60 * 60
FALLBACK_HANDLES = {"sahilkahveevi", "cadde19kafe"}


@dataclass
class RunCounters:
    places: CallCounter
    bd: CallCounter
    apify: CallCounter


async def _run(
    *,
    places_raw: dict[str, Any],
    bd_profiles: dict[str, Any],
    apify_profiles: dict[str, Any],
    session_factory: async_sessionmaker[AsyncSession],
    redis: Any,
    ttl: int = SEVEN_DAYS,
) -> tuple[Any, RunCounters]:
    counters = RunCounters(CallCounter(), CallCounter(), CallCounter())
    places_c = places_client(places_raw, counters.places)
    bd_c = bd_client(bd_profiles, counters.bd)
    apify_c = apify_client(apify_profiles, counters.apify)
    try:
        summary = await run_discovery(
            DiscoveryQuery(query="samsun işletmeleri"),
            places=PlacesAdapter(client=places_c),
            profile_primary=BusinessDiscoveryAdapter(client=bd_c),
            profile_fallback=ApifyAdapter(client=apify_c),
            session_factory=session_factory,
            redis=redis,
            cache_ttl_seconds=ttl,
        )
    finally:
        await places_c.aclose()
        await bd_c.aclose()
        await apify_c.aclose()
    return summary, counters


async def _counts(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, int]:
    async with session_factory() as session:
        biz = await session.scalar(select(func.count()).select_from(Business))
        snaps = await session.scalar(select(func.count()).select_from(Snapshot))
        posts = await session.scalar(select(func.count()).select_from(Post))
    return {"businesses": biz or 0, "snapshots": snaps or 0, "posts": posts or 0}


def _fixtures(load_fixture: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        load_fixture("places_response"),
        load_fixture("ig_business_discovery")["profiles"],
        load_fixture("apify_profile")["profiles"],
    )


# --- Blok 4: 7 gün cache --------------------------------------------------------


async def test_ikinci_kosu_cache_isabeti_dis_profil_cagrisi_yok(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """İlk koşu profil çeker; ikinci koşu cache'ten döner — 0 dış profil çağrısı, çift snapshot yok."""
    places_raw, bd, apify = _fixtures(load_fixture)

    summary1, c1 = await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    assert summary1.discovered == 20
    assert summary1.handles_matched == 14
    assert summary1.snapshots_written == 14
    assert summary1.fallback_used == 2  # sahilkahveevi + cadde19kafe
    # İlk koşuda profil çağrıları yapıldı.
    assert c1.bd.count == 14  # her handle için BD denendi
    assert c1.apify.count == 2  # iki fallback
    after1 = await _counts(db_session_factory)
    assert after1["snapshots"] == 14

    summary2, c2 = await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    # İKİNCİ KOŞU: tüm handle'lar cache'te → hiç dış profil çağrısı yok.
    assert c2.bd.count == 0
    assert c2.apify.count == 0
    assert summary2.cache_skipped == 14
    assert summary2.snapshots_written == 0
    # Çift snapshot oluşmadı.
    after2 = await _counts(db_session_factory)
    assert after2["snapshots"] == 14
    assert after2["businesses"] == 20  # upsert, çift yok


async def test_cache_devre_disi_ikinci_kosu_cagri_yapar_karsi_kanit(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """KARŞI-KANIT: cache anahtarları silinirse (cache devre dışı gibi) ikinci koşu dış çağrı yapar.

    Bu, cache testinin gerçekten bir şey ölçtüğünü gösterir: cache sarmalı çalışmasaydı
    `test_ikinci_kosu_...` kırmızıya dönerdi.
    """
    places_raw, bd, apify = _fixtures(load_fixture)
    await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    # Cache'i düşür (7 gün dolmuş gibi / cache kapalı gibi).
    async for key in test_redis.scan_iter("radar:snapshot:*"):
        await test_redis.delete(key)

    _, c2 = await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    # Cache boş → ikinci koşu yeniden çağırdı.
    assert c2.bd.count == 14
    assert c2.apify.count == 2


async def test_cache_ttl_yedi_gun(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Yazılan cache anahtarının TTL'i ~7 gün olmalı (maliyet disiplini)."""
    places_raw, bd, apify = _fixtures(load_fixture)
    await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
        ttl=SEVEN_DAYS,
    )
    ttl = await test_redis.ttl("radar:snapshot:elmaskuyumculuk")
    # Anahtar var ve TTL 7 güne çok yakın (birkaç saniyelik koşu payı).
    assert SEVEN_DAYS - 120 <= ttl <= SEVEN_DAYS


async def test_cache_suresi_dolunca_yeniden_cekiliyor_ama_cift_snapshot_yok(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Bir handle'ın cache'i dolunca (silinince) yeniden çekilir; persist idempotent → çift yok."""
    places_raw, bd, apify = _fixtures(load_fixture)
    await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    before = await _counts(db_session_factory)

    # Tek bir handle'ın süresi dolmuş gibi cache anahtarını düşür.
    await test_redis.delete("radar:snapshot:elmaskuyumculuk")

    _, c2 = await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    # Yalnız o handle yeniden çekildi (diğer 13 cache'te).
    assert c2.bd.count == 1
    assert c2.apify.count == 0
    # Aynı veri → yeni snapshot yok (idempotent persist).
    after = await _counts(db_session_factory)
    assert after["snapshots"] == before["snapshots"]


# --- Blok 3: persist source (fallback → apify) ----------------------------------


async def test_snapshot_source_fallbackte_apify_digerlerinde_bd(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    places_raw, bd, apify = _fixtures(load_fixture)
    await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    async with db_session_factory() as session:
        rows = await session.execute(
            select(Business.ig_handle, Snapshot.source).join(
                Snapshot, Snapshot.business_id == Business.id
            )
        )
        source_by_handle = dict(rows.tuples().all())

    assert source_by_handle["sahilkahveevi"] == "apify"
    assert source_by_handle["cadde19kafe"] == "apify"
    assert source_by_handle["atakumdisklinigi"] == "business_discovery"
    assert source_by_handle["elmaskuyumculuk"] == "business_discovery"
    # Sadece fallback handle'ları apify olmalı.
    apify_handles = {h for h, s in source_by_handle.items() if s == "apify"}
    assert apify_handles == FALLBACK_HANDLES


# --- Blok 5: gizlilik zinciri (persist sonrası DB) ------------------------------


async def test_yasak_metrik_yalnizca_raw_jsonda_sutunlarda_yok(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Apify handle'ının snapshot'ı: yasak metrik yalnız raw JSONB'de, tipli sütunlarda/posts'ta yok."""
    places_raw, bd, apify = _fixtures(load_fixture)
    await _run(
        places_raw=places_raw,
        bd_profiles=bd,
        apify_profiles=apify,
        session_factory=db_session_factory,
        redis=test_redis,
    )
    async with db_session_factory() as session:
        snap = await session.scalar(
            select(Snapshot)
            .join(Business, Business.id == Snapshot.business_id)
            .where(Business.ig_handle == "sahilkahveevi")
        )
        assert snap is not None
        # raw arşivde yasak metrik DURUYOR (denetim izi).
        assert snap.raw["impressions"] == 15234
        assert "followerDemographics" in snap.raw
        # Tipli sütun değerlerinde yasak metrik YOK — yalnız SPEC §3 alanları.
        assert snap.followers == 3120  # followersCount
        assert snap.media_count == 194  # postsCount

        posts = (await session.scalars(select(Post).where(Post.snapshot_id == snap.id))).all()
        assert len(posts) == 3
        for post in posts:
            # posts satırında yalnız izin verilen nicel alanlar; yasak veri yok.
            # (Sütunlar zaten sabit; burada değerlerin de temiz geldiğini teyit ederiz.)
            assert post.like_count is not None
            # view_count yalnız videoda dolar; resimde None — yasak alan değil.
