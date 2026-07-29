"""180 günlük silme — dönüşmeyen adayın verisini siler (CLAUDE.md hukuki sınır).

Bu bir **cron** işidir, opsiyonel değil. "180 gün" ve "şimdi" enjekte edilen referans
zamandan gelir (BE-11 deseni): üretimde `now(UTC)`, testte sabit referans — saf silme
mantığı takvim gününe bağlı değildir.

**`won` korunur:** durumu `won` olan (dönüşen müşteri) aday **silinmez** — iş ilişkisi
kurulmuş bir müşterinin verisi saklanır. Silme yalnız *dönüşmeyen* adayı kapsar.

FK zinciri DB seviyesinde `ondelete=CASCADE`: işletme silinince snapshots→posts,
triage_scores, audits→outreach otomatik gider. Yetim PDF bırakmamak için audit
`pdf_path` dosyaları ayrıca silinir.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.models import Audit, Business, Outreach
from api.models.enums import OutreachStatus

logger = logging.getLogger(__name__)


@dataclass
class PurgeSummary:
    deleted_businesses: int = 0
    removed_pdfs: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"deleted_businesses": self.deleted_businesses, "removed_pdfs": self.removed_pdfs}


def _cutoff(reference_now: datetime, retention_days: int) -> datetime:
    """Bu andan eski olan işletmeler silme adayı (saf, test edilebilir)."""
    return reference_now - timedelta(days=retention_days)


async def _deletable_business_ids(session: AsyncSession, cutoff: datetime) -> list[int]:
    """`cutoff`'tan eski **ve** dönüşmemiş (won outreach'i olmayan) işletme kimlikleri."""
    # Dönüşen (won) işletmeler: audits→outreach zincirinde status=won olanlar.
    won_business_ids = (
        select(Audit.business_id)
        .join(Outreach, Outreach.audit_id == Audit.id)
        .where(Outreach.status == OutreachStatus.WON)
    )
    stmt = (
        select(Business.id)
        .where(Business.discovered_at < cutoff)
        .where(Business.id.notin_(won_business_ids))
    )
    return list((await session.execute(stmt)).scalars().all())


async def purge_old_candidates(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    reference_now: datetime,
    retention_days: int,
) -> PurgeSummary:
    """180 günden eski dönüşmemiş adayları (bağlı kayıtlar + PDF) siler; özet döner."""
    cutoff = _cutoff(reference_now, retention_days)
    async with session_factory() as session:
        ids = await _deletable_business_ids(session, cutoff)
        if not ids:
            logger.info("silme cron: silinecek aday yok (cutoff=%s)", cutoff.date())
            return PurgeSummary()

        # PDF yollarını silmeden ÖNCE topla (satırlar CASCADE ile gidecek).
        pdf_paths = list(
            (
                await session.execute(
                    select(Audit.pdf_path).where(
                        Audit.business_id.in_(ids), Audit.pdf_path.is_not(None)
                    )
                )
            )
            .scalars()
            .all()
        )
        # Tek DELETE; postgres FK CASCADE alt kayıtları temizler.
        await session.execute(delete(Business).where(Business.id.in_(ids)))
        await session.commit()

    # Yetim PDF dosyalarını sil (transaction dışında; dosya sistemi işi).
    removed = 0
    for path in pdf_paths:
        if path is None:
            continue
        try:
            Path(path).unlink(missing_ok=True)
            removed += 1
        except OSError:
            logger.warning("PDF silinemedi: %s", path, exc_info=True)

    summary = PurgeSummary(deleted_businesses=len(ids), removed_pdfs=removed)
    logger.info("silme cron tamamlandı: %s", summary.as_dict())
    return summary
