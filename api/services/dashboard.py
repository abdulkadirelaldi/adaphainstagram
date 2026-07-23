"""Panel okuma sorguları — `/businesses` ve `/stats` DB'den.

Filtre/sayfalama/toplam **SQL'de** uygulanır (Faz 1'in sahte verisi kaldırıldı).
Her işletmenin **son** triyaj skoru/durumu `triage_scores`'tan LEFT JOIN ile gelir;
skorlanmamış (handle'sız / kohort<5 skorsuz) hesapta `score`/`status` null kalır —
sözleşmedeki nullable davranış.
"""

from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Audit, Business, TriageScore
from api.schemas import Business as BusinessOut
from api.schemas import BusinessList, Stats, TriageStatus

# İşletme başına en güncel triyaj satırı. triage_scores zaten idempotent (işletme
# başına tek satır) ama DISTINCT ON ile birden fazlaya karşı da doğru kalır.
_latest_triage = (
    select(
        TriageScore.business_id,
        TriageScore.score.label("score"),
        TriageScore.status.label("status"),
    )
    .distinct(TriageScore.business_id)
    .order_by(TriageScore.business_id, TriageScore.computed_at.desc())
    .subquery()
)


def _apply_filters(
    stmt: Select[tuple[Business, Decimal | None, TriageStatus | None]],
    *,
    status: TriageStatus | None,
    category: str | None,
    min_score: float | None,
) -> Select[tuple[Business, Decimal | None, TriageStatus | None]]:
    if status is not None:
        stmt = stmt.where(_latest_triage.c.status == status)
    if category is not None:
        stmt = stmt.where(Business.category == category)
    if min_score is not None:
        # NULL skor (skorlanmamış) otomatik elenir: NULL >= x → NULL → satır düşer.
        stmt = stmt.where(_latest_triage.c.score >= min_score)
    return stmt


async def list_businesses(
    session: AsyncSession,
    *,
    status: TriageStatus | None = None,
    category: str | None = None,
    min_score: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> BusinessList:
    base = select(Business, _latest_triage.c.score, _latest_triage.c.status).outerjoin(
        _latest_triage, Business.id == _latest_triage.c.business_id
    )
    filtered = _apply_filters(base, status=status, category=category, min_score=min_score)

    total = await session.scalar(select(func.count()).select_from(filtered.subquery())) or 0

    # Nitelikli adaylar üstte: skora göre azalan (skorsuz en sonda), id ile stabil.
    page = (
        filtered.order_by(_latest_triage.c.score.desc().nulls_last(), Business.id)
        .limit(limit)
        .offset(offset)
    )

    rows = (await session.execute(page)).all()
    items = [
        BusinessOut(
            id=business.id,
            place_id=business.place_id,
            name=business.name,
            category=business.category,
            address=business.address,
            phone=business.phone,
            website=business.website,
            ig_handle=business.ig_handle,
            rating_count=business.rating_count,
            discovered_at=business.discovered_at,
            score=float(score) if score is not None else None,
            status=status_value,
        )
        for business, score, status_value in rows
    ]
    return BusinessList(items=items, total=total)


async def compute_stats(session: AsyncSession) -> Stats:
    scanned = await session.scalar(select(func.count(func.distinct(TriageScore.business_id))))
    qualified = await session.scalar(
        select(func.count())
        .select_from(TriageScore)
        .where(TriageScore.status == TriageStatus.QUALIFIED)
    )
    # Faz 4'te audits dolacak; şimdilik gerçek sorgu boş tabloda 0 döner (uydurma yok).
    reports = await session.scalar(select(func.count()).select_from(Audit))
    monthly_cost = await session.scalar(select(func.coalesce(func.sum(Audit.llm_cost_usd), 0)))

    return Stats(
        scanned=scanned or 0,
        qualified=qualified or 0,
        reports=reports or 0,
        monthly_cost_usd=float(monthly_cost or 0),
    )
