"""IG Business Discovery profil adaptörü (SPEC §2).

IG Graph API `business_discovery` yanıtını `NormalizedProfile`'a çevirir. Tercih edilen
profil kaynağıdır; hesap işletme/creator değilse veya BD boş dönerse
`ProfileUnavailableError` yükseltir ve profil servisi Apify'a düşer (fallback).

HTTP client enjekte edilebilir (test fixture; canlı çağrı yok, kural 6). Normalize saf
fonksiyondur (`normalize_business_discovery`).
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

_GRAPH_BASE = "https://graph.facebook.com/v21.0"
_TIMEOUT = httpx.Timeout(15.0)


def _normalize_post(media: dict[str, Any]) -> NormalizedPost:
    return NormalizedPost(
        ig_id=media["id"],
        media_type=media.get("media_type"),
        caption=media.get("caption"),
        like_count=media.get("like_count"),
        # Ad farkı: BD `comments_count` → normalize `comment_count`.
        comment_count=media.get("comments_count"),
        # BD gönderi izlenme sayısı vermez → None.
        view_count=None,
        posted_at=parse_ig_timestamp(media["timestamp"]),
        permalink=media.get("permalink"),
        # Videoda ayrı thumbnail; yoksa media_url.
        thumb_url=media.get("thumbnail_url") or media.get("media_url"),
    )


def normalize_business_discovery(raw: dict[str, Any]) -> NormalizedProfile:
    """Ham BD yanıtını `NormalizedProfile`'a çevirir.

    `business_discovery` alanı yoksa/boşsa `ProfileUnavailableError` yükseltir —
    fallback tetikleyicisi (SPEC §2).
    """
    profile = raw.get("business_discovery")
    if not profile:
        raise ProfileUnavailableError(
            "Business Discovery yanıtında veri yok (hesap işletme hesabı olmayabilir)."
        )

    media_items = profile.get("media", {}).get("data", [])
    posts = [_normalize_post(m) for m in media_items]

    return NormalizedProfile(
        source="business_discovery",
        followers=profile.get("followers_count"),
        follows=profile.get("follows_count"),
        media_count=profile.get("media_count"),
        biography=profile.get("biography"),
        external_url=profile.get("website"),
        # BD yalnızca işletme/creator hesaplarını döndürür.
        is_professional=True,
        posts=posts,
        raw=raw,
    )


@register_profile("business_discovery")
class BusinessDiscoveryAdapter:
    source_name = "business_discovery"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        ig_user_id: str | None = None,
        token: str | None = None,
    ) -> None:
        self._client = client
        self._ig_user_id = ig_user_id
        self._token = token

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        raw = await self._fetch(handle)
        return normalize_business_discovery(raw)

    async def _fetch(self, handle: str) -> dict[str, Any]:
        params = self._params(handle)
        if self._client is not None:
            response = await self._client.get(self._url(), params=params)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data

        token = self._token or get_settings().ig_business_discovery_token
        if not token:
            raise RuntimeError(
                "IG Business Discovery token yok: IG_BUSINESS_DISCOVERY_TOKEN tanımlı değil."
            )
        # ig_user_id: çağıran işletme hesabının IG kullanıcı kimliği; verilmezse `me`.
        ig_user_id = self._ig_user_id or "me"
        params["access_token"] = token
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_GRAPH_BASE}/{ig_user_id}", params=params)
            response.raise_for_status()
            data = response.json()
            return data

    def _url(self) -> str:
        return f"{_GRAPH_BASE}/{self._ig_user_id or 'me'}"

    def _params(self, handle: str) -> dict[str, str]:
        # Graph API alan sorgusu: yalnızca SPEC §3'e düşürülebilir alanlar istenir.
        fields = (
            f"business_discovery.username({handle})"
            "{followers_count,follows_count,media_count,biography,website,"
            "media{id,media_type,caption,like_count,comments_count,timestamp,"
            "permalink,media_url,thumbnail_url}}"
        )
        return {"fields": fields}
