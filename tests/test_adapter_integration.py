"""SEC-5 blok 1+3 — adaptör entegrasyonu + fallback (DB'siz).

SEC-4 şema kontratıydı; burada **adaptör gövdesi** fixture'ı gerçekten normalize
ediyor mu (alan eşlemesi README ile) ve profil servisi BD→Apify fallback'ini doğru
yapıyor mu. Enjekte sahte client; canlı çağrı yok (kural 6, ağ muhafızı altında geçer).
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from api.adapters.apify import ApifyAdapter, normalize_apify
from api.adapters.base import DiscoveryQuery, ProfileUnavailableError
from api.adapters.business_discovery import (
    BusinessDiscoveryAdapter,
    normalize_business_discovery,
)
from api.adapters.places import PlacesAdapter, normalize_places
from api.services.profile import fetch_profile
from tests._mocks import (
    CallCounter,
    apify_client,
    bd_client,
    bd_error_client,
    places_client,
)

# --- Blok 1: adaptör → normalize (alan eşlemesi README ile) ---------------------


async def test_places_adapter_fixturei_normalize_ediyor(load_fixture: Any) -> None:
    raw = load_fixture("places_response")
    counter = CallCounter()
    client = places_client(raw, counter)
    try:
        businesses = await PlacesAdapter(client=client).discover(DiscoveryQuery(query="samsun"))
    finally:
        await client.aclose()

    assert counter.count == 1  # tek POST
    assert len(businesses) == 20

    elmas = next(b for b in businesses if b.place_id == "ChIJradar00kuyumcu0001")
    assert elmas.name == "Elmas Kuyumculuk"
    assert elmas.category == "jewelry_store"  # primaryType
    assert elmas.phone == "0362 431 20 14"  # nationalPhoneNumber
    assert elmas.website == "https://www.instagram.com/elmaskuyumculuk/"  # websiteUri
    assert elmas.rating_count == 214  # userRatingCount
    # Normalize dışı alanlar yalnız raw'da: rating, types, internationalPhoneNumber.
    assert "rating" in elmas.raw
    assert not hasattr(elmas, "rating")


def test_places_normalize_none_yolu(load_fixture: Any) -> None:
    raw = load_fixture("places_response")
    businesses = normalize_places(raw)
    sahil = next(b for b in businesses if b.name == "Sahil Kahve Evi")
    assert sahil.phone is None  # nationalPhoneNumber yok
    gunes = next(b for b in businesses if b.name == "Güneş Diş Kliniği")
    assert gunes.website is None  # websiteUri yok
    ada = next(b for b in businesses if b.name == "Ada Emlak")
    assert ada.phone is None and ada.website is None


def test_bd_adapter_alan_donusumleri(load_fixture: Any) -> None:
    profiles = load_fixture("ig_business_discovery")["profiles"]
    profile = normalize_business_discovery(profiles["atakumdisklinigi"])

    assert profile.source == "business_discovery"
    assert profile.followers == 4820  # followers_count
    assert profile.follows == 312  # follows_count
    assert profile.media_count == 287
    assert profile.external_url == "https://www.instagram.com/atakumdisklinigi"  # website
    assert profile.is_professional is True  # BD yalnız işletme hesabı
    assert len(profile.posts) == 2

    # comments_count → comment_count (ad farkı, README).
    post = profile.posts[0]
    assert post.comment_count == 11
    # BD gönderi izlenmesi vermez → view_count None.
    assert post.view_count is None
    # Video gönderisi: thumbnail_url → thumb_url.
    video = profile.posts[1]
    assert video.media_type == "VIDEO"
    assert video.thumb_url == "https://scontent.example.com/2002_thumb.jpg"


async def test_apify_adapter_alan_donusumleri(load_fixture: Any) -> None:
    profiles = load_fixture("apify_profile")["profiles"]
    counter = CallCounter()
    client = apify_client(profiles, counter)
    try:
        profile = await ApifyAdapter(client=client).fetch_profile("sahilkahveevi")
    finally:
        await client.aclose()

    assert counter.count == 1
    assert profile.source == "apify"
    assert profile.media_count == 194  # postsCount
    assert profile.is_professional is True  # isBusinessAccount
    assert len(profile.posts) == 3

    # type → media_type, likesCount → like_count, videoViewCount → view_count.
    image = profile.posts[0]
    assert image.media_type == "Image"
    assert image.like_count == 176
    assert image.view_count is None  # resimde video görüntüsü yok
    video = profile.posts[1]
    assert video.view_count == 8710  # videoViewCount


def test_apify_normalize_yasak_alanlari_dusuruyor(load_fixture: Any) -> None:
    """Adaptör düzeyinde: yasak metrikler normalize yüzeye çıkmıyor, raw'da kalıyor."""
    profiles = load_fixture("apify_profile")["profiles"]
    profile = normalize_apify(profiles["sahilkahveevi"])
    surface = profile.model_dump(exclude={"raw"})
    for forbidden in ("impressions", "reach", "saves", "profileVisits", "followerDemographics"):
        assert forbidden not in surface
    # Ama raw arşivde duruyor.
    assert profile.raw["impressions"] == 15234


# --- Blok 3: fallback (BD → Apify) ----------------------------------------------


async def test_fallback_bd_dolu_business_discovery_kaliyor(load_fixture: Any) -> None:
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    c1, c2 = CallCounter(), CallCounter()
    bd_c, apify_c = bd_client(bd, c1), apify_client(apify, c2)
    try:
        profile = await fetch_profile(
            "elmaskuyumculuk",
            primary=BusinessDiscoveryAdapter(client=bd_c),
            fallback=ApifyAdapter(client=apify_c),
        )
    finally:
        await bd_c.aclose()
        await apify_c.aclose()

    assert profile.source == "business_discovery"
    assert c1.count == 1  # BD denendi
    assert c2.count == 0  # Apify'a düşülmedi


async def test_fallback_bd_bos_apifye_dusuyor(load_fixture: Any) -> None:
    """SEC-6'nın fallback handle'ı: BD boş {} → Apify → source=apify."""
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    c1, c2 = CallCounter(), CallCounter()
    bd_c, apify_c = bd_client(bd, c1), apify_client(apify, c2)
    try:
        profile = await fetch_profile(
            "sahilkahveevi",
            primary=BusinessDiscoveryAdapter(client=bd_c),
            fallback=ApifyAdapter(client=apify_c),
        )
    finally:
        await bd_c.aclose()
        await apify_c.aclose()

    assert profile.source == "apify"
    assert c1.count == 1  # BD denendi (boş döndü)
    assert c2.count == 1  # Apify'a düşüldü


async def test_fallback_http_hatasi_yukseliyor_sessiz_dusme_yok(load_fixture: Any) -> None:
    """Ağ/HTTP hatası fallback tetiklemez — yükselir. Yoksa yanlış kaynağa sessiz düşüş olurdu."""
    apify = load_fixture("apify_profile")["profiles"]
    c1, c2 = CallCounter(), CallCounter()
    bd_c = bd_error_client(500, c1)  # BD sunucu hatası
    apify_c = apify_client(apify, c2)
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_profile(
                "elmaskuyumculuk",
                primary=BusinessDiscoveryAdapter(client=bd_c),
                fallback=ApifyAdapter(client=apify_c),
            )
    finally:
        await bd_c.aclose()
        await apify_c.aclose()

    assert c1.count == 1  # BD denendi, patladı
    assert c2.count == 0  # Apify'a düşülMEDİ — hata yutulmadı


def test_fallback_yalnizca_profileunavailable_tetikler() -> None:
    """`ProfileUnavailableError` `AdapterError` değil, ayrı bir sinyal — yalnız o fallback tetikler."""
    # ProfileUnavailableError bir istisna sınıfı; HTTPStatusError'dan bağımsız.
    assert issubclass(ProfileUnavailableError, Exception)
    assert not issubclass(ProfileUnavailableError, httpx.HTTPStatusError)
