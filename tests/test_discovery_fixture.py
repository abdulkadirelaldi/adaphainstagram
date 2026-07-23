"""Keşif demo fixture setinin iç tutarlılık testleri (SEC-6).

Faz 2 bitiş kriteri "tek komutla 20 işletme keşfedilip snapshot'ı alınıyor" (SPEC §8)
bu fixture'la beslenecek. Burada test edilen **fixture'ın kendisi**: handle eşleme
sözleşmesine (docs/TASKS.md "IG handle eşleme sözleşmesi") uygun şekilde kurulmuş mu.

**Kapsam sınırı:** BE-9'un handle çıkarım/persist mantığı burada test EDİLMEZ — o
SEC-5'te (BE-9 sonrası) gelir. Buradaki `_extract_handle` yalnızca fixture kompozisyonunu
sözleşmeye göre doğrulamak için var; BE-9 kendi üretim çıkarıcısını yazar, bu onun
kopyası değil.

Canlı çağrı yok (CLAUDE.md kural 6).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# Handle eşleme sözleşmesi: handle YALNIZCA açık bir instagram.com/{handle} URL'sinden
# türetilir, ad benzerliğinden tahmin edilmez. Host tam olarak (www.)instagram.com
# olmalı — help.instagram.com gibi alt alan adları ve instagramm.example.com gibi
# benzer alan adları handle üretmez.
_IG_URL = re.compile(
    r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?$",
    re.IGNORECASE,
)

# Sözleşme gereği handle taşıması beklenen 14 işletme.
EXPECTED_HANDLES = {
    "elmaskuyumculuk",
    "atakumdisklinigi",
    "sahilkahveevi",
    "karadenizoto",
    "samsunemlakofisi",
    "bayramkuyumcu",
    "denizkafe55",
    "atakumkuafor",
    "sactasarimstudio",
    "mavideniz.emlak",
    "cadde19kafe",
    "glamkuafor",
    "modakuafor.samsun",
    "espressolab.samsun",
}

# BD boş döndüğü için Apify'a düşen handle'lar (fallback yolu, SPEC §2).
FALLBACK_HANDLES = {"sahilkahveevi", "cadde19kafe"}


def _extract_handle(place: dict[str, Any]) -> str | None:
    """Sözleşmeye göre place raw'ından handle çıkarır (yalnız fixture doğrulaması için)."""
    website = place.get("websiteUri")
    if not website:
        return None
    match = _IG_URL.match(website)
    return match.group(1).lower() if match else None


def test_yirmi_isletme_var(load_fixture: Any) -> None:
    data = load_fixture("places_response")
    assert len(data["places"]) == 20, "Faz 2 demo'su tam 20 işletme bekliyor"


def test_kategori_cesitliligi_kohort_icin_yeterli(load_fixture: Any) -> None:
    """SPEC §4 kohort<5 kuralı test edilebilsin: hem >=5 hem <5 kategori olmalı."""
    data = load_fixture("places_response")
    counts = Counter(p["primaryType"] for p in data["places"])
    buyuk = [c for c, n in counts.items() if n >= 5]
    kucuk = [c for c, n in counts.items() if n < 5]
    assert len(buyuk) >= 2, (
        f"Kohort medyanı testi için >=5 üyeli en az 2 kategori bekleniyordu: {dict(counts)}"
    )
    assert kucuk, (
        f"Kohort<5 (watch) yolu testi için <5 üyeli en az 1 kategori bekleniyordu: {dict(counts)}"
    )


def test_handle_tasiyan_ve_tasimayan_isletmeler(load_fixture: Any) -> None:
    """14 işletme açık instagram URL'si taşır, 6 taşımaz (NULL yolu)."""
    data = load_fixture("places_response")
    handles = {h for p in data["places"] if (h := _extract_handle(p)) is not None}
    handlesiz = [p for p in data["places"] if _extract_handle(p) is None]
    assert handles == EXPECTED_HANDLES, (
        f"Çıkarılan handle kümesi beklenenden farklı.\n"
        f"Fazla: {handles - EXPECTED_HANDLES}\nEksik: {EXPECTED_HANDLES - handles}"
    )
    assert len(handlesiz) == 6, "6 işletme handle taşımamalı (ig_handle=NULL yolu)"


def test_tuzak_linkler_handle_uretmiyor(load_fixture: Any) -> None:
    """Ad benzerliği / benzer alan adı tuzakları handle vermemeli (yanlış-pozitif koruması).

    Sözleşme: yanlış eşleme = yanlış işletmeye rapor = hukuki sınır ihlali. Bu yüzden
    ada benzeyen facebook linki, instagram.com alt alan adı ve benzer alan adı
    handle ÜRETMEMELİ.
    """
    data = load_fixture("places_response")
    by_name = {p["displayName"]["text"]: p for p in data["places"]}

    tuzaklar = {
        "Atlas Oto Galeri": "https://www.facebook.com/atlasotogaleri",  # ad-eşleşme, facebook
        "Sırma Kuaför": "https://help.instagram.com/",  # instagram.com alt alan adı, profil değil
        "Nostalji Kafe": "https://www.instagramm.example.com/nostaljikafe",  # benzer alan adı
        "Yıldız Kuyumculuk": "https://yildizkuyum.example.com",  # instagram olmayan site
    }
    for name, expected_url in tuzaklar.items():
        place = by_name[name]
        assert place.get("websiteUri") == expected_url, f"{name}: tuzak link değişmiş"
        assert _extract_handle(place) is None, (
            f"{name}: tuzak link handle üretti — sözleşme ihlali "
            f"(ad benzerliğinden/alt alan adından tahmin yasak)"
        )


def test_her_handle_bir_profille_cozulebiliyor(load_fixture: Any) -> None:
    """Handle taşıyan her işletme BD (dolu) veya Apify profiliyle çözülebilmeli.

    Aksi halde BE-9 o handle için snapshot alamaz ve demo eksik kalır.
    """
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    for handle in EXPECTED_HANDLES:
        bd_dolu = bool(bd.get(handle))  # boş {} → False
        apify_var = handle in apify
        assert bd_dolu or apify_var, (
            f"{handle}: ne dolu BD profili ne Apify profili var — çözülemez"
        )


def test_fallback_handleleri_bdde_bos_apifyde_dolu(load_fixture: Any) -> None:
    """Fallback yolu için veri: BD boş {} döner, Apify profili sağlar (SPEC §2)."""
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    for handle in FALLBACK_HANDLES:
        assert handle in bd, f"{handle}: fallback için BD'de anahtar bulunmalı"
        assert not bd[handle], f"{handle}: fallback için BD yanıtı boş {{}} olmalı"
        assert handle in apify, f"{handle}: fallback hedefi Apify'da profili olmalı"


def test_apify_fallback_profilleri_yasak_alanlari_koruyor(load_fixture: Any) -> None:
    """Apify profilleri yasak metrikleri (kural 7) BİLEREK taşımalı — BE-9 düşürecek, SEC-5 doğrulayacak."""
    apify = load_fixture("apify_profile")["profiles"]
    for handle in FALLBACK_HANDLES:
        prof = apify[handle]
        for field in ("impressions", "reach", "saves", "profileVisits", "followerDemographics"):
            assert field in prof, f"{handle}: yasak profil alanı {field!r} korunmalıydı"
        first_post = prof["latestPosts"][0]
        for field in ("impressions", "reach", "saved"):
            assert field in first_post, f"{handle}: yasak gönderi alanı {field!r} korunmalıydı"


def test_eksik_alan_yollari_korunuyor(load_fixture: Any) -> None:
    """En az bir işletme telefonsuz, en az biri websitesiz (normalize None yolu)."""
    data = load_fixture("places_response")
    assert any("nationalPhoneNumber" not in p for p in data["places"]), (
        "En az bir telefonsuz işletme bekleniyordu"
    )
    assert any("websiteUri" not in p for p in data["places"]), (
        "En az bir websitesiz işletme bekleniyordu"
    )
