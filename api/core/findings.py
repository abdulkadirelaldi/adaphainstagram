"""Deterministik denetim bulgu motoru — SPEC §5. **LLM yok.**

Her bulgu deterministik bir kuraldan doğar (SPEC §5): kural + eşik + tetikleyen değer.
LLM bulgu **icat etmez** — bu motor bulguları üretir, BE-16 (Sonnet) sonra `message`
alanına ajans-dili çeviriyi yazar. Burada `message=None`.

Saf: dataclass alır, dataclass döndürür (httpx/SQLAlchemy yok, `now()` yok — referans
enjekte, BE-11 deseni). Ortak sinyal primitifleri `api/core/signals.py`'den (skorlama
ile paylaşılır, kopyalama yok).

**Üretilebilir 5 kural** (SPEC §5, TASKS "Faz 4 karara bağlananlar"):
Reels yok (kritik), Bio'da dönüşüm yolu yok (yüksek), Kadans düzensiz (orta),
CTA'sız caption (orta), Hashtag tekrarı (düşük).

**Dışarıda kalan 2 kural** — kural 7 "ölçmediğini iddia etme" gereği üretilmez:
- *Yorum yanıtsız* (yüksek): yanıtsız yorum oranı ister; yorum-düzeyi "kim yanıtladı"
  verisi sistemde yok (`posts` yalnız `comment_count`). Faz 5+ Apify yorum çekiminde.
- *Görsel tutarsızlık* (düşük): baskın renk kümesi gerçek görüntü indirmeyi ister;
  fixture'da görüntü yok, canlı indirme kural 6'ya aykırı. Ertelenir.
Bu motorda hiç yer almazlar.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from api.core.signals import (
    PostData,
    cta_ratio,
    has_cta,
    hashtags_of,
    longest_silence_days,
    posts_in_window,
    reels_ratio,
)
from api.models.enums import Severity

# Denetim penceresi (SPEC §5 "90 günde ...").
AUDIT_WINDOW_DAYS = 90

# Eşikler (SPEC §5).
_REELS_MIN_RATIO = 0.10  # < %10 Reels → tetikler
_SILENCE_MAX_DAYS = 14  # en uzun sessizlik > 14 gün → tetikler
_CTA_MIN_RATIO = 0.20  # CTA'lı gönderi < %20 → tetikler
_HASHTAG_REPEAT_RATIO = 0.70  # aynı set > %70 → tetikler

# Önem → görünürlük cezası. Sıralama SPEC §5'ten (kritik>yüksek>orta>düşük); sayılar
# seçim: bir kritik tek başına belirgin düşürür, hepsi tetiklenince skor açıkça düşer.
# Toplam maksimum ceza (5 kural) = 35+22+12+12+5 = 86 → skor 14.
_PENALTY: dict[Severity, float] = {
    Severity.CRITICAL: 35.0,
    Severity.HIGH: 22.0,
    Severity.MEDIUM: 12.0,
    Severity.LOW: 5.0,
}


@dataclass(frozen=True)
class Finding:
    """Tek denetim bulgusu → `docs/openapi.yaml` `Finding`. `message` LLM'e ait (BE-16), burada None."""

    rule: str
    title: str
    severity: Severity
    detail: str
    message: str | None = None


@dataclass(frozen=True)
class AuditAccount:
    """Denetlenecek hesabın deterministik girdisi (son snapshot + gönderiler + iletişim)."""

    posts: Sequence[PostData] = field(default_factory=tuple)
    external_url: str | None = None  # snapshots.external_url (bio linki)
    phone: str | None = None  # businesses.phone
    biography: str | None = None  # snapshots.biography


def _pct(ratio: float) -> int:
    return round(ratio * 100)


def _rule_reels(window: Sequence[PostData]) -> Finding | None:
    ratio = reels_ratio(window)
    if ratio is None or ratio >= _REELS_MIN_RATIO:
        return None
    return Finding(
        rule="reels_yok",
        title="Reels yok",
        severity=Severity.CRITICAL,
        detail=f"Son 90 günde Reels oranı %{_pct(ratio)} (eşik <%10).",
    )


def _rule_bio(account: AuditAccount) -> Finding | None:
    has_link = bool(account.external_url)
    has_phone = bool(account.phone)
    has_bio_cta = has_cta(account.biography)
    if has_link or has_phone or has_bio_cta:
        return None
    return Finding(
        rule="bio_donusum_yok",
        title="Bio'da dönüşüm yolu yok",
        severity=Severity.HIGH,
        detail="Bio'da link, telefon ve CTA'nın üçü de yok.",
    )


def _rule_cadence(window: Sequence[PostData], reference_now: datetime) -> Finding | None:
    if not window:
        return None
    silence = longest_silence_days(window, reference_now)
    if silence <= _SILENCE_MAX_DAYS:
        return None
    return Finding(
        rule="kadans_duzensiz",
        title="Kadans düzensiz",
        severity=Severity.MEDIUM,
        detail=f"En uzun sessizlik {round(silence)} gün (eşik >14).",
    )


def _rule_cta(window: Sequence[PostData]) -> Finding | None:
    ratio = cta_ratio(window)
    if ratio is None or ratio >= _CTA_MIN_RATIO:
        return None
    return Finding(
        rule="cta_yok",
        title="CTA'sız caption",
        severity=Severity.MEDIUM,
        detail=f"CTA içeren gönderi oranı %{_pct(ratio)} (eşik <%20).",
    )


def _rule_hashtag(window: Sequence[PostData]) -> Finding | None:
    if not window:
        return None
    # Aynı hashtag setinin (boş olmayan) gönderilerin >%70'inde tekrarı.
    sets = [hashtags_of(p.caption) for p in window]
    counts = Counter(s for s in sets if s)
    if not counts:
        return None
    top_set, top_count = counts.most_common(1)[0]
    ratio = top_count / len(window)
    if ratio <= _HASHTAG_REPEAT_RATIO:
        return None
    tags = " ".join(f"#{t}" for t in sorted(top_set))
    return Finding(
        rule="hashtag_tekrari",
        title="Hashtag tekrarı",
        severity=Severity.LOW,
        detail=f"Aynı hashtag seti ({tags}) gönderilerin %{_pct(ratio)}'inde (eşik >%70).",
    )


def evaluate_findings(account: AuditAccount, reference_now: datetime) -> list[Finding]:
    """Beş kuralı deterministik uygular; tetiklenen bulguları döndürür (SPEC §5)."""
    window = posts_in_window(account.posts, reference_now, AUDIT_WINDOW_DAYS)
    candidates = [
        _rule_reels(window),
        _rule_bio(account),
        _rule_cadence(window, reference_now),
        _rule_cta(window),
        _rule_hashtag(window),
    ]
    return [finding for finding in candidates if finding is not None]


def visibility_score(findings: Sequence[Finding]) -> float:
    """Görünürlük skoru = 100 − tetiklenen bulguların ağırlıklı cezası, 0'a kırpılı (SPEC §5).

    Hiç bulgu yok → 100. Bulgu ne kadar ağır/çoksa skor o kadar düşük.
    """
    penalty = sum(_PENALTY[f.severity] for f in findings)
    return max(0.0, 100.0 - penalty)
