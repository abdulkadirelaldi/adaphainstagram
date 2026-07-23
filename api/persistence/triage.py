"""Triyaj skorlarını `triage_scores` tablosuna yazar."""

from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.scoring import ScoreResult
from api.models import TriageScore


async def write_triage_scores(session: AsyncSession, results: Sequence[ScoreResult]) -> None:
    """Skorları yazar. İdempotent: işletme başına **tek** (en güncel) satır semantiği.

    Tekrar skorlama çift satır üretmesin diye, yazılan işletmelerin önceki
    `triage_scores` satırları silinir, sonra taze satırlar eklenir. Böylece bir
    işletmenin daima tek ve en güncel triyaj kaydı olur; `/businesses` bunu okur.
    """
    if not results:
        return

    business_ids = [r.business_id for r in results]
    await session.execute(delete(TriageScore).where(TriageScore.business_id.in_(business_ids)))
    session.add_all(
        TriageScore(
            business_id=r.business_id,
            snapshot_id=r.snapshot_id,
            activity=r.activity,
            capacity=r.capacity,
            potential=r.potential,
            score=r.score,
            status=r.status,
        )
        for r in results
    )
    await session.flush()
