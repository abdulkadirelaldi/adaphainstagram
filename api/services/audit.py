"""Denetim orkestrasyonu — DB'den okur, saf bulgu motorunu çağırır, `audits`'a yazar.

Saf bulgu motoru `api/core/findings.py`'de; bu katman DB↔dataclass köprüsü ve denetim
fazlarının orkestrasyonu. Fazlar: **BE-14** deterministik bulgu → **BE-15** Haiku
sınıflandırma → **BE-16** Sonnet sentez → tek `audits` kaydı gerçek maliyetle.

`llm_client` verilmezse yalnız deterministik faz koşar (`llm_cost_usd=0`, meşru — LLM
çağrılmadı). Verilirse Haiku+Sonnet koşar; maliyet 0 kalamaz. "Şimdi" referansı enjekte
edilir (üretimde `now`, fixture/testte `REFERENCE_NOW`).
"""

import logging
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from api.core.findings import AuditAccount, Finding, evaluate_findings, visibility_score
from api.core.signals import PostData
from api.llm.classify import classify_posts
from api.llm.client import LLMClient
from api.llm.synthesize import synthesize_audit
from api.models import Business, Snapshot, TriageScore
from api.models.enums import TriageStatus
from api.persistence import persist_audit, persist_outreach

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


def _to_posts(snapshot: Snapshot) -> list[PostData]:
    return [
        PostData(
            posted_at=post.posted_at,
            media_type=post.media_type,
            caption=post.caption,
            like_count=post.like_count,
            comment_count=post.comment_count,
            ig_id=post.ig_id,
        )
        for post in snapshot.posts
    ]


def _metrics(snapshot: Snapshot) -> dict[str, Any]:
    """Sentez girdisi için hesap metrikleri. Yalnız izinli alanlar — yasak metrik yok (kural 7)."""
    return {
        "followers": snapshot.followers,
        "follows": snapshot.follows,
        "media_count": snapshot.media_count,
        "post_count": len(snapshot.posts),
        "has_link": bool(snapshot.external_url),
        "has_phone": bool(snapshot.business.phone),
        "rating_count": snapshot.business.rating_count,
    }


async def _synthesize_phase(
    session: AsyncSession,
    *,
    llm_client: LLMClient,
    business_id: int,
    snapshot: Snapshot,
    posts: list[PostData],
    findings: list[Finding],
    score: float,
    reference_now: datetime,
) -> int:
    """BE-15 (Haiku) + BE-16 (Sonnet): sınıflandır, sentezle, gerçek maliyetle persist et."""
    as_of = reference_now.date()
    classify = await classify_posts(llm_client, posts, as_of=as_of)
    synthesis = await synthesize_audit(
        llm_client,
        findings=findings,
        classifications=classify.classifications,
        metrics=_metrics(snapshot),
        cohort={"category": snapshot.business.category},
        as_of=as_of,
    )
    # Bulgu mesajlarını yerleştir: LLM icat edemez, yalnız var olan kurala metin bağlar.
    enriched = [replace(f, message=synthesis.finding_messages.get(f.rule)) for f in findings]
    total_cost = classify.cost_usd + synthesis.cost_usd  # Decimal

    audit = await persist_audit(
        session,
        business_id=business_id,
        visibility_score=score,
        findings=enriched,
        llm_cost_usd=total_cost,
        report_text=synthesis.report_text,
    )
    # outreach `draft` doğar (CLAUDE.md hukuki sınır); gönderme yok.
    await persist_outreach(
        session, audit_id=audit.id, channel="instagram_dm", draft=synthesis.outreach_draft
    )
    logger.info(
        "denetim sentezi: audit=%d haiku_çağrı=%d llm_maliyet=%s",
        audit.id,
        classify.calls,
        total_cost,
    )
    return audit.id


async def run_audit(
    session_factory: async_sessionmaker[AsyncSession],
    business_id: int,
    reference_now: datetime,
    *,
    llm_client: LLMClient | None = None,
) -> int:
    """İşletmenin son snapshot'ını denetler; audit id döner.

    `llm_client` None → yalnız deterministik faz (BE-14): bulgu + skor, `llm_cost_usd=0`.
    Verilirse Haiku sınıflandırma + Sonnet sentez de koşar; rapor metni + outreach draft
    üretilir ve `llm_cost_usd` gerçek Haiku+Sonnet toplamı olur (maliyet disiplini).
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

        posts = _to_posts(snapshot)
        account = AuditAccount(
            posts=posts,
            external_url=snapshot.external_url,
            phone=snapshot.business.phone,
            biography=snapshot.biography,
        )
        findings = evaluate_findings(account, reference_now)
        score = visibility_score(findings)

        if llm_client is None:
            audit = await persist_audit(
                session,
                business_id=business_id,
                visibility_score=score,
                findings=findings,
                llm_cost_usd=Decimal(0),
            )
            audit_id = audit.id
        else:
            audit_id = await _synthesize_phase(
                session,
                llm_client=llm_client,
                business_id=business_id,
                snapshot=snapshot,
                posts=posts,
                findings=findings,
                score=score,
                reference_now=reference_now,
            )
        await session.commit()

    logger.info(
        "denetim tamamlandı: işletme=%d audit=%d skor=%.1f bulgu=%d llm=%s",
        business_id,
        audit_id,
        score,
        len(findings),
        "var" if llm_client is not None else "yok",
    )
    return audit_id
