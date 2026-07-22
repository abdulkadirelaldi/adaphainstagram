"""IG Business Discovery profil adaptörü.

BE-6 iskeleti: gerçek çağrı **BE-8**'de. Hedef işletme hesabıysa tercih edilen
profil kaynağıdır; başarısız olursa Apify'a düşülür (SPEC §2).
"""

from api.adapters.base import (
    NormalizedProfile,
    register_profile,
)


@register_profile("business_discovery")
class BusinessDiscoveryAdapter:
    source_name = "business_discovery"

    async def fetch_profile(self, handle: str) -> NormalizedProfile:
        raise NotImplementedError("IG Business Discovery profili BE-8'de uygulanacak.")
