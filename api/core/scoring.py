"""Triyaj skorlama — saf, deterministik, **LLM yok** (SPEC §4, Faz 3).

Bu modül CLAUDE.md mimari kuralına göre saftır: dataclass alır, dataclass döndürür;
httpx/SQLAlchemy import etmez, `datetime.now()` çağırmaz. "Şimdi" referansı **enjekte**
edilir (üretimde `now`, testte `REFERENCE_NOW=2026-07-15`) — böylece skorlama DB ve
takvim gününden bağımsız test edilir.

Üç alt skor (0–100), sonra ağırlıklı **çarpım** birleşik skor:

    score = 100 * (activity/100)^0.30 * (potential/100)^0.40 * (capacity/100)^0.30

Çarpım seçildi (SPEC §4): bir alt skor 0'a yaklaşınca birleşik **çöker** — ölü ama
potansiyelli hesap qualified olmamalı.

**Potansiyel: dört değil ÜÇ sinyal.** SPEC §4 dört sinyal sayar ama dördüncüsü (yorum
yanıt oranı) bu sistemde **ölçülemez**: `posts` yalnız `comment_count` taşır, "kim
yanıtladı" verisi Faz 2'de çekilmedi (SPEC §3 modelinde yok). Kural 7 gereği (ölçmediğini
iddia etme) bu sinyal Faz 3'te skora **sokulmaz**; potansiyel, ölçülebilen üç sinyalin
(Reels yokluğu, kohort medyanına göre etkileşim düşüklüğü, CTA yokluğu) ortalamasıdır.
Yorum-yanıt sinyali Faz 4'te Apify yorum çekimi gelince eklenir.

Etkileşim için **mutlak eşik yok** (SPEC §4): karşılaştırma daima aynı kategorideki
taranmış hesapların medyanına göre. Kohort<5 → potansiyel hesaplanmaz, hesap `watch`.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import median

from api.models.enums import TriageStatus

# --- Ayarlanabilir sabitler (SPEC §4 niyetinin sayısal karşılığı) ---------------

ACTIVITY_WINDOW_DAYS = 90
_WEEKLY_TARGET = 2.0  # haftada 2+ gönderi → tam frekans (SPEC §4)
_SILENCE_OK_DAYS = 14  # <14 gün en uzun sessizlik → tam kadans (SPEC §4)
_ACT_W_FREQ = 0.35  # aktiflikte frekans ağırlığı
_ACT_W_CADENCE = 0.65  # aktiflikte kadans (düzenlilik) ağırlığı — daha güçlü canlılık sinyali

MIN_COHORT = 5  # kohort<5 → potansiyel hesaplanmaz (SPEC §4)

# Kapasite kategori ağırlıkları (SPEC §4: klinik/kuyumcu/oto galeri/emlak yüksek;
# hobi/kişisel düşük). Bilinmeyen kategori nötr.
_CATEGORY_WEIGHT: dict[str, float] = {
    "dental_clinic": 1.0,
    "jewelry_store": 1.0,
    "car_dealer": 1.0,
    "real_estate_agency": 1.0,
    "restaurant": 0.6,
    "cafe": 0.6,
    "hair_salon": 0.6,
    "beauty_salon": 0.6,
    "gym": 0.6,
    "florist": 0.3,
    "gift_shop": 0.3,
    "pet_store": 0.3,
}
_CATEGORY_WEIGHT_UNKNOWN = 0.5
_FOLLOWER_TARGET = 4000  # bu ve üstü → tam takipçi puanı
_RATING_TARGET = 250  # bu ve üstü → tam değerlendirme puanı

# Kapasite alt ağırlıkları (kategori en güçlü sinyal; ödeme gücünü o belirler).
_CAP_W_CATEGORY = 0.40
_CAP_W_FOLLOWERS = 0.20
_CAP_W_WEBSITE = 0.20
_CAP_W_RATING = 0.20

# CTA tespiti — deterministik anahtar kelime (Faz 3 LLM kullanamaz; nitelikli tespit
# Faz 4 Haiku'nun işi). Küçük harfe indirilmiş caption'da aranır.
_CTA_KEYWORDS = (
    "dm",
    "mesaj",
    "ara",
    "arayın",
    "sipariş",
    "siparis",
    "link",
    "whatsapp",
    "wp",
    "randevu",
    "rezervasyon",
    "iletişim",
    "iletisim",
    "bilgi için",
    "detaylı bilgi",
)

_REELS_TYPES = frozenset({"VIDEO", "REELS", "Video"})


# --- Girdi/çıktı dataclass'ları -------------------------------------------------


@dataclass(frozen=True)
class PostData:
    """Skorlamaya giren tek gönderi (SPEC §3 `posts` alt kümesi)."""

    posted_at: datetime
    media_type: str | None = None
    caption: str | None = None
    like_count: int | None = None
    comment_count: int | None = None


@dataclass(frozen=True)
class AccountData:
    """Bir işletmenin skorlanabilir hâli — son snapshot + gönderileri + Places sinyalleri."""

    business_id: int
    snapshot_id: int
    category: str | None
    rating_count: int | None
    has_website: bool
    followers: int | None
    posts: Sequence[PostData] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScoreResult:
    """Bir hesabın triyaj sonucu → `triage_scores` satırı."""

    business_id: int
    snapshot_id: int
    activity: float
    capacity: float
    potential: float | None  # kohort<5 → None
    score: float | None  # potansiyel None ise None
    status: TriageStatus


# --- Yardımcılar ---------------------------------------------------------------


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _posts_in_window(posts: Sequence[PostData], reference_now: datetime) -> list[PostData]:
    start = reference_now - timedelta(days=ACTIVITY_WINDOW_DAYS)
    return [p for p in posts if start <= p.posted_at <= reference_now]


def _longest_silence_days(window_posts: Sequence[PostData], reference_now: datetime) -> float:
    """En uzun sessizlik: ardışık gönderiler arası + son gönderiden referansa kadar.

    Pencere başlangıcından ilk gönderiye kadar olan boşluk **sayılmaz** — yeni
    başlamış bir hesabı geçmişte var olmadığı için cezalandırmayız; dormantlık son
    gönderiden bugüne olan sessizlikle yakalanır.
    """
    times = sorted(p.posted_at for p in window_posts)
    gaps = [(times[i + 1] - times[i]).total_seconds() / 86400 for i in range(len(times) - 1)]
    gaps.append((reference_now - times[-1]).total_seconds() / 86400)
    return max(gaps)


# --- Alt skorlar ---------------------------------------------------------------


def activity_score(account: AccountData, reference_now: datetime) -> float:
    """Aktiflik 0–100: son 90 gün gönderi sıklığı + en uzun sessizlik.

    0 gönderi → 0 (SPEC §4; çarpımı çökertir → ölü hesap rejected). Frekans ve kadans
    ortalanır; ikisi de iyiyse (2+/hafta, <14 gün sessizlik) 100'e yaklaşır.
    """
    window = _posts_in_window(account.posts, reference_now)
    if not window:
        return 0.0

    weekly_rate = len(window) / (ACTIVITY_WINDOW_DAYS / 7)
    freq = _clamp(weekly_rate / _WEEKLY_TARGET)

    silence = _longest_silence_days(window, reference_now)
    if silence < _SILENCE_OK_DAYS:
        cadence = 1.0
    else:
        span = ACTIVITY_WINDOW_DAYS - _SILENCE_OK_DAYS
        cadence = _clamp(1.0 - (silence - _SILENCE_OK_DAYS) / span)

    # Kadans (düzenli mi postluyor) ağırlıklı: "en uzun sessizlik" hesabın canlı olup
    # olmadığının daha güçlü göstergesi. Frekans tavanı gerçekçi hesap hacminde düşük
    # kalır; kadans, düzenli ama az postlayan canlı hesabı hak ettiği yere taşır.
    return 100.0 * (_ACT_W_FREQ * freq + _ACT_W_CADENCE * cadence)


def engagement_rate(account: AccountData, reference_now: datetime) -> float | None:
    """(like+comment)/followers, pencere gönderileri üzerinden ortalama.

    Kohort medyanı bu orandan hesaplanır. Takipçi yok/0 veya pencerede gönderi yok →
    hesaplanamaz (`None`); bu hesap kohort medyanına katılmaz.
    """
    if not account.followers or account.followers <= 0:
        return None
    window = _posts_in_window(account.posts, reference_now)
    if not window:
        return None
    rates = [((p.like_count or 0) + (p.comment_count or 0)) / account.followers for p in window]
    return sum(rates) / len(rates)


def _has_cta(caption: str | None) -> bool:
    if not caption:
        return False
    lowered = caption.lower()
    return any(keyword in lowered for keyword in _CTA_KEYWORDS)


def potential_score(
    account: AccountData,
    reference_now: datetime,
    cohort_engagement_median: float | None,
) -> float:
    """Potansiyel 0–100: yüksek = kötü yönetim = bizim için iyi. ÜÇ sinyalin ortalaması.

    1) Reels yokluğu: 1 - reels oranı (hiç Reels yok → 1.0).
    2) Etkileşim düşüklüğü: kohort medyanına göre. Medyanın altı → yüksek sinyal.
       Mutlak eşik yok (SPEC §4). Medyan yoksa (veri yetersiz) bu sinyal atlanır.
    3) CTA yokluğu: CTA içermeyen gönderi oranı.
    """
    signals: list[float] = []

    all_posts = list(account.posts)
    if all_posts:
        reels = sum(1 for p in all_posts if p.media_type in _REELS_TYPES)
        signals.append(1.0 - reels / len(all_posts))
        cta_posts = sum(1 for p in all_posts if _has_cta(p.caption))
        signals.append(1.0 - cta_posts / len(all_posts))
    else:
        # Gönderi yok → Reels de CTA da yok → iki sinyal de tam yüksek.
        signals.extend((1.0, 1.0))

    eng = engagement_rate(account, reference_now)
    if cohort_engagement_median is not None and cohort_engagement_median > 0:
        # Hesabın etkileşimi yoksa 0 kabul → medyanın çok altında → yüksek sinyal.
        rate = eng if eng is not None else 0.0
        signals.append(_clamp((cohort_engagement_median - rate) / cohort_engagement_median))

    return 100.0 * (sum(signals) / len(signals))


def capacity_score(account: AccountData) -> float:
    """Kapasite 0–100: ödeyebilir mi. Kategori ağırlığı + takipçi + website + rating."""
    category = account.category
    weight = (
        _CATEGORY_WEIGHT.get(category, _CATEGORY_WEIGHT_UNKNOWN)
        if category
        else _CATEGORY_WEIGHT_UNKNOWN
    )

    followers = _clamp((account.followers or 0) / _FOLLOWER_TARGET)
    website = 1.0 if account.has_website else 0.0
    rating = _clamp((account.rating_count or 0) / _RATING_TARGET)

    return 100.0 * (
        _CAP_W_CATEGORY * weight
        + _CAP_W_FOLLOWERS * followers
        + _CAP_W_WEBSITE * website
        + _CAP_W_RATING * rating
    )


# --- Birleşik skor + durum ------------------------------------------------------


def combined_score(activity: float, potential: float, capacity: float) -> float:
    """Ağırlıklı çarpım (SPEC §4). Bir alt skor 0 → birleşik 0."""
    # float(...): mypy'de `float ** float` overload'ı Any döndürüyor (negatif taban +
    # kesirli üs complex olabilir); alt skorlar 0–100 olduğu için sonuç daima reel.
    return float(
        100.0 * (activity / 100) ** 0.30 * (potential / 100) ** 0.40 * (capacity / 100) ** 0.30
    )


def assign_status(score: float) -> TriageStatus:
    """Skordan durum (SPEC §1): <40 rejected, 40–69 watch, ≥70 qualified."""
    if score < 40:
        return TriageStatus.REJECTED
    if score < 70:
        return TriageStatus.WATCH
    return TriageStatus.QUALIFIED


# --- Batch skorlama (iki geçişli — kohort medyanı) ------------------------------


def score_accounts(accounts: Sequence[AccountData], reference_now: datetime) -> list[ScoreResult]:
    """Bir batch hesabı skorlar. İki geçiş: önce kategori etkileşim medyanları, sonra skor.

    Etkileşim karşılaştırması izole hesapla yapılamaz (SPEC §4) — bu yüzden batch.
    Kohort<5 (kategoride etkileşimi hesaplanabilen hesap sayısı) → potansiyel None,
    hesap `watch`, birleşik skor yok.
    """
    # 1. geçiş: kategori bazında etkileşim oranlarını topla.
    rates_by_category: dict[str | None, list[float]] = {}
    for account in accounts:
        rate = engagement_rate(account, reference_now)
        if rate is not None:
            rates_by_category.setdefault(account.category, []).append(rate)

    median_by_category = {category: median(rates) for category, rates in rates_by_category.items()}
    # Kohort = kategorideki **taranmış hesap** sayısı (SPEC §4 "aynı kategorideki
    # taranmış hesaplar"). Etkileşimi hesaplanabilen sayı DEĞİL: ölü (0 gönderi)
    # hesaplar kategoriyi küçültüp büyük kategorileri yanlışlıkla kohort<5'e itmesin.
    # Medyan yine yalnız hesaplanabilir oranlardan çıkar.
    cohort_size = Counter(account.category for account in accounts)

    # 2. geçiş: her hesabı skorla.
    results: list[ScoreResult] = []
    for account in accounts:
        activity = activity_score(account, reference_now)
        capacity = capacity_score(account)

        if cohort_size.get(account.category, 0) < MIN_COHORT:
            # Kohort<5 → potansiyel hesaplanmaz → watch, birleşik skor yok.
            results.append(
                ScoreResult(
                    business_id=account.business_id,
                    snapshot_id=account.snapshot_id,
                    activity=round(activity, 2),
                    capacity=round(capacity, 2),
                    potential=None,
                    score=None,
                    status=TriageStatus.WATCH,
                )
            )
            continue

        potential = potential_score(
            account, reference_now, median_by_category.get(account.category)
        )
        score = combined_score(activity, potential, capacity)
        results.append(
            ScoreResult(
                business_id=account.business_id,
                snapshot_id=account.snapshot_id,
                activity=round(activity, 2),
                capacity=round(capacity, 2),
                potential=round(potential, 2),
                score=round(score, 2),
                status=assign_status(score),
            )
        )

    return results
