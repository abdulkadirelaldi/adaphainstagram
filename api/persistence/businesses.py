"""Keşfedilen işletmeleri `businesses` tablosuna yazar."""

from sqlalchemy import select, update
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


async def set_ig_handle(session: AsyncSession, place_id: str, ig_handle: str) -> None:
    """Bir işletmenin `ig_handle`'ını set eder (handle eşleme, TASKS sözleşmesi).

    Idempotent: aynı handle tekrar yazılınca değer değişmez. Handle çıkarımı NULL
    dönen işletmeler için bu fonksiyon hiç çağrılmaz — `ig_handle` NULL kalır.
    """
    await session.execute(
        update(Business).where(Business.place_id == place_id).values(ig_handle=ig_handle)
    )


async def place_id_to_id(session: AsyncSession, place_ids: list[str]) -> dict[str, int]:
    """Verilen `place_id`'ler için `place_id → businesses.id` eşlemesi."""
    if not place_ids:
        return {}
    rows = await session.execute(
        select(Business.place_id, Business.id).where(Business.place_id.in_(place_ids))
    )
    return dict(rows.tuples().all())
