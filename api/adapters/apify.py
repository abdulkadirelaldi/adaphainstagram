"""Apify Instagram Scraper profil adaptörü (SPEC §2).

Business Discovery çalışmazsa yedek profil kaynağıdır. Apify çok daha fazla alan
döndürür — özellikle CLAUDE.md kural 7'nin yasakladığı erişim/gösterim/kaydetme
metrikleri ile takipçi demografisi. Ham alan adları `tests/fixtures/README.md`'de
listeli. Normalize katmanı bu alanları **okumaz**: yalnızca SPEC §3'e düşürülebilir
alanları alır, gerisi `raw`'da arşive kalır ama normalize yüzeye asla çıkmaz.
`NormalizedProfile`/`NormalizedPost` `extra="forbid"` olduğu için yanlışlıkla
taşınırsa doğrulama patlar — bu bir güvenlik ağı, birincil savunma alanı bilerek
düşürmektir.

HTTP client enjekte edilebilir (test fixture; canlı çağrı yok, kural 6).
"""

from typing import Any

import httpx

from api.adapters.base import (
    NormalizedPost,
    NormalizedProfile,
    ProfileUnavailableError,
    parse_ig_timestamp,
    register_profile,
)
from api.config import get_settings

_APIFY_BASE = "https://api.apify.com/v2"
_TIMEOUT = httpx.Timeout(30.0)


def _normalize_post(post: dict[str, Any]) -> NormalizedPost:
    # Yalnızca izin verilen alanlar okunur. Gönderi düzeyindeki erişim/gösterim/
    # kaydetme metrikleri ve yorum metni BİLEREK okunmaz — raw'da kalır, normalize
    # yüzeye çıkmaz (kural 7).
    return NormalizedPost(
        ig_id=post["id"],
        media_type=post.get("type"),
        caption=post.get("caption"),
        like_count=post.get("likesCount"),
        comment_count=post.get("commentsCount"),
        # videoViewCount yalnız videoda; yoksa None.
        view_count=post.get("videoViewCount"),
        posted_at=parse_ig_timestamp(post["timestamp"]),
        permalink=post.get("url"),
        thumb_url=post.get("displayUrl"),
    )


def normalize_apify(raw: dict[str, Any]) -> NormalizedProfile:
    """Ham Apify çıktısını `NormalizedProfile`'a çevirir; yasak metrikleri düşürür."""
    posts = [_normalize_post(p) for p in raw.get("latestPosts", [])]

    # Profil düzeyinde de yalnızca izin verilen alanlar; erişim/gösterim/kaydetme
    # metrikleri, profil ziyareti ve takipçi demografisi okunmaz.
    return NormalizedProfile(
        source="apify",
        followers=raw.get("followersCount"),
        follows=raw.get("followsCount"),
        media_count=raw.get("postsCount"),
        biography=raw.get("biography"),
        external_url=raw.get("externalUrl"),
        is_professional=raw.get("isBusinessAccount"),
        posts=posts,
        raw=raw,
    )


@register_profile("apify")
class ApifyAdapter:
    source_name = "apify"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        token: str | None = None,
        actor_id: str = "apify~instagram-profile-scraper",
    ) -> None:
        self._client = client
        self._token = token
        self._actor_id = actor_id

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        raw = await self._fetch(handle)
        if not raw:
            raise ProfileUnavailableError(f"Apify {handle} için veri döndürmedi.")
        return normalize_apify(raw)

    async def _fetch(self, handle: str) -> dict[str, Any]:
        if self._client is not None:
            response = await self._client.post(self._url(), json=self._payload(handle))
            response.raise_for_status()
            items: list[dict[str, Any]] = response.json()
            return items[0] if items else {}

        token = self._token or get_settings().apify_token
        if not token:
            raise RuntimeError("Apify token yok: APIFY_TOKEN tanımlı değil.")
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                self._url(), params={"token": token}, json=self._payload(handle)
            )
            response.raise_for_status()
            items = response.json()
            return items[0] if items else {}

    def _url(self) -> str:
        # Actor'ı senkron çalıştırıp öğeleri döndüren uç.
        return f"{_APIFY_BASE}/acts/{self._actor_id}/run-sync-get-dataset-items"

    def _payload(self, handle: str) -> dict[str, Any]:
        return {"usernames": [handle], "resultsLimit": 30}
