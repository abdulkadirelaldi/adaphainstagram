"""BE-6 normalize şemalarının kontrat testleri (SEC-4).

Adaptör gövdesi olmadan çalışır: yalnızca `NormalizedBusiness`/`NormalizedProfile`/
`NormalizedPost` şemalarının davranışı sınanır. Adaptörün fixture'ı normalize etmesi
BE-7/BE-8'de gelir, o entegrasyon testi SEC-5'tedir.

Merkezdeki kural: `extra="forbid"`. CLAUDE.md kural 7'nin yasakladığı bir metrik
(erişim/gösterim/kaydetme/demografi) normalize modele verilirse `ValidationError`
atmalı — böylece "yasak alan yüzeye çıkarsa test kırmızı" bir makine kuralıdır.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from api.adapters.base import (
    NormalizedBusiness,
    NormalizedPost,
    NormalizedProfile,
)

# --- Apify fixture'ının yasakladığı alanlar (kural 7) ---------------------------
#
# Bu adlar apify_profile.json'da BİLEREK var. Normalize şema hepsini reddetmeli.
# `test_yasak_alan_adlari_fixturede_gercekten_var` bu listeyi fixture'a bağlar:
# fixture'dan biri düşerse test uyarır, liste ile fixture senkron kalır.
FORBIDDEN_PROFILE_FIELDS = [
    "impressions",
    "reach",
    "saves",
    "profileVisits",
    "followerDemographics",
]
FORBIDDEN_POST_FIELDS = [
    "impressions",
    "reach",
    "saved",
]


def _a_valid_post() -> NormalizedPost:
    return NormalizedPost(
        ig_id="17920000000111001",
        media_type="IMAGE",
        posted_at=datetime(2026, 6, 18, 9, 12, tzinfo=UTC),
        like_count=142,
        comment_count=11,
    )


# --- Geçerli örnekleme ----------------------------------------------------------


def test_business_gecerli_veriyle_orneklenir() -> None:
    b = NormalizedBusiness(
        place_id="ChIJradar0000kuyumcu0001",
        name="Elmas Kuyumculuk",
        category="jewelry_store",
        address="Kale Mah. ...",
        phone="0362 431 20 14",
        website="https://example.com",
        rating_count=214,
        raw={"id": "ChIJradar0000kuyumcu0001"},
    )
    assert b.place_id == "ChIJradar0000kuyumcu0001"
    assert b.rating_count == 214


def test_business_opsiyonel_alanlar_none_olabilir() -> None:
    """Places'te telefonsuz/websitesiz işletme (Sahil Kahve Evi) yolu."""
    b = NormalizedBusiness(place_id="ChIJradar0000kafe0003", name="Sahil Kahve Evi", raw={})
    assert b.phone is None
    assert b.website is None
    assert b.category is None
    assert b.rating_count is None


def test_profile_gecerli_veriyle_orneklenir() -> None:
    p = NormalizedProfile(
        source="apify",
        followers=3120,
        follows=845,
        media_count=194,
        biography="İlkadım sahilde üçüncü nesil kahve.",
        external_url="https://example.com",
        is_professional=True,
        posts=[_a_valid_post()],
        raw={"username": "sahilkahveevi"},
    )
    assert p.source == "apify"
    assert len(p.posts) == 1


def test_post_gecerli_veriyle_orneklenir() -> None:
    post = _a_valid_post()
    assert post.ig_id == "17920000000111001"
    assert post.view_count is None  # BD gönderi izlenmesi vermez


# --- extra="forbid": yasak alan reddi (kural 7'nin makine hali) ------------------


# Yasak/geçersiz girdiler bilerek şemayı ihlal eder; bunları statik kwargs yerine
# `model_validate(dict)` ile veriyoruz. Sebep: adaptör de ham dış-API dict'ini
# `model_validate` ile doğrular, testin girdi biçimi gerçek yolu taklit eder ve
# dinamik alan adları tip denetimini kirletmez.


@pytest.mark.parametrize("field", FORBIDDEN_PROFILE_FIELDS)
def test_profile_yasak_alani_reddeder(field: str) -> None:
    """Profil düzeyi yasak metrik verilince ValidationError atmalı."""
    payload: dict[str, Any] = {"source": "apify", "raw": {}, field: 999}
    with pytest.raises(ValidationError) as exc:
        NormalizedProfile.model_validate(payload)
    # Hatanın gerçekten 'extra forbidden' olduğunu doğrula — başka sebeple patlamasın.
    assert any(e["type"] == "extra_forbidden" for e in exc.value.errors())


@pytest.mark.parametrize("field", FORBIDDEN_POST_FIELDS)
def test_post_yasak_alani_reddeder(field: str) -> None:
    """Gönderi düzeyi yasak metrik verilince ValidationError atmalı."""
    payload: dict[str, Any] = {
        "ig_id": "1",
        "posted_at": datetime(2026, 6, 18, tzinfo=UTC),
        field: 999,
    }
    with pytest.raises(ValidationError) as exc:
        NormalizedPost.model_validate(payload)
    assert any(e["type"] == "extra_forbidden" for e in exc.value.errors())


def test_business_yasak_alani_reddeder() -> None:
    """Keşif şeması da forbid: demografi vb. place kaydına sızamaz."""
    payload: dict[str, Any] = {
        "place_id": "x",
        "name": "y",
        "raw": {},
        "followerDemographics": {"gender": {"female": 0.5}},
    }
    with pytest.raises(ValidationError) as exc:
        NormalizedBusiness.model_validate(payload)
    assert any(e["type"] == "extra_forbidden" for e in exc.value.errors())


# --- ge=0 sınırları --------------------------------------------------------------


@pytest.mark.parametrize("field", ["followers", "follows", "media_count"])
def test_profile_negatif_sayac_reddedilir(field: str) -> None:
    payload: dict[str, Any] = {"source": "apify", "raw": {}, field: -1}
    with pytest.raises(ValidationError) as exc:
        NormalizedProfile.model_validate(payload)
    assert any(e["type"] == "greater_than_equal" for e in exc.value.errors())


@pytest.mark.parametrize("field", ["like_count", "comment_count", "view_count"])
def test_post_negatif_sayac_reddedilir(field: str) -> None:
    payload: dict[str, Any] = {
        "ig_id": "1",
        "posted_at": datetime(2026, 6, 18, tzinfo=UTC),
        field: -1,
    }
    with pytest.raises(ValidationError) as exc:
        NormalizedPost.model_validate(payload)
    assert any(e["type"] == "greater_than_equal" for e in exc.value.errors())


def test_business_negatif_rating_count_reddedilir() -> None:
    with pytest.raises(ValidationError) as exc:
        NormalizedBusiness(place_id="x", name="y", raw={}, rating_count=-1)
    assert any(e["type"] == "greater_than_equal" for e in exc.value.errors())


# --- raw serbest dict ------------------------------------------------------------


def test_raw_serbest_dict_kabul_eder() -> None:
    """Ham veri raw'a gömülebilir — iç içe, karışık tipli olabilir.

    Yasak alanların gideceği yer burasıdır: normalize yüzeyde değil, raw içinde.
    raw'da yasak anahtar bulunması sorun değil; sorun onun normalize alana çıkması.
    """
    raw = {
        "username": "sahilkahveevi",
        "impressions": 15234,
        "followerDemographics": {"gender": {"female": 0.58, "male": 0.42}},
        "latestPosts": [{"id": "1", "saved": 55}],
    }
    p = NormalizedProfile(source="apify", raw=raw)
    assert p.raw["impressions"] == 15234
    # Yasak metrik raw'da yaşıyor ama normalize yüzeyde alan olarak yok.
    assert not hasattr(p, "impressions")
    assert "impressions" not in p.model_dump(exclude={"raw"})


# --- Liste ile fixture senkronizasyonu ------------------------------------------


def test_yasak_alan_adlari_fixturede_gercekten_var(load_fixture: object) -> None:
    """Test ettiğimiz yasak adlar apify fixture'ında gerçekten bulunmalı.

    Fixture yasak alanı içermeyi bırakırsa (ör. biri 'temizleyip' sildi) bu test
    uyarır. Böylece kontrat testi hayali bir alanı değil, gerçek ham veriyi kovalar.
    """
    # Fixture SEC-6'da handle-anahtarlı yapıya geçti: profiles[<handle>] altında.
    data = load_fixture("apify_profile")  # type: ignore[operator]
    profile = data["profiles"]["sahilkahveevi"]
    for field in FORBIDDEN_PROFILE_FIELDS:
        assert field in profile, f"apify sahilkahveevi profilinde {field!r} bekleniyordu"
    first_post = profile["latestPosts"][0]
    for field in FORBIDDEN_POST_FIELDS:
        assert field in first_post, f"apify sahilkahveevi gönderisinde {field!r} bekleniyordu"
