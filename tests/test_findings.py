"""SEC-9 blok 1 — deterministik bulgu motoru (api/core/findings.py, SPEC §5).

DB'siz saf testler. Beş kuralın her biri eşiğinde tetikleniyor/tetiklenmiyor (off-by-one);
dışarıda kalan iki kural (yorum yanıtsız, görsel tutarsızlık) hiçbir hesapta üretilmiyor
(kural 7 kararı, regresyon); görünürlük skoru deterministik.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.core.findings import (
    AuditAccount,
    evaluate_findings,
    visibility_score,
)
from api.core.signals import PostData
from api.models.enums import Severity

REFERENCE_NOW = datetime(2026, 7, 15, 0, 0, 0, tzinfo=UTC)

# Motorun üretebileceği kural kimlikleri (SPEC §5'in 5 üretilebilir kuralı).
PRODUCIBLE_RULES = {"reels_yok", "bio_donusum_yok", "kadans_duzensiz", "cta_yok", "hashtag_tekrari"}
# Kural 7 kararıyla motorda HİÇ olmaması gereken iki kural.
EXCLUDED_RULES = {"yorum_yanitsiz", "gorsel_tutarsizlik"}


def _post(
    days_ago: int,
    *,
    media_type: str = "IMAGE",
    caption: str = "gunluk paylasim",
    ig_id: str = "1",
) -> PostData:
    return PostData(
        posted_at=REFERENCE_NOW - timedelta(days=days_ago),
        media_type=media_type,
        caption=caption,
        ig_id=ig_id,
    )


def _rules(account: AuditAccount) -> set[str]:
    return {f.rule for f in evaluate_findings(account, REFERENCE_NOW)}


# --- Reels < %10 (kritik) — eşik sınırı -----------------------------------------


def test_reels_esik_tam_yuzde_on_tetiklemez() -> None:
    """1 video / 10 gönderi = %10 tam → tetiklemez (eşik <%10, `>=` muaf)."""
    posts = [_post(3 + i, media_type="IMAGE", caption="a", ig_id=str(i)) for i in range(9)]
    posts.append(_post(2, media_type="VIDEO", caption="a", ig_id="9"))
    # CTA olsun ki cta_yok tetiklenmesin, hashtag yok, kadans kısa.
    posts = [
        PostData(
            posted_at=p.posted_at, media_type=p.media_type, caption="randevu icin dm", ig_id=p.ig_id
        )
        for p in posts
    ]
    assert "reels_yok" not in _rules(AuditAccount(posts=posts, external_url="x"))


def test_reels_esik_altinda_tetikler() -> None:
    """1 video / 11 gönderi ≈ %9.09 (<%10) → tetikler."""
    posts = [
        _post(
            2 + i,
            media_type=("VIDEO" if i == 0 else "IMAGE"),
            caption="randevu icin dm",
            ig_id=str(i),
        )
        for i in range(11)
    ]
    assert "reels_yok" in _rules(AuditAccount(posts=posts, external_url="x"))


# --- Bio: link + tel + CTA üçü de yok (yüksek) ----------------------------------


def test_bio_ucu_de_yoksa_tetikler() -> None:
    acc = AuditAccount(posts=[_post(3)], external_url=None, phone=None, biography="kahve dukkani")
    assert "bio_donusum_yok" in _rules(acc)


def test_bio_biri_varsa_tetiklemez() -> None:
    # Link var.
    assert "bio_donusum_yok" not in _rules(
        AuditAccount(posts=[_post(3)], external_url="https://x.example", phone=None, biography="a")
    )
    # Telefon var.
    assert "bio_donusum_yok" not in _rules(
        AuditAccount(posts=[_post(3)], external_url=None, phone="0362", biography="a")
    )
    # Bio'da CTA var.
    assert "bio_donusum_yok" not in _rules(
        AuditAccount(posts=[_post(3)], external_url=None, phone=None, biography="randevu icin dm")
    )


# --- Kadans: en uzun sessizlik > 14 gün (orta) — eşik sınırı --------------------


def test_kadans_tam_ondort_gun_tetiklemez() -> None:
    """Tek gönderi 14 gün önce → sessizlik tam 14 → tetiklemez (eşik >14, `<=` muaf)."""
    acc = AuditAccount(posts=[_post(14, caption="randevu icin dm")], external_url="x")
    assert "kadans_duzensiz" not in _rules(acc)


def test_kadans_onbes_gun_tetikler() -> None:
    acc = AuditAccount(posts=[_post(15, caption="randevu icin dm")], external_url="x")
    assert "kadans_duzensiz" in _rules(acc)


# --- CTA'lı gönderi oranı < %20 (orta) — eşik sınırı ----------------------------


def test_cta_tam_yuzde_yirmi_tetiklemez() -> None:
    """2 CTA'lı / 10 gönderi = %20 tam → tetiklemez (eşik <%20)."""
    posts = [
        _post(
            2 + i, media_type="VIDEO", caption=("randevu dm" if i < 2 else "gunluk"), ig_id=str(i)
        )
        for i in range(10)
    ]
    assert "cta_yok" not in _rules(AuditAccount(posts=posts, external_url="x"))


def test_cta_altinda_tetikler() -> None:
    """1 CTA'lı / 10 = %10 (<%20) → tetikler."""
    posts = [
        _post(
            2 + i, media_type="VIDEO", caption=("randevu dm" if i < 1 else "gunluk"), ig_id=str(i)
        )
        for i in range(10)
    ]
    assert "cta_yok" in _rules(AuditAccount(posts=posts, external_url="x"))


# --- Hashtag tekrarı > %70 (düşük) — eşik sınırı --------------------------------


def test_hashtag_tam_yuzde_yetmis_tetiklemez() -> None:
    """Aynı set 7/10 = %70 tam → tetiklemez (eşik >%70)."""
    posts = [
        _post(
            2 + i,
            media_type="VIDEO",
            caption=("#kahve #samsun randevu dm" if i < 7 else "farkli dm"),
            ig_id=str(i),
        )
        for i in range(10)
    ]
    assert "hashtag_tekrari" not in _rules(AuditAccount(posts=posts, external_url="x"))


def test_hashtag_ustunde_tetikler() -> None:
    """Aynı set 8/10 = %80 (>%70) → tetikler."""
    posts = [
        _post(
            2 + i,
            media_type="VIDEO",
            caption=("#kahve #samsun randevu dm" if i < 8 else "farkli dm"),
            ig_id=str(i),
        )
        for i in range(10)
    ]
    assert "hashtag_tekrari" in _rules(AuditAccount(posts=posts, external_url="x"))


# --- Dışarıda kalan 2 kural — regresyon (kural 7) -------------------------------


def test_dislanan_kurallar_hicbir_hesapta_uretilmiyor() -> None:
    """'yorum_yanitsiz' ve 'gorsel_tutarsizlik' hiçbir konfigürasyonda Finding üretmemeli.

    Regresyon: biri motora geri sızarsa (kural 7 ihlali) bu test kırmızıya döner.
    """
    accounts = [
        AuditAccount(posts=[], external_url=None, phone=None, biography=None),  # ölü + boş bio
        AuditAccount(
            posts=[_post(30, media_type="IMAGE", caption="#a #b", ig_id=str(i)) for i in range(20)],
            external_url=None,
            phone=None,
            biography="a",
        ),
        AuditAccount(
            posts=[_post(2, media_type="VIDEO", caption="randevu dm")],
            external_url="https://x.example",
            phone="0362",
            biography="randevu",
        ),
    ]
    produced: set[str] = set()
    for acc in accounts:
        produced |= _rules(acc)
    # Üretilenlerin tamamı üretilebilir kümede; dışlananlardan hiçbiri yok.
    assert produced <= PRODUCIBLE_RULES
    assert not (produced & EXCLUDED_RULES)


# --- Görünürlük skoru deterministik ---------------------------------------------


def test_hic_bulgu_yoksa_skor_yuz() -> None:
    assert visibility_score([]) == 100.0


def test_skor_deterministik_ayni_hesap_ayni_skor() -> None:
    acc = AuditAccount(posts=[_post(40, media_type="IMAGE", caption="gunluk")], external_url=None)
    f1 = evaluate_findings(acc, REFERENCE_NOW)
    f2 = evaluate_findings(acc, REFERENCE_NOW)
    assert visibility_score(f1) == visibility_score(f2)


def test_skor_bulgu_arttikca_dusuyor() -> None:
    """Daha çok/ağır bulgu → daha düşük skor (ağırlıklı ceza)."""
    temiz = AuditAccount(
        posts=[_post(2 + i, media_type="VIDEO", caption="randevu dm #x") for i in range(10)],
        external_url="https://x.example",
        phone="0362",
        biography="randevu",
    )
    kotu = AuditAccount(posts=[], external_url=None, phone=None, biography="kahve")
    assert visibility_score(evaluate_findings(kotu, REFERENCE_NOW)) < visibility_score(
        evaluate_findings(temiz, REFERENCE_NOW)
    )


def test_ceza_haritasi_tum_onemleri_kapsiyor() -> None:
    """Her Severity için ceza tanımlı — bir kural eklenip cezasız kalırsa KeyError yakalanır."""
    from api.core.findings import _PENALTY

    assert set(_PENALTY) == set(Severity)
