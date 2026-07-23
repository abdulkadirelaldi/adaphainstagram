"""SEC-7 — triyaj skorlama motorunun saf-fonksiyon testleri (api/core/scoring.py).

DB'siz: dataclass girer, dataclass çıkar. "Şimdi" enjekte edilir (`REFERENCE_NOW`),
`datetime.now()` yok → deterministik, `currentDate`'e bağlı değil (kural 6).

Doğrulananlar: çarpım çökme (karşı-kanıtlı), durum eşikleri (off-by-one), mutlak-eşik
yokluğu (kohort-göreli potansiyel), referans zaman, kohort<5→watch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.core.scoring import (
    AccountData,
    PostData,
    activity_score,
    assign_status,
    capacity_score,
    combined_score,
    engagement_rate,
    potential_score,
    score_accounts,
)
from api.models.enums import TriageStatus

# SEC-8 fixture sözleşmesiyle aynı sabit referans (tests/fixtures/README.md).
REFERENCE_NOW = datetime(2026, 7, 15, 0, 0, 0, tzinfo=UTC)


def _post(
    days_ago: int, *, media_type: str = "IMAGE", caption: str = "gunluk", like: int = 10
) -> PostData:
    return PostData(
        posted_at=REFERENCE_NOW - timedelta(days=days_ago),
        media_type=media_type,
        caption=caption,
        like_count=like,
        comment_count=2,
    )


def _account(**kw: object) -> AccountData:
    base: dict[str, object] = {
        "business_id": 1,
        "snapshot_id": 1,
        "category": "cafe",
        "rating_count": 100,
        "has_website": True,
        "followers": 1000,
        "posts": (),
    }
    base.update(kw)
    return AccountData(**base)  # type: ignore[arg-type]


# --- Çarpım çökme davranışı (SPEC §4 gerekçesi) ---------------------------------


def test_carpim_cokme_bir_alt_skor_sifir() -> None:
    """Bir alt skor 0 → birleşik 0. Ölü ama potansiyelli/kapasiteli hesap qualified olmamalı."""
    assert combined_score(0.0, 95.0, 95.0) == 0.0


def test_carpim_dusuk_aktiflik_birlesigi_cokertiyor_karsi_kanit() -> None:
    """Aktiflik ≈0, potansiyel/kapasite yüksek → birleşik DÜŞÜK (rejected).

    KARŞI-KANIT: aynı değerlerin aritmetik ortalaması (toplam mantığı) yüksek çıkardı.
    Çarpım bunu çökertir (SPEC §4). Formül toplama/ortalamaya çevrilirse bu test kırmızı olur.
    """
    activity, potential, capacity = 1.0, 95.0, 95.0
    score = combined_score(activity, potential, capacity)
    aritmetik_ortalama = (activity + potential + capacity) / 3

    assert score < 40, f"çarpım çökmesi bekleniyordu, score={score}"
    assert aritmetik_ortalama >= 60, "ortalama yüksek olmalı (karşı-kanıtın anlamı)"
    # Çarpım, toplam mantığından belirgin biçimde düşük.
    assert score < aritmetik_ortalama - 30


def test_olu_hesap_yuksek_kapasiteyle_bile_rejected() -> None:
    """0 gönderi → aktiflik 0 → çarpım çöker; yüksek kapasite kategoride bile rejected."""
    dead = _account(category="dental_clinic", followers=8000, rating_count=800, posts=())
    # Dead'in kategorisinde kohort≥5 olmalı ki potansiyel hesaplansın ve çöküş görünsün
    # (aksi halde kohort<5 → watch yoluna girer, bu testin konusu değil).
    filler = [
        _account(business_id=i, snapshot_id=i, category="dental_clinic", posts=(_post(3),))
        for i in range(2, 7)
    ]
    results = {r.business_id: r for r in score_accounts([dead, *filler], REFERENCE_NOW)}
    dead_result = results[1]
    assert dead_result.activity == 0.0
    assert dead_result.score == 0.0
    assert dead_result.status is TriageStatus.REJECTED


# --- Durum eşikleri (off-by-one) ------------------------------------------------


def test_durum_esikleri_sinir_degerleri() -> None:
    """SPEC §1: <40 rejected, 40–69 watch, ≥70 qualified. Sınırlar tam."""
    assert assign_status(39.99) is TriageStatus.REJECTED
    assert assign_status(40.0) is TriageStatus.WATCH  # 40 dahil watch
    assert assign_status(69.99) is TriageStatus.WATCH
    assert assign_status(70.0) is TriageStatus.QUALIFIED  # 70 dahil qualified
    assert assign_status(0.0) is TriageStatus.REJECTED
    assert assign_status(100.0) is TriageStatus.QUALIFIED


# --- Mutlak eşik yokluğu (kohort-göreli potansiyel) -----------------------------


def test_mutlak_esik_yok_ayni_etkilesim_farkli_medyanda_farkli_potansiyel() -> None:
    """Aynı ham etkileşim, farklı kohort medyanı → farklı potansiyel (SPEC §4: mutlak eşik yok).

    Etkileşimi kohort medyanının ALTINDA olan hesabın potansiyeli yüksek (kötü yönetim);
    aynı ham etkileşim, düşük medyanlı bir kohortta ortalamanın üstünde kalır → potansiyel düşük.
    Reels/CTA sinyalleri sabit; yalnız kohort medyanı değişiyor.
    """
    # Sabit: 1 gönderi, IMAGE (reels yok), CTA yok, like+comment/followers = 0.05.
    acc = _account(followers=1000, posts=(_post(5, media_type="IMAGE", caption="gunluk", like=48),))
    rate = engagement_rate(acc, REFERENCE_NOW)
    assert rate is not None and abs(rate - 0.05) < 1e-9

    yuksek_medyan = potential_score(acc, REFERENCE_NOW, cohort_engagement_median=0.10)
    dusuk_medyan = potential_score(acc, REFERENCE_NOW, cohort_engagement_median=0.02)

    # Medyanı 0.10 olan kohortta hesap altta kalır → etkileşim sinyali yüksek → potansiyel daha yüksek.
    assert yuksek_medyan > dusuk_medyan, (
        f"kohort-göreli fark bekleniyordu: 0.10→{yuksek_medyan}, 0.02→{dusuk_medyan}"
    )


def test_medyan_yoksa_etkilesim_sinyali_atlanir() -> None:
    """Kohort medyanı yoksa (veri yetersiz) potansiyel yalnız Reels+CTA'dan; patlama yok."""
    acc = _account(posts=(_post(5, media_type="IMAGE", caption="gunluk"),))
    p = potential_score(acc, REFERENCE_NOW, cohort_engagement_median=None)
    # IMAGE + CTA yok → iki sinyal de 1.0 → potansiyel 100.
    assert p == 100.0


# --- Referans zaman -------------------------------------------------------------


def test_aktiflik_referans_zamana_bagli_deterministik() -> None:
    """Aynı sabit gönderiler, referans kaydırılınca aktiflik beklenen yönde değişir.

    Gönderiler 2026-07 civarı. REFERENCE_NOW'da pencere içinde → aktiflik>0. Referansı
    200 gün ileri alınca gönderiler 90 gün penceresinin dışına düşer → aktiflik 0.
    Test `currentDate`'e bağlı değil: iki referans da sabit.
    """
    acc = _account(posts=(_post(3), _post(10), _post(20)))
    yakin = activity_score(acc, REFERENCE_NOW)
    uzak = activity_score(acc, REFERENCE_NOW + timedelta(days=200))
    assert yakin > 0.0
    assert uzak == 0.0


def test_kesintisiz_kadans_uzun_sessizlikten_yuksek() -> None:
    """Düzenli postlayan hesap, aynı sayıda ama büyük boşluklu hesaptan yüksek aktiflik alır."""
    duzenli = _account(posts=tuple(_post(3 + i * 6) for i in range(8)))  # ~6 gün kadans
    bosluklu = _account(posts=(_post(3), _post(80)))  # 2 gönderi, ~77 gün sessizlik
    assert activity_score(duzenli, REFERENCE_NOW) > activity_score(bosluklu, REFERENCE_NOW)


# --- Kapasite -------------------------------------------------------------------


def test_kapasite_kategori_agirligi() -> None:
    """Yüksek-kapasite kategori (klinik) düşük-kapasiteden (florist) yüksek puan alır — aynı diğer sinyaller."""
    klinik = _account(category="dental_clinic")
    florist = _account(category="florist")
    assert capacity_score(klinik) > capacity_score(florist)


# --- Kohort<5 → watch -----------------------------------------------------------


def test_kohort_bes_altinda_potansiyel_none_watch() -> None:
    """Kategoride <5 taranmış hesap → potansiyel hesaplanmaz (None), hesap watch, birleşik None."""
    # 3 florist (kohort<5) + 5 cafe (kohort≥5) aynı batch.
    florists = [
        _account(business_id=i, snapshot_id=i, category="florist", posts=(_post(3 + i),))
        for i in range(1, 4)
    ]
    cafes = [
        _account(business_id=10 + i, snapshot_id=10 + i, category="cafe", posts=(_post(3 + i),))
        for i in range(1, 6)
    ]
    by_id = {r.business_id: r for r in score_accounts([*florists, *cafes], REFERENCE_NOW)}

    for f in florists:
        r = by_id[f.business_id]
        assert r.potential is None, "kohort<5 → potansiyel None olmalı"
        assert r.score is None
        assert r.status is TriageStatus.WATCH
    for c in cafes:
        r = by_id[c.business_id]
        assert r.potential is not None, "kohort≥5 → potansiyel hesaplanmalı"
        assert r.score is not None


def test_kohort_bes_ve_uzeri_potansiyel_hesaplaniyor() -> None:
    """Sınır: tam 5 taranmış hesap → kohort yeterli, potansiyel hesaplanır."""
    accs = [
        _account(business_id=i, snapshot_id=i, category="gym", posts=(_post(3 + i),))
        for i in range(1, 6)
    ]
    results = score_accounts(accs, REFERENCE_NOW)
    assert all(r.potential is not None for r in results)


def test_engagement_rate_takipci_yoksa_none() -> None:
    assert engagement_rate(_account(followers=None, posts=(_post(3),)), REFERENCE_NOW) is None
    assert engagement_rate(_account(followers=0, posts=(_post(3),)), REFERENCE_NOW) is None
    assert engagement_rate(_account(followers=1000, posts=()), REFERENCE_NOW) is None
