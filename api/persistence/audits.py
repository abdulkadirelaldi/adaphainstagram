"""Denetim sonucunu `audits` tablosuna yazar / okur."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.findings import Finding
from api.models import Audit


def _finding_to_dict(finding: Finding) -> dict[str, str | None]:
    return {
        "rule": finding.rule,
        "title": finding.title,
        "severity": finding.severity.value,
        "detail": finding.detail,
        "message": finding.message,  # BE-14'te None; BE-16 doldurur
    }


async def persist_audit(
    session: AsyncSession,
    *,
    business_id: int,
    visibility_score: float,
    findings: Sequence[Finding],
    llm_cost_usd: float = 0.0,
) -> Audit:
    """Bir denetim satırı yazar ve döndürür.

    `llm_cost_usd` BE-14'te **0**: LLM gerçekten çağrılmadı, gerçek maliyet 0 (alan
    NOT NULL — boş değil). BE-15/16 aynı audit'i güncelleyip gerçek maliyeti yazacak.
    `findings` JSONB listesi olarak saklanır; `report_text`/`outreach` bu aşamada yok.
    """
    audit = Audit(
        business_id=business_id,
        visibility_score=visibility_score,
        findings=[_finding_to_dict(f) for f in findings],
        pdf_path=None,
        llm_cost_usd=llm_cost_usd,
    )
    session.add(audit)
    await session.flush()
    return audit


async def get_audit(session: AsyncSession, audit_id: int) -> Audit | None:
    """Denetimi kimliğiyle getirir; yoksa `None`."""
    return await session.get(Audit, audit_id)
