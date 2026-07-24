"""Denetim orkestrasyonu — DB'den okur, saf bulgu motorunu çağırır, `audits`'a yazar.

Saf bulgu motoru `api/core/findings.py`'de; bu katman yalnız DB↔dataclass köprüsü.
**LLM yok** (BE-14): bulgular deterministik, `llm_cost_usd=0`. "Şimdi" referansı
enjekte edilir (üretimde `now`, fixture/testte `REFERENCE_NOW`).
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from api.core.findings import AuditAccount, evaluate_findings, visibility_score
from api.core.signals import PostData
from api.models import Business, Snapshot, TriageScore
from api.models.enums import TriageStatus
from api.persistence import persist_audit

logger = logging.getLogger(__name__)


class NotAuditableError(Exception):
    """İşletme derin denetime uygun değil (yok, skorsuz veya `qualified` değil)."""


async def latest_triage_status(session: AsyncSession, business_id: int) -> TriageStatus | None:
    """İşletmenin en güncel triyaj durumu; hiç skorlanmadıysa `None`."""
    status: TriageStatus | None = await session.scalar(
        select(TriageScore.status)
        .where(TriageScore.business_id == business_id)
        .order_by(TriageScore.computed_at.desc())
        .limit(1)
    )
    return status


async def assert_auditable(session: AsyncSession, business_id: int) -> None:
    """İşletme derin denetime uygun mu doğrular (SPEC §1: yalnız `qualified`).

    Yoksa `LookupError` (route 404'e çevirir), nitelikli değilse `NotAuditableError`
    (route 409'a çevirir).
    """
    if await session.get(Business, business_id) is None:
        raise LookupError(f"İşletme bulunamadı: {business_id}")
    status = await latest_triage_status(session, business_id)
    if status is not TriageStatus.QUALIFIED:
        raise NotAuditableError(
            f"İşletme {business_id} derin denetime uygun değil (durum: {status})."
        )


def _to_audit_account(snapshot: Snapshot) -> AuditAccount:
    return AuditAccount(
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
        external_url=snapshot.external_url,
        phone=snapshot.business.phone,
        biography=snapshot.biography,
    )


async def run_audit(
    session_factory: async_sessionmaker[AsyncSession],
    business_id: int,
    reference_now: datetime,
) -> int:
    """İşletmenin son snapshot'ını denetler, bulguları+skoru `audits`'a yazar; audit id döner.

    Deterministik faz (BE-14): bulgu motoru → görünürlük skoru → persist. LLM yok,
    `llm_cost_usd=0`. BE-15/16 aynı audit'i zenginleştirecek.
    """
    async with session_factory() as session:
        snapshot = await session.scalar(
            select(Snapshot)
            .where(Snapshot.business_id == business_id)
            .options(selectinload(Snapshot.posts), selectinload(Snapshot.business))
            .order_by(Snapshot.captured_at.desc())
            .limit(1)
        )
        if snapshot is None:
            raise NotAuditableError(f"İşletme {business_id} için snapshot yok, denetlenemez.")

        account = _to_audit_account(snapshot)
        findings = evaluate_findings(account, reference_now)
        score = visibility_score(findings)

        audit = await persist_audit(
            session,
            business_id=business_id,
            visibility_score=score,
            findings=findings,
            llm_cost_usd=0.0,
        )
        await session.commit()
        audit_id = audit.id

    logger.info(
        "denetim tamamlandı: işletme=%d audit=%d skor=%.1f bulgu=%d",
        business_id,
        audit_id,
        score,
        len(findings),
    )
    return audit_id
