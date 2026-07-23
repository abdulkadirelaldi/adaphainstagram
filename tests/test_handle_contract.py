"""SEC-5 blok 2 — handle eşleme sözleşme testi (api/core/handle.py).

`extract_ig_handle`'ı SEC-6'nın 20 işletmesiyle test eder: 14 handle, 6 NULL, dört
yanlış-pozitif tuzağı NULL. Sözleşme (docs/TASKS.md "IG handle eşleme sözleşmesi"):
handle YALNIZCA açık `instagram.com/{handle}` URL'sinden; ad benzerliğinden tahmin yok.

**Sözleşme regresyon testi:** "ad tahmini yok" maddesi bir daha sessizce kırılmasın —
`extract_ig_handle` fixture'daki backend fonksiyonudur, testi backend'i bağlar.
"""

from __future__ import annotations

from typing import Any

import pytest

from api.core import extract_ig_handle
from tests._fixture_facts import ref_extract_handle


def test_production_cikarim_bagimsiz_referansla_uyusuyor(load_fixture: Any) -> None:
    """`extract_ig_handle` (production) 100 işletmede bağımsız referans regex'le aynı sonucu vermeli.

    Referans (`tests/_fixture_facts.ref_extract_handle`) production'ın kopyası değil, ayrı
    yazılmış bir sözleşme uygulamasıdır. İkisinin her işletmede aynı handle'ı (veya NULL'ı)
    üretmesi, production'ın sözleşmeye uyduğunu bağımsız kaynaktan doğrular.
    """
    places = load_fixture("places_response")["places"]
    for p in places:
        assert extract_ig_handle(p) == ref_extract_handle(p), (
            f"Uyumsuzluk: {p.get('websiteUri')!r} → "
            f"production={extract_ig_handle(p)!r}, referans={ref_extract_handle(p)!r}"
        )
    # Fixture hem handle'lı hem NULL yolları içeriyor (ikisi de test edildi).
    handles = {h for p in places if (h := extract_ig_handle(p)) is not None}
    nulls = [p for p in places if extract_ig_handle(p) is None]
    assert handles, "handle'lı işletme bekleniyordu"
    assert nulls, "NULL yollu işletme bekleniyordu"


@pytest.mark.parametrize(
    ("name", "url"),
    [
        ("facebook ad-eşleşme", "https://www.facebook.com/atlasotogaleri"),
        ("instagram.com alt alan adı", "https://help.instagram.com/"),
        ("benzer alan adı (instagramm)", "https://www.instagramm.example.com/nostaljikafe"),
        ("düz web sitesi", "https://yildizkuyum.example.com"),
    ],
)
def test_tuzak_linkler_null_donuyor(name: str, url: str) -> None:
    """Dört yanlış-pozitif tuzağı handle üretmemeli (sözleşme: yanlış eşleme = hukuki ihlal)."""
    assert extract_ig_handle({"websiteUri": url}) is None, f"{name} handle üretti: {url}"


def test_gercek_instagram_url_handle_veriyor() -> None:
    assert extract_ig_handle({"websiteUri": "https://www.instagram.com/kahvedukkani/"}) == (
        "kahvedukkani"
    )
    # www'suz da olur.
    assert extract_ig_handle({"websiteUri": "https://instagram.com/kuyumcu55"}) == "kuyumcu55"


def test_ad_benzerligi_tahmin_edilmiyor_regresyon() -> None:
    """SÖZLEŞME REGRESYONU: ada benzeyen ama instagram olmayan link → NULL.

    Bir işletmenin adı 'Elmas Kuyumculuk' ve elinde yalnız facebook linki var. Naif bir
    çıkarım addan 'elmaskuyumculuk' handle'ı uydurabilir — sözleşme bunu YASAKLAR (yanlış
    işletmeye rapor = hukuki sınır ihlali). Bu test o davranışı makineye bağlar: çıkarım
    ad-tahminine açılırsa (regex gevşetilir / ad-benzerliği eklenirse) burası kırmızıya döner.
    """
    raw = {
        "displayName": {"text": "Elmas Kuyumculuk"},
        "websiteUri": "https://www.facebook.com/elmaskuyumculuk",
        "formattedAddress": "elmaskuyumculuk caddesi",  # metinde ad geçiyor — yine de tahmin yok
    }
    assert extract_ig_handle(raw) is None


def test_rezerve_yollar_handle_degil() -> None:
    """instagram.com/p/... gibi profil olmayan yollar handle sayılmaz."""
    assert extract_ig_handle({"websiteUri": "https://www.instagram.com/p/ABC123/"}) is None
    assert extract_ig_handle({"websiteUri": "https://instagram.com/explore/"}) is None


def test_ic_ice_raw_taraniyor() -> None:
    """URL raw'ın derininde bir alanda olsa da bulunmalı (adaptör raw'ı iç içe olabilir)."""
    raw = {
        "displayName": {"text": "X"},
        "socials": {"links": ["https://twitter.com/x", "https://instagram.com/derindeki"]},
    }
    assert extract_ig_handle(raw) == "derindeki"
