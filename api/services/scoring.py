"""Skorlama orkestrasyonu — DB'den okur, saf motoru çağırır, `triage_scores`'a yazar.

Saf skorlama `api/core/scoring.py`'de; bu katman yalnız DB↔dataclass köprüsü. "Şimdi"
referansı **enjekte** edilir (üretimde `now`, fixture/testte `REFERENCE_NOW`) — `now()`
bu katmanın da dışında, çağıran (worker/demo) verir.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from api.core.scoring import AccountData, PostData, score_accounts
from api.models import Snapshot
from api.persistence.triage import write_triage_scores

logger = logging.getLogger(__name__)


def _to_account(snapshot: Snapshot) -> AccountData:
    business = snapshot.business
    return AccountData(
        business_id=snapshot.business_id,
        snapshot_id=snapshot.id,
        category=business.category,
        rating_count=business.rating_count,
        has_website=bool(business.website),
        followers=snapshot.followers,
        posts=[
            PostData(
                posted_at=post.posted_at,
                media_type=post.media_type,
                caption=post.caption,
                like_count=post.like_count,
                comment_count=post.comment_count,
            )
            for post in snapshot.posts
        ],
    )


async def score_discovered(
    session_factory: async_sessionmaker[AsyncSession], reference_now: datetime
) -> int:
    """Snapshot'ı olan tüm işletmeleri (son snapshot üzerinden) skorlar. Skorlanan sayı döner.

    Kohort medyanı kategori bazında hesaplandığı için tüm hesaplar tek batch'te
    skorlanır (SPEC §4 — etkileşim izole hesapla karşılaştırılamaz).
    """
    async with session_factory() as session:
        snapshots = (
            (
                await session.execute(
                    select(Snapshot)
                    .options(selectinload(Snapshot.posts), selectinload(Snapshot.business))
                    .order_by(Snapshot.captured_at)
                )
            )
            .scalars()
            .all()
        )

    # İşletme başına en güncel snapshot (captured_at artan sıralı → son yazan kazanır).
    latest_by_business: dict[int, Snapshot] = {s.business_id: s for s in snapshots}
    accounts = [_to_account(s) for s in latest_by_business.values()]

    results = score_accounts(accounts, reference_now)

    async with session_factory() as session:
        await write_triage_scores(session, results)
        await session.commit()

    logger.info("skorlama tamamlandı: %d hesap", len(results))
    return len(results)
