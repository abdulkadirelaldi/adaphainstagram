"""Kaynak adaptörü soyutlaması — protokoller, normalize şema, kayıt.

**İki protokol, tek protokol değil.** SPEC §2'de üç kaynak iki farklı işi yapar:

- Google Places **keşif** yapar: bir sorgudan yeni `businesses` kayıtları üretir.
  Takipçi/gönderi bilmez.
- IG Business Discovery ve Apify **profil** çeker: var olan bir işletmenin Instagram
  hesabından `snapshots` + `posts` üretir. Keşif yapmaz.

Bu ikisini tek imzaya zorlamak, alanların yarısı daima null olan sahte-birleşik bir
şema doğururdu (keşifte follower yok, profilde place_id yok). Bunun yerine iki protokol
ve iki normalize çıktı şeması var: `DiscoverySource → NormalizedBusiness`,
`ProfileSource → NormalizedProfile`. Her ikisi de aynı kayıt/registry deseniyle bulunur,
böylece "yeni kaynak tek dosya" (SPEC §2) korunur.

Normalize şemalar `extra="forbid"`: bir adaptör kaynağa özel fazla alan (özellikle
CLAUDE.md kural 7'nin yasakladığı erişim/gösterim/kaydetme/demografi) taşımaya kalkarsa
doğrulama patlar. Fazlalık `raw` alanına gömülür, normalize yüzeye çıkmaz.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class UnknownSourceError(KeyError):
    """Kayıtta olmayan bir kaynak adı istendi."""


class ProfileUnavailableError(Exception):
    """Bir profil kaynağı verilen handle için veri döndüremedi.

    Fallback tetikleyicisi (SPEC §2): Business Discovery bunu yükseltirse profil
    servisi Apify'a düşer. Ağ/HTTP hatasından ayrıdır — bu "kaynak bu hesabı
    veremiyor" demektir (ör. işletme hesabı değil, BD boş döndü).
    """


def parse_ig_timestamp(value: str) -> datetime:
    """Instagram/Apify zaman damgasını tz-aware `datetime`'a çevirir.

    Iki biçimi de karşılar: IG Graph `2026-06-18T09:12:00+0000` (iki nokta yok) ve
    Apify `2026-06-20T06:30:00.000Z`. Sonuç daima tz-aware (SPEC §3, UTC).
    """
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    # `+0000` gibi iki noktasız ofseti `+00:00`'a normalize et.
    if len(text) >= 5 and text[-5] in "+-" and text[-3] != ":":
        text = f"{text[:-2]}:{text[-2:]}"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


# --- Normalize çıktı şemaları (SPEC §3 tablolarına düşürülebilir) ---------------


class NormalizedBusiness(BaseModel):
    """Keşif çıktısı → `businesses` tablosu (SPEC §3).

    `ig_handle` burada yok: eşleme keşiften sonra ayrı bir adımda yapılır (SPEC §1).
    `discovered_at` veritabanı tarafından atanır.
    """

    model_config = ConfigDict(extra="forbid")

    place_id: str
    name: str
    category: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    rating_count: int | None = Field(default=None, ge=0)
    raw: dict[str, Any]


class NormalizedPost(BaseModel):
    """Profil çıktısındaki tek gönderi → `posts` tablosu (SPEC §3).

    Yalnızca SPEC §3'teki nicel alanlar. Erişim/gösterim/kaydetme yok (kural 7);
    `view_count` sadece videoda dolar.
    """

    model_config = ConfigDict(extra="forbid")

    ig_id: str
    media_type: str | None = None
    caption: str | None = None
    like_count: int | None = Field(default=None, ge=0)
    comment_count: int | None = Field(default=None, ge=0)
    view_count: int | None = Field(default=None, ge=0)
    posted_at: datetime
    permalink: str | None = None
    thumb_url: str | None = None


class NormalizedProfile(BaseModel):
    """Profil çıktısı → `snapshots` + `posts` tabloları (SPEC §3)."""

    model_config = ConfigDict(extra="forbid")

    # Hangi adaptör üretti (snapshots.source ile aynı değer): business_discovery | apify.
    source: str
    followers: int | None = Field(default=None, ge=0)
    follows: int | None = Field(default=None, ge=0)
    media_count: int | None = Field(default=None, ge=0)
    biography: str | None = None
    external_url: str | None = None
    is_professional: bool | None = None
    posts: list[NormalizedPost] = Field(default_factory=list)
    raw: dict[str, Any]


class DiscoveryQuery(BaseModel):
    """Keşif adaptörüne verilen girdi. HTTP gövdesinden (DiscoveryRequest) türetilir."""

    model_config = ConfigDict(extra="forbid")

    query: str
    region: str = "Samsun"
    limit: int | None = Field(default=None, ge=1, le=200)


# --- Protokoller ---------------------------------------------------------------


@runtime_checkable
class DiscoverySource(Protocol):
    """Keşif kaynağı: sorgudan işletme kayıtları üretir (ör. Places)."""

    source_name: str

    async def discover(self, query: DiscoveryQuery) -> list[NormalizedBusiness]: ...


@runtime_checkable
class ProfileSource(Protocol):
    """Profil kaynağı: bir IG handle'ından snapshot + gönderi üretir (ör. Apify)."""

    source_name: str

    async def fetch_profile(self, handle: str) -> NormalizedProfile: ...


# --- Kayıt (registry) ----------------------------------------------------------
#
# Adaptörler adlarıyla kayda girer; çağıran taraf `if source == "apify"` gibi dağınık
# dallanma yazmaz (SPEC §2). Kayıt fabrikaları (çağrılınca örnek üreten) tutar; bir
# Protocol tipi doğrudan örneklenemeyeceği için tip `Callable[[], ...]`.

_discovery_registry: dict[str, Callable[[], DiscoverySource]] = {}
_profile_registry: dict[str, Callable[[], ProfileSource]] = {}

D = TypeVar("D", bound=DiscoverySource)
P = TypeVar("P", bound=ProfileSource)


def register_discovery(name: str) -> Callable[[type[D]], type[D]]:
    """Bir keşif adaptörü sınıfını ada bağlar (dekoratör)."""

    def decorator(cls: type[D]) -> type[D]:
        _discovery_registry[name] = cls
        return cls

    return decorator


def register_profile(name: str) -> Callable[[type[P]], type[P]]:
    """Bir profil adaptörü sınıfını ada bağlar (dekoratör)."""

    def decorator(cls: type[P]) -> type[P]:
        _profile_registry[name] = cls
        return cls

    return decorator


def get_discovery_source(name: str) -> DiscoverySource:
    try:
        factory = _discovery_registry[name]
    except KeyError:
        raise UnknownSourceError(
            f"Bilinmeyen keşif kaynağı: {name!r}. Kayıtlı: {sorted(_discovery_registry)}"
        ) from None
    return factory()


def get_profile_source(name: str) -> ProfileSource:
    try:
        factory = _profile_registry[name]
    except KeyError:
        raise UnknownSourceError(
            f"Bilinmeyen profil kaynağı: {name!r}. Kayıtlı: {sorted(_profile_registry)}"
        ) from None
    return factory()


def discovery_sources() -> list[str]:
    """Kayıtlı keşif kaynaklarının adları."""
    return sorted(_discovery_registry)


def profile_sources() -> list[str]:
    """Kayıtlı profil kaynaklarının adları."""
    return sorted(_profile_registry)
