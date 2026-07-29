"""`GET /stats` — panel üst şeridi, DB'den.

Gerçek sorgu: `scanned` (triyajlı işletme), `qualified` (durum=qualified). `reports`
ve `monthly_cost_usd` `audits`'tan gelir — Faz 4'e kadar tablo boş, sorgu 0 döner
(uydurma sayı yok).
"""

from fastapi import APIRouter, Request

from api.config import get_settings
from api.schemas import CategoryCohortList, Stats
from api.services.dashboard import category_cohorts, compute_stats

router = APIRouter(tags=["dashboard"])


@router.get(
    "/stats",
    summary="Panel üst şeridi",
    operation_id="getStats",
    response_model=Stats,
)
async def get_stats(request: Request) -> Stats:
    # Lifespan yoksa (hermetik test) session_factory yok → sıfır sayaç. Üretimde
    # lifespan onu daima kurar.
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        return Stats(scanned=0, qualified=0, reports=0, monthly_cost_usd=0.0)

    async with session_factory() as session:
        return await compute_stats(
            session, monthly_cost_limit=get_settings().monthly_cost_limit_usd
        )


@router.get(
    "/stats/categories",
    summary="Kategori kohort dağılımı",
    operation_id="getCategoryCohorts",
    response_model=CategoryCohortList,
)
async def get_category_cohorts(request: Request) -> CategoryCohortList:
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        return CategoryCohortList(items=[])

    async with session_factory() as session:
        return await category_cohorts(session)
