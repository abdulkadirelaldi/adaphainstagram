"""`GET /businesses` — sayfalanmış aday listesi, DB'den.

Filtre (`status`/`category`/`min_score`) ve sayfalama (`limit`/`offset`/`total`) SQL'de
uygulanır; her kayıt en son triyaj skorunu/durumunu taşır (`api.services.dashboard`).
Handler yalnız HTTP: query parametrelerini alır, bir DB oturumu açar, servisi çağırır.
"""

from typing import Annotated

from fastapi import APIRouter, Query, Request

from api.schemas import BusinessList, TriageStatus
from api.services.dashboard import list_businesses

router = APIRouter(tags=["dashboard"])


@router.get(
    "/businesses",
    summary="Aday listesi",
    operation_id="listBusinesses",
    response_model=BusinessList,
)
async def get_businesses(
    request: Request,
    status: Annotated[
        TriageStatus | None,
        Query(description="Triyaj durumuna göre filtre. Verilmezse tüm durumlar."),
    ] = None,
    category: Annotated[
        str | None,
        Query(min_length=1, description="Kategoriye göre birebir filtre."),
    ] = None,
    min_score: Annotated[
        float | None,
        Query(ge=0, le=100, description="Altındaki (ve skorsuz) kayıtları eler."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=200, description="Sayfa başına kayıt."),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Atlanacak kayıt."),
    ] = 0,
) -> BusinessList:
    # Uygulama lifespan olmadan kurulmuşsa (yalnız hermetik testler) session_factory
    # yoktur → boş liste. Üretimde lifespan onu daima kurar; bu yol canlıda görülmez.
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        return BusinessList(items=[], total=0)

    async with session_factory() as session:
        return await list_businesses(
            session,
            status=status,
            category=category,
            min_score=min_score,
            limit=limit,
            offset=offset,
        )
