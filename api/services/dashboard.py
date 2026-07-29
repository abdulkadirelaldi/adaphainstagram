"""Panel okuma sorguları — `/businesses` ve `/stats` DB'den.

Filtre/sayfalama/toplam **SQL'de** uygulanır (Faz 1'in sahte verisi kaldırıldı).
Her işletmenin **son** triyaj skoru/durumu `triage_scores`'tan LEFT JOIN ile gelir;
skorlanmamış (handle'sız / kohort<5 skorsuz) hesapta `score`/`status` null kalır —
sözleşmedeki nullable davranış.
"""

import logging
from decimal import Decimal

from sqlalchemy import Float, Select, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.scoring import MIN_COHORT
from api.models import Audit, Business, Post, Snapshot, TriageScore
from api.schemas import Business as BusinessOut
from api.schemas import BusinessList, CategoryCohort, CategoryCohortList, Stats, TriageStatus

logger = logging.getLogger(__name__)

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


async def compute_stats(session: AsyncSession, *, monthly_cost_limit: float | None = None) -> Stats:
    scanned = await session.scalar(select(func.count(func.distinct(TriageScore.business_id))))
    qualified = await session.scalar(
        select(func.count())
        .select_from(TriageScore)
        .where(TriageScore.status == TriageStatus.QUALIFIED)
    )
    reports = await session.scalar(select(func.count()).select_from(Audit))
    monthly_cost = float(
        await session.scalar(select(func.coalesce(func.sum(Audit.llm_cost_usd), 0))) or 0
    )

    # Maliyet alarmı (SPEC §8): eşik tanımlı ve aşıldıysa alarm açık + net uyarı logu.
    # Alarm bir bildirim; sistemi durdurmaz.
    alarm = monthly_cost_limit is not None and monthly_cost > monthly_cost_limit
    if alarm:
        logger.warning(
            "MALİYET ALARMI: aylık LLM maliyeti %.4f USD eşiği (%.2f USD) aştı.",
            monthly_cost,
            monthly_cost_limit,
        )

    return Stats(
        scanned=scanned or 0,
        qualified=qualified or 0,
        reports=reports or 0,
        monthly_cost_usd=monthly_cost,
        monthly_cost_alarm=alarm,
        monthly_cost_limit_usd=monthly_cost_limit,
    )


async def category_cohorts(session: AsyncSession) -> CategoryCohortList:
    """Kategori başına skor dağılımı (medyan+çeyrekler) + etkileşim medyanı (SPEC §4).

    Panelin kohort rayı bunu kullanır (FE-3-B1). Skor dağılımı `triage_scores`'tan;
    etkileşim medyanı son snapshot + gönderilerden `(like+comment)/followers`. **SPEC §4:
    kohort<5 → etkileşim hesaplanmaz → null.** Yalnız skor/etkileşim; yasak metrik yok.
    """
    # İşletme başına en güncel triyaj skoru.
    latest = (
        select(TriageScore.business_id, TriageScore.score.label("score"))
        .distinct(TriageScore.business_id)
        .order_by(TriageScore.business_id, TriageScore.computed_at.desc())
        .subquery()
    )
    score_stmt = (
        select(
            Business.category.label("category"),
            func.count().label("scanned"),
            func.percentile_cont(0.5).within_group(latest.c.score.asc()).label("median"),
            func.percentile_cont(0.25).within_group(latest.c.score.asc()).label("q1"),
            func.percentile_cont(0.75).within_group(latest.c.score.asc()).label("q3"),
        )
        .join(latest, latest.c.business_id == Business.id)
        .where(latest.c.score.is_not(None), Business.category.is_not(None))
        .group_by(Business.category)
    )

    # Etkileşim: son snapshot + gönderiler. Kategori → işletme → ortalama oran → medyan.
    latest_snap = (
        select(Snapshot.id, Snapshot.business_id, Snapshot.followers)
        .distinct(Snapshot.business_id)
        .order_by(Snapshot.business_id, Snapshot.captured_at.desc())
        .subquery()
    )
    biz_eng = (
        select(
            Business.category.label("category"),
            latest_snap.c.business_id.label("business_id"),
            func.avg(
                cast(
                    func.coalesce(Post.like_count, 0) + func.coalesce(Post.comment_count, 0), Float
                )
                / func.nullif(latest_snap.c.followers, 0)
            ).label("eng"),
        )
        .join(Business, Business.id == latest_snap.c.business_id)
        .join(Post, Post.snapshot_id == latest_snap.c.id)
        .where(latest_snap.c.followers > 0, Business.category.is_not(None))
        .group_by(Business.category, latest_snap.c.business_id)
        .subquery()
    )
    eng_stmt = select(
        biz_eng.c.category,
        func.percentile_cont(0.5).within_group(biz_eng.c.eng.asc()).label("eng_median"),
    ).group_by(biz_eng.c.category)

    score_rows = (await session.execute(score_stmt)).all()
    eng_by_cat = {r.category: r.eng_median for r in (await session.execute(eng_stmt)).all()}

    items: list[CategoryCohort] = []
    for category, scanned, median, q1, q3 in score_rows:
        eng_median = eng_by_cat.get(category)
        # SPEC §4: yetersiz kohort (<5) → etkileşim medyanı hesaplanmaz.
        engagement = float(eng_median) if eng_median is not None and scanned >= MIN_COHORT else None
        items.append(
            CategoryCohort(
                category=category,
                scanned=scanned,
                score_median=float(median) if median is not None else None,
                score_q1=float(q1) if q1 is not None else None,
                score_q3=float(q3) if q3 is not None else None,
                engagement_median=engagement,
            )
        )
    return CategoryCohortList(items=items)
