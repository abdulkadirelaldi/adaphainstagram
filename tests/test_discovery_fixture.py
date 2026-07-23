"""Keşif demo fixture setinin iç tutarlılık testleri (SEC-6 → SEC-8'de 100 hesaba büyüdü).

Faz 3 bitiş kriteri "100 hesap taranıp panelde skorlarıyla listeleniyor" (SPEC §8) bu
fixture'la beslenir. Burada test edilen **fixture'ın kendisi**: handle eşleme sözleşmesine
(docs/TASKS.md) ve SPEC §4 kohort mantığına uygun kurulmuş mu.

Sayılar `tests/_fixture_facts.py`'den türetilir — magic number yok, fixture büyüyünce uyar.
BE-9/BE-11'in mantığı burada test EDİLMEZ; yalnız fixture kompozisyonu doğrulanır.

Canlı çağrı yok (CLAUDE.md kural 6).
"""

from __future__ import annotations

from typing import Any

from tests._fixture_facts import compute_facts, ref_extract_handle

# Sözleşmeye göre kesin handle üretmemesi gereken tuzaklar (SEC-6'dan korunur).
TRAP_URLS = {
    "https://www.facebook.com/atlasotogaleri",  # ad-eşleşme, facebook
    "https://help.instagram.com/",  # instagram.com alt alan adı, profil değil
    "https://www.instagramm.example.com/nostaljikafe",  # benzer alan adı
    "https://yildizkuyum.example.com",  # instagram olmayan site
}


def _facts(load_fixture: Any) -> Any:
    return compute_facts(
        load_fixture("places_response"),
        load_fixture("ig_business_discovery")["profiles"],
        load_fixture("apify_profile")["profiles"],
    )


def test_yuz_isletme_var(load_fixture: Any) -> None:
    facts = _facts(load_fixture)
    assert facts.n_places == 100, "Faz 3 demo'su 100 işletme bekliyor"


def test_kategori_cesitliligi_kohort_icin_yeterli(load_fixture: Any) -> None:
    """SPEC §4 kohort<5 kuralı test edilebilsin: hem >=5 hem <5 kategori olmalı."""
    facts = _facts(load_fixture)
    assert len(facts.big_categories) >= 2, (
        f">=5 üyeli en az 2 kategori bekleniyordu: {dict(facts.categories)}"
    )
    assert facts.small_categories, (
        f"Kohort<5 (watch) yolu için <5 üyeli en az 1 kategori bekleniyordu: {dict(facts.categories)}"
    )


def test_handle_ve_null_dagilimi(load_fixture: Any) -> None:
    """Handle taşıyan ve taşımayan işletmeler birlikte var (snapshot + NULL yolları)."""
    facts = _facts(load_fixture)
    assert facts.handles, "En az bir handle'lı işletme bekleniyordu"
    assert facts.null_count > 0, "En az bir handle'sız işletme bekleniyordu (NULL yolu)"
    assert len(facts.handles) + facts.null_count == facts.n_places


def test_tuzak_linkler_handle_uretmiyor(load_fixture: Any) -> None:
    """SEC-6 yanlış-pozitif tuzakları hâlâ NULL üretmeli (sözleşme: ad tahmini yok)."""
    places = load_fixture("places_response")["places"]
    by_url = {p.get("websiteUri"): p for p in places}
    for url in TRAP_URLS:
        assert url in by_url, f"Tuzak link fixture'dan kaybolmuş: {url}"
        assert ref_extract_handle(by_url[url]) is None, f"Tuzak handle üretti: {url}"


def test_her_handle_bir_profille_cozulebiliyor(load_fixture: Any) -> None:
    """Handle taşıyan her işletme BD (dolu) veya Apify profiliyle çözülebilmeli."""
    facts = _facts(load_fixture)
    unresolved = facts.handles - facts.resolvable
    assert not unresolved, f"Çözülemeyen handle(ler): {unresolved}"


def test_fallback_handleleri_bdde_bos_apifyde_dolu(load_fixture: Any) -> None:
    """Fallback yolu için veri: BD boş {} döner, Apify profili sağlar (SPEC §2)."""
    facts = _facts(load_fixture)
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    assert facts.fallback, "En az bir fallback handle bekleniyordu"
    for handle in facts.fallback:
        assert handle in bd and not bd[handle], f"{handle}: BD yanıtı boş {{}} olmalı"
        assert handle in apify, f"{handle}: Apify profili olmalı"


def test_apify_profilleri_yasak_alanlari_koruyor(load_fixture: Any) -> None:
    """Tüm Apify profilleri yasak metrikleri (kural 7) BİLEREK taşımalı — BE-9 düşürür, SEC-5 doğrular."""
    apify = load_fixture("apify_profile")["profiles"]
    for handle, prof in apify.items():
        for f in ("impressions", "reach", "saves", "profileVisits", "followerDemographics"):
            assert f in prof, f"{handle}: yasak profil alanı {f!r} korunmalıydı"


def test_eksik_alan_yollari_korunuyor(load_fixture: Any) -> None:
    """En az bir işletme telefonsuz, en az biri websitesiz (normalize None yolu)."""
    places = load_fixture("places_response")["places"]
    assert any("nationalPhoneNumber" not in p for p in places), "telefonsuz işletme bekleniyordu"
    assert any("websiteUri" not in p for p in places), "websitesiz işletme bekleniyordu"


def test_referans_zaman_gecmiste_sabit(load_fixture: Any) -> None:
    """Tüm post tarihleri sabit ISO ve referans zaman (2026-07-15) civarında — göreli 'bugün' yok.

    SEC-8 sözleşmesi: BE-11 90 gün penceresini bu sabit referansa göre kurar. Tarihlerin
    fixture'da sabit olduğunu (gelecekte kaymayacağını) burada güvenceye alıyoruz.
    """
    bd = load_fixture("ig_business_discovery")["profiles"]
    stamps = [
        post["timestamp"]
        for v in bd.values()
        if v
        for post in v["business_discovery"]["media"]["data"]
    ]
    assert stamps, "BD gönderi zaman damgası bekleniyordu"
    # Hepsi 2026 sabit tarihleri; hiçbiri 2027+ değil (göreli 'bugün' kullanılmadığının işareti).
    assert all(s.startswith("2026-") for s in stamps)
