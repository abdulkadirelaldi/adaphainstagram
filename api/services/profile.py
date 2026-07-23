"""Profil çekimi + fallback orkestrasyonu (SPEC §2).

Fallback burada, adaptörlerin dışında: her adaptör tek kaynağı bilir ve kendi
başarısızlığını `ProfileUnavailableError` ile bildirir; hangi kaynağın önce
deneneceği ve ne zaman düşüleceği bir servis kararıdır. Böylece yeni bir profil
kaynağı eklemek fallback mantığını değiştirmez.
"""

import logging

from api.adapters.base import (
    NormalizedProfile,
    ProfileSource,
    ProfileUnavailableError,
)

logger = logging.getLogger(__name__)


async def fetch_profile(
    handle: str,
    *,
    primary: ProfileSource,
    fallback: ProfileSource,
) -> NormalizedProfile:
    """Önce `primary`'yi (Business Discovery) dener, veri veremezse `fallback`'e (Apify) düşer.

    Yalnızca `ProfileUnavailableError` fallback tetikler — "bu kaynak bu hesabı
    veremiyor" demektir. Ağ/HTTP hatası yükselmeye devam eder; onu yutup yanlış
    kaynağa düşmek veriyi sessizce bozardı.
    """
    try:
        return await primary.fetch_profile(handle)
    except ProfileUnavailableError:
        logger.info(
            "profil kaynağı %r veri vermedi, %r'a düşülüyor: %s",
            primary.source_name,
            fallback.source_name,
            handle,
        )
        return await fallback.fetch_profile(handle)
