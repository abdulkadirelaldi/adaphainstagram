"""Kaynak adaptörleri.

Bu paketi import etmek üç adaptörü de kayda sokar: alt modüller import edilince
`@register_*` dekoratörleri çalışır. Yeni kaynak eklemek = yeni dosya + buraya tek
import satırı.
"""

from api.adapters.apify import ApifyAdapter
from api.adapters.base import (
    DiscoveryQuery,
    DiscoverySource,
    NormalizedBusiness,
    NormalizedPost,
    NormalizedProfile,
    ProfileSource,
    UnknownSourceError,
    discovery_sources,
    get_discovery_source,
    get_profile_source,
    profile_sources,
    register_discovery,
    register_profile,
)
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter

# Protokol uyumu mypy'de burada zorlanır: bir adaptör imzayı bozarsa (metot eksik,
# yanlış imza, `source_name` yok) bu atamalar tip hatası verir. Faz 2 boyunca
# BE-7/BE-8 gövdeleri doldururken sözleşmeden sapmayı derleme zamanında yakalar.
_discovery_conformance: DiscoverySource = PlacesAdapter()
_profile_conformance: tuple[ProfileSource, ProfileSource] = (
    BusinessDiscoveryAdapter(),
    ApifyAdapter(),
)

__all__ = [
    "ApifyAdapter",
    "BusinessDiscoveryAdapter",
    "DiscoveryQuery",
    "DiscoverySource",
    "NormalizedBusiness",
    "NormalizedPost",
    "NormalizedProfile",
    "PlacesAdapter",
    "ProfileSource",
    "UnknownSourceError",
    "discovery_sources",
    "get_discovery_source",
    "get_profile_source",
    "profile_sources",
    "register_discovery",
    "register_profile",
]
