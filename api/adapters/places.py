"""Google Places keşif adaptörü.

BE-6 iskeleti: protokol uyumu ve kayıt için var, gerçek HTTP çağrısı **BE-7**'de gelir.
Yeni bir keşif kaynağı eklemek isteyen bu dosyayı örnek alır — tek dosya, kayıt dekoratörü.
"""

from api.adapters.base import (
    DiscoveryQuery,
    NormalizedBusiness,
    register_discovery,
)


@register_discovery("places")
class PlacesAdapter:
    source_name = "places"

    async def discover(self, query: DiscoveryQuery) -> list[NormalizedBusiness]:
        raise NotImplementedError("Places keşfi BE-7'de uygulanacak.")
