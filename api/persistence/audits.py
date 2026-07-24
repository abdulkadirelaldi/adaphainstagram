"""Denetim sonucunu `audits` tablosuna yazar / okur."""

from collections.abc import Sequence
from decimal import Decimal

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
    llm_cost_usd: float | Decimal = 0.0,
    report_text: str | None = None,
) -> Audit:
    """Bir denetim satırı yazar ve döndürür.

    LLM çağrılmadan (deterministik yol) `llm_cost_usd=0` ve `report_text=None` meşru
    (alan NOT NULL — 0 gerçek maliyet). LLM çağrıldığında (BE-16) çağıran gerçek
    toplam maliyeti ve rapor metnini geçer; `findings` içindeki `message` alanları
    Sonnet'in ajans-dili çevirisiyle dolar. `llm_cost_usd` Numeric — Decimal geçilir.
    """
    audit = Audit(
        business_id=business_id,
        visibility_score=visibility_score,
        findings=[_finding_to_dict(f) for f in findings],
        report_text=report_text,
        pdf_path=None,
        llm_cost_usd=llm_cost_usd,
    )
    session.add(audit)
    await session.flush()
    return audit


async def get_audit(session: AsyncSession, audit_id: int) -> Audit | None:
    """Denetimi kimliğiyle getirir; yoksa `None`."""
    return await session.get(Audit, audit_id)
