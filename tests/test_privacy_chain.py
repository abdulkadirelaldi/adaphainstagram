"""SEC-5 blok 5 — gizlilik zinciri (DB'siz uçlar).

CLAUDE.md kural 7: erişim/gösterim/kaydetme/profil ziyareti/demografi sistemde yok.
Bu dosya zincirin DB gerektirmeyen uçlarını bağlar: ORM sütunları, HTTP şemaları ve
`/businesses` yanıtı. DB'ye yazılan snapshot/posts sütunları `test_discovery_integration`
içinde (gerçek persist sonrası) doğrulanır. İkisi birlikte ham→normalize→persist→sütun→
API zincirini kapatır.
"""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

from api.main import create_app
from api.models import Post, Snapshot
from api.schemas import Business, BusinessList, JobResult, JobStatus, Stats

# Kural 7'nin yasakladığı alanların adları (İng + olası varyant). Hiçbiri sütun,
# şema alanı veya API anahtarı olarak görünmemeli.
FORBIDDEN_TOKENS = frozenset(
    {
        "impressions",
        "reach",
        "saves",
        "saved",
        "profile_views",
        "profile_visits",
        "profilevisits",
        "demographics",
        "demographic",
        "follower_age",
        "age_range",
        "agerange",
        "gender",
    }
)


def _has_forbidden(name: str) -> bool:
    low = name.lower()
    return any(tok in low for tok in FORBIDDEN_TOKENS)


def test_snapshots_sutunlari_yasak_alan_icermiyor() -> None:
    cols = set(Snapshot.__table__.columns.keys())
    leaked = {c for c in cols if _has_forbidden(c)}
    assert not leaked, f"snapshots'ta yasak sütun: {leaked}"
    # Yasak metriklerin gidebileceği tek yer raw (JSONB arşivi).
    assert "raw" in cols


def test_posts_sutunlari_yalnizca_izin_verilen_metrikler() -> None:
    cols = set(Post.__table__.columns.keys())
    leaked = {c for c in cols if _has_forbidden(c)}
    assert not leaked, f"posts'ta yasak sütun: {leaked}"
    # SPEC §3: yalnız bu üç nicel alan.
    assert {"like_count", "comment_count", "view_count"} <= cols


@pytest.mark.parametrize("model", [Business, BusinessList, JobResult, JobStatus, Stats])
def test_http_semalarinda_yasak_alan_yok(model: type[BaseModel]) -> None:
    fields = set(model.model_fields)
    leaked = {f for f in fields if _has_forbidden(f)}
    assert not leaked, f"{model.__name__} şemasında yasak alan: {leaked}"


async def test_businesses_yaniti_yasak_anahtar_icermiyor() -> None:
    """`GET /businesses` yanıtındaki hiçbir öğede yasak anahtar bulunmamalı."""
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/businesses")

    assert response.status_code == 200
    body = response.json()
    for item in body["items"]:
        leaked = {k for k in item if _has_forbidden(k)}
        assert not leaked, f"/businesses öğesinde yasak anahtar: {leaked}"


def test_snapshot_cache_ttl_varsayilani_yedi_gun() -> None:
    """Maliyet disiplini: cache TTL varsayılanı tam 7 gün olmalı."""
    from api.config import Settings

    default = Settings.model_fields["snapshot_cache_ttl_seconds"].default
    assert default == 7 * 24 * 60 * 60
