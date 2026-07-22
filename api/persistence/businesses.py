"""Keşfedilen işletmeleri `businesses` tablosuna yazar."""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.adapters.base import NormalizedBusiness
from api.models import Business

# Tekrar keşifte güncellenen alanlar. `discovered_at` bilinçle DIŞARIDA: ilk keşifte
# server_default ile atanır, çakışmada korunur (ilk görülme anı sabit kalmalı — 180
# günlük silme buna dayanır). `ig_handle` de dışarıda: eşleme ayrı bir adım (SPEC §1),
# keşif onu ezmemeli.
_UPDATABLE = ("name", "category", "address", "phone", "website", "rating_count")


async def upsert_businesses(
    session: AsyncSession, items: list[NormalizedBusiness]
) -> list[Business]:
    """İşletmeleri `place_id` üzerinden upsert eder; çift kayıt oluşmaz.

    Aynı `place_id` tekrar geldiğinde güncellenir (INSERT ... ON CONFLICT DO UPDATE),
    `discovered_at` ve `ig_handle` korunur. `NormalizedBusiness.raw` businesses'a
    yazılmaz — ham veri snapshots katmanına aittir (SPEC §3).
    """
    if not items:
        return []

    rows = [
        {
            "place_id": item.place_id,
            "name": item.name,
            "category": item.category,
            "address": item.address,
            "phone": item.phone,
            "website": item.website,
            "rating_count": item.rating_count,
        }
        for item in items
    ]

    insert_stmt = pg_insert(Business).values(rows)
    stmt = insert_stmt.on_conflict_do_update(
        index_elements=["place_id"],
        set_={col: getattr(insert_stmt.excluded, col) for col in _UPDATABLE},
    ).returning(Business)

    result = await session.execute(stmt)
    await session.flush()
    return list(result.scalars())
