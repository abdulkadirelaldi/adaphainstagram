"""Deterministik gönderi-analizi primitifleri — skorlama (BE-11) ve bulgular (BE-14) paylaşır.

Bu ilkel işlevler tek kaynakta durur ki iki motor (skorlama, bulgu) aynı CTA tespitini,
aktiflik penceresini ve sessizlik hesabını **kopyalamadan** kullansın (SPEC §4/§5 aynı
sinyalleri farklı eşiklerle okur). Saf: dataclass alır, sayı/liste döndürür.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

# Reels sayılan medya tipleri (IG BD `VIDEO`, Apify `Video`, olası `REELS`).
REELS_TYPES = frozenset({"VIDEO", "REELS", "Video"})

# CTA tespiti — deterministik anahtar kelime (Faz 3/4 LLM kullanamaz; nitelikli tespit
# Faz 4 Haiku'nun işi). Küçük harfe indirilmiş metinde aranır.
CTA_KEYWORDS = (
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

_HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)


@dataclass(frozen=True)
class PostData:
    """Skorlamaya/bulguya giren tek gönderi (SPEC §3 `posts` alt kümesi)."""

    posted_at: datetime
    media_type: str | None = None
    caption: str | None = None
    like_count: int | None = None
    comment_count: int | None = None


def has_cta(caption: str | None) -> bool:
    """Caption/bio deterministik CTA anahtar kelimesi içeriyor mu."""
    if not caption:
        return False
    lowered = caption.lower()
    return any(keyword in lowered for keyword in CTA_KEYWORDS)


def posts_in_window(
    posts: Sequence[PostData], reference_now: datetime, window_days: int
) -> list[PostData]:
    """`reference_now`'dan geriye `window_days` gün içindeki gönderiler."""
    start = reference_now - timedelta(days=window_days)
    return [p for p in posts if start <= p.posted_at <= reference_now]


def longest_silence_days(window_posts: Sequence[PostData], reference_now: datetime) -> float:
    """En uzun sessizlik: ardışık gönderiler arası + son gönderiden referansa kadar (gün).

    Pencere başlangıcından ilk gönderiye kadar olan boşluk sayılmaz — yeni başlamış
    hesabı cezalandırmayız; dormantlık son gönderiden bugüne olan sessizlikle yakalanır.
    Boş listede 0 döner (çağıran boş pencereyi ayrıca ele alır).
    """
    if not window_posts:
        return 0.0
    times = sorted(p.posted_at for p in window_posts)
    gaps = [(times[i + 1] - times[i]).total_seconds() / 86400 for i in range(len(times) - 1)]
    gaps.append((reference_now - times[-1]).total_seconds() / 86400)
    return max(gaps)


def reels_ratio(posts: Sequence[PostData]) -> float | None:
    """Reels (video) oranı. Gönderi yoksa `None`."""
    if not posts:
        return None
    reels = sum(1 for p in posts if p.media_type in REELS_TYPES)
    return reels / len(posts)


def cta_ratio(posts: Sequence[PostData]) -> float | None:
    """CTA içeren gönderi oranı. Gönderi yoksa `None`."""
    if not posts:
        return None
    return sum(1 for p in posts if has_cta(p.caption)) / len(posts)


def hashtags_of(caption: str | None) -> frozenset[str]:
    """Caption'daki hashtag'lerin küçük harfli kümesi."""
    if not caption:
        return frozenset()
    return frozenset(tag.lower() for tag in _HASHTAG_RE.findall(caption))
