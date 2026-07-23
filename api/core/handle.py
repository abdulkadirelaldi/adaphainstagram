"""IG handle çıkarımı — saf fonksiyon (TASKS "IG handle eşleme sözleşmesi").

Handle **yalnızca açık bir `instagram.com/{handle}` bağlantısından** türetilir; ad
benzerliğinden asla tahmin edilmez. Yanlış eşleme = yanlış işletmeye rapor = hukuki
sınır ihlali (CLAUDE.md). Bu yüzden regex kasıtlı olarak katıdır:

- Host **tam olarak** `instagram.com` veya `www.instagram.com` olmalı. Alt alan adları
  (`help.instagram.com`) ve benzer alan adları (`instagramm.example.com`) eşleşmez.
- `facebook.com/...` gibi başka platformlar, düz web siteleri eşleşmez.
- `p`, `reel`, `explore` gibi profil olmayan yollar handle sayılmaz.

Belirsizse handle yoktur (`None`) — işletme keşfedilir ama taranmaz.
"""

import re
from typing import Any

# Host'u ankraja bağlar: `://` hemen ardından (isteğe bağlı `www.`) `instagram.com/`.
# Böylece `help.instagram.com` (alt alan adı) ve `instagramm...` (benzer ad) elenir.
_IG_URL = re.compile(
    r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)",
    re.IGNORECASE,
)

# Instagram'ın profil olmayan yolları — handle değil.
_RESERVED = frozenset(
    {
        "p",
        "reel",
        "reels",
        "explore",
        "stories",
        "accounts",
        "about",
        "developer",
        "directory",
        "help",
        "web",
        "tv",
    }
)


def _iter_strings(value: Any) -> list[str]:
    """`raw` içindeki tüm string değerleri (iç içe dahil) düz bir listeye toplar."""
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(_iter_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_iter_strings(item))
    return found


def extract_ig_handle(raw: dict[str, Any]) -> str | None:
    """`raw` içindeki açık bir instagram profil URL'sinden handle çıkarır.

    Bulunamazsa `None`. Handle küçük harfe indirilir (IG kullanıcı adları büyük/küçük
    harfe duyarsız; fixture profilleri de küçük harf anahtarlı).
    """
    for text in _iter_strings(raw):
        match = _IG_URL.search(text)
        if match is None:
            continue
        handle = match.group(1).rstrip("/").lower()
        if handle and handle not in _RESERVED:
            return handle
    return None
