"""`GET /stats` — panel üst şeridi.

Faz 1: sahte ama tutarlı sayaçlar. Faz 4'te gerçek denetim/maliyet verisi bağlanınca
handler imzası ve `Stats` yanıt modeli değişmeyecek.
"""

from fastapi import APIRouter

from api.fake_data import FAKE_BUSINESSES, build_stats
from api.schemas import Stats

router = APIRouter(tags=["dashboard"])


@router.get(
    "/stats",
    summary="Panel üst şeridi",
    operation_id="getStats",
    response_model=Stats,
)
async def get_stats() -> Stats:
    return build_stats(FAKE_BUSINESSES)
