"""`GET /businesses` — sayfalanmış aday listesi.

Faz 1: sahte veri, ama query parametreleri gerçekten uygulanır (filtre + sayfalama).
Filtre/sayfalama mantığı `api.fake_data.select_businesses` içinde saf fonksiyon;
handler yalnızca query parametrelerini alıp yanıtı kurar.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from api.fake_data import FAKE_BUSINESSES, select_businesses
from api.schemas import BusinessList, TriageStatus

router = APIRouter(tags=["dashboard"])


@router.get(
    "/businesses",
    summary="Aday listesi",
    operation_id="listBusinesses",
    response_model=BusinessList,
)
async def list_businesses(
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
    items, total = select_businesses(
        FAKE_BUSINESSES,
        status=status,
        category=category,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    return BusinessList(items=items, total=total)
