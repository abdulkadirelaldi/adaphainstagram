"""Fixture geçerlilik testleri (SEC-4).

Üç dış-API fixture'ı geçerli JSON mu ve beklenen üst-düzey yapıyı taşıyor mu.
Bu, adaptör gövdesi (BE-7/BE-8) yazılırken fixture'ların altından kaymamasını
sağlar: fixture şekli sessizce bozulursa burası kırmızıya döner.

Canlı çağrı yok — yalnızca yerel dosya okunur (CLAUDE.md kural 6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXPECTED_FILES = ["places_response", "ig_business_discovery", "apify_profile"]


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_fixture_gecerli_json(name: str) -> None:
    """Dosya var ve geçerli JSON olarak yükleniyor."""
    path = FIXTURES_DIR / f"{name}.json"
    assert path.exists(), f"Fixture eksik: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data, f"{name}.json boş"


def test_places_ust_duzey_yapi(load_fixture: Any) -> None:
    data = load_fixture("places_response")
    assert "places" in data
    assert len(data["places"]) >= 3, "En az 3 işletme bekleniyordu"
    for place in data["places"]:
        assert "id" in place
        assert "displayName" in place and "text" in place["displayName"]


def test_places_en_az_bir_eksik_alanli_kayit_var(load_fixture: Any) -> None:
    """Normalize'ın None yolunu test edebilmek için en az bir işletme
    telefonsuz veya websitesiz olmalı."""
    data = load_fixture("places_response")
    eksik_telefon = [p for p in data["places"] if "nationalPhoneNumber" not in p]
    eksik_website = [p for p in data["places"] if "websiteUri" not in p]
    assert eksik_telefon, "En az bir telefonsuz işletme bekleniyordu (None yolu)"
    assert eksik_website, "En az bir websitesiz işletme bekleniyordu (None yolu)"


def test_ig_business_discovery_ust_duzey_yapi(load_fixture: Any) -> None:
    data = load_fixture("ig_business_discovery")
    bd = data["business_discovery"]
    for key in ("followers_count", "follows_count", "media_count", "biography"):
        assert key in bd, f"business_discovery.{key} eksik"
    posts = bd["media"]["data"]
    assert posts, "En az bir gönderi bekleniyordu"
    for post in posts:
        # Görev şartı: gönderiler like_count ve comments_count taşımalı.
        assert "like_count" in post
        assert "comments_count" in post
        assert "timestamp" in post


def test_apify_ust_duzey_yapi(load_fixture: Any) -> None:
    data = load_fixture("apify_profile")
    for key in ("username", "followersCount", "followsCount", "postsCount"):
        assert key in data, f"apify profil alanı eksik: {key}"
    posts = data["latestPosts"]
    assert posts, "En az bir gönderi bekleniyordu"
    for post in posts:
        assert "id" in post
        assert "likesCount" in post
        assert "commentsCount" in post


def test_ig_business_discovery_yasak_alan_icermiyor(load_fixture: Any) -> None:
    """BD temiz kaynak: yasak metrik (kural 7) ham veride bile olmamalı.

    Apify'ın aksine BD bu alanları döndürmez; fixture bunu yansıtmalı ki
    'temiz kaynak' varsayımı gerçek kalsın.
    """
    data = load_fixture("ig_business_discovery")
    blob = json.dumps(data).lower()
    for forbidden in ("impressions", "reach", "saves", "profilevisits", "demographic"):
        assert forbidden not in blob, (
            f"BD fixture'ında yasak alan izi: {forbidden!r}. "
            "BD temiz kaynak olmalı; yasak metrikler yalnız Apify fixture'ında."
        )
