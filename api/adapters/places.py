"""Google Places keşif adaptörü (SPEC §2).

Places (New) `places:searchText` yanıtını `NormalizedBusiness` listesine çevirir.
HTTP client dışarıdan enjekte edilebilir: test fixture'la çağırır, canlı çağrı yapmaz
(CLAUDE.md kural 6). Normalize saf bir fonksiyondur (`normalize_places`) — HTTP'den
bağımsız test edilebilir.

Yeni bir keşif kaynağı = bu dosyanın kopyası: tek dosya, `@register_discovery`.
"""

from typing import Any

import httpx

from api.adapters.base import (
    DiscoveryQuery,
    NormalizedBusiness,
    register_discovery,
)
from api.config import get_settings

# Places API (New) — metinle arama. Alan maskesi zorunlu; yalnızca SPEC §2'deki
# alanları ister, gereksiz veri (ve maliyet) çekmez.
_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = ",".join(
    f"places.{f}"
    for f in (
        "id",
        "displayName",
        "primaryType",
        "formattedAddress",
        "nationalPhoneNumber",
        "websiteUri",
        "userRatingCount",
        "rating",
        "types",
        "internationalPhoneNumber",
    )
)
_TIMEOUT = httpx.Timeout(15.0)
# Places tek sayfada en fazla 20 sonuç döndürür.
_MAX_PAGE_SIZE = 20


def normalize_places(raw: dict[str, Any]) -> list[NormalizedBusiness]:
    """Ham Places yanıtını `NormalizedBusiness` listesine çevirir.

    Eksik alanlar (`nationalPhoneNumber`, `websiteUri` yoksa) `None` olur. `rating`,
    `types`, `internationalPhoneNumber` gibi normalize dışı alanlar yalnızca `raw`'da
    kalır — yüzeye çıkmaz.
    """
    businesses: list[NormalizedBusiness] = []
    for place in raw.get("places", []):
        businesses.append(
            NormalizedBusiness(
                place_id=place["id"],
                # displayName Places'te işletme için daima döner; yoksa ham yanıt
                # bozuktur ve KeyError açık bir sinyaldir.
                name=place["displayName"]["text"],
                category=place.get("primaryType"),
                address=place.get("formattedAddress"),
                phone=place.get("nationalPhoneNumber"),
                website=place.get("websiteUri"),
                rating_count=place.get("userRatingCount"),
                raw=place,
            )
        )
    return businesses


@register_discovery("places")
class PlacesAdapter:
    source_name = "places"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        api_key: str | None = None,
    ) -> None:
        # Enjekte edilen client testte kullanılır; None ise canlı yolda geçici bir
        # client kurulur ve anahtar ayarlardan okunur.
        self._client = client
        self._api_key = api_key

    async def discover(self, query: DiscoveryQuery) -> list[NormalizedBusiness]:
        raw = await self._fetch(query)
        return normalize_places(raw)

    def _payload(self, query: DiscoveryQuery) -> dict[str, Any]:
        payload: dict[str, Any] = {"textQuery": f"{query.query} {query.region}"}
        if query.limit is not None:
            payload["pageSize"] = min(query.limit, _MAX_PAGE_SIZE)
        return payload

    async def _fetch(self, query: DiscoveryQuery) -> dict[str, Any]:
        payload = self._payload(query)
        if self._client is not None:
            response = await self._client.post(_ENDPOINT, json=payload, headers=self._headers())
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data

        api_key = self._api_key or get_settings().google_places_api_key
        if not api_key:
            raise RuntimeError(
                "Places API anahtarı yok: GOOGLE_PLACES_API_KEY .env'de tanımlı değil."
            )
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_ENDPOINT, json=payload, headers=self._headers(api_key))
            response.raise_for_status()
            data = response.json()
            return data

    def _headers(self, api_key: str | None = None) -> dict[str, str]:
        headers = {"X-Goog-FieldMask": _FIELD_MASK}
        key = api_key or self._api_key
        if key:
            headers["X-Goog-Api-Key"] = key
        return headers
