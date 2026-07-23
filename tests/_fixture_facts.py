"""Fixture'dan türetilen gerçekler — sayı-tabanlı testler magic number kullanmasın.

SEC-8 fixture'ı 20→100 hesaba büyüdü. Testler sabit sayı (14 handle, 2 fallback…)
yerine bu modülden türetir; fixture yeniden boyutlanınca testler kendiliğinden uyar.

Buradaki `ref_extract_handle` handle sözleşmesinin **bağımsız** referans uygulamasıdır
(production `api.core.extract_ig_handle`'ın kopyası değil). `test_handle_contract`
production'ı bu referansa karşı doğrular; diğer testler türetme için kullanır.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

# Sözleşme: host tam olarak (www.)instagram.com; alt alan adı / benzer ad eşleşmez.
_REF_IG_URL = re.compile(
    r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?$",
    re.IGNORECASE,
)
_RESERVED = frozenset({"p", "reel", "reels", "explore", "stories", "help", "about", "web"})


def ref_extract_handle(place: dict[str, Any]) -> str | None:
    """Bir place'in `websiteUri`'sinden sözleşmeye göre handle (bağımsız referans)."""
    url = place.get("websiteUri")
    if not url:
        return None
    m = _REF_IG_URL.match(url)
    if m is None:
        return None
    handle = m.group(1).lower()
    return handle if handle not in _RESERVED else None


@dataclass
class FixtureFacts:
    n_places: int
    handles: set[str]
    null_count: int
    categories: Counter[str]
    resolvable: set[str] = field(default_factory=set)
    fallback: set[str] = field(default_factory=set)

    @property
    def big_categories(self) -> list[str]:
        return [c for c, n in self.categories.items() if n >= 5]

    @property
    def small_categories(self) -> list[str]:
        return [c for c, n in self.categories.items() if n < 5]


def compute_facts(
    places_data: dict[str, Any],
    bd_profiles: dict[str, Any],
    apify_profiles: dict[str, Any],
) -> FixtureFacts:
    places = places_data["places"]
    handles = {h for p in places if (h := ref_extract_handle(p)) is not None}
    null_count = sum(1 for p in places if ref_extract_handle(p) is None)
    categories: Counter[str] = Counter(p["primaryType"] for p in places)
    # Bir handle çözülebilir: BD'de dolu yanıt VAR ya da Apify'da profili var.
    resolvable = {h for h in handles if bd_profiles.get(h) or h in apify_profiles}
    # Fallback: BD'de anahtar var ama boş {} (veri yok) ve Apify'da profili var.
    fallback = {
        h for h in handles if h in bd_profiles and not bd_profiles[h] and h in apify_profiles
    }
    return FixtureFacts(
        n_places=len(places),
        handles=handles,
        null_count=null_count,
        categories=categories,
        resolvable=resolvable,
        fallback=fallback,
    )
