"""Apify Instagram Scraper profil adaptörü.

BE-6 iskeleti: gerçek çağrı **BE-8**'de. Business Discovery çalışmadığında yedek
profil kaynağıdır (SPEC §2). Apify daha fazla alan döndürür; normalize katmanı
fazlalığı `raw`'a gömer, yasak metrikleri (kural 7) yüzeye taşımaz.
"""

from api.adapters.base import (
    NormalizedProfile,
    register_profile,
)


@register_profile("apify")
class ApifyAdapter:
    source_name = "apify"

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        raise NotImplementedError("Apify profili BE-8'de uygulanacak.")
