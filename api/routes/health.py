"""`GET /health` — bağımlılıkları gerçekten yoklar.

Sabit string dönmez: Postgres'e `SELECT 1`, Redis'e `PING` gider. Bağımlılıklardan
biri erişilemezse yanıt 503 olur ve ilgili alan `error` döner.
"""

import asyncio
import logging
from collections.abc import Awaitable

from fastapi import APIRouter, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from api.schemas import ComponentStatus, Health

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


async def _probe_db(engine: AsyncEngine) -> None:
    """Postgres'e tek bir `SELECT 1` atar; başarısızsa yükseltir.

    Zaman aşımı bilinçli olarak burada yok — iptal kapsamını çağıran `get_health`
    yönetir (ruff ASYNC109). Bu fonksiyon yalnızca yoklamayı yapar.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _probe_redis(redis: Redis) -> None:
    """Redis'e `PING` atar; başarısızsa yükseltir."""
    await redis.ping()


@router.get(
    "/health",
    summary="Servis sağlığı",
    operation_id="getHealth",
    response_model=Health,
    responses={
        status.HTTP_200_OK: {"description": "Tüm bağımlılıklar sağlıklı"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "En az bir bağımlılık erişilemez durumda",
            "model": Health,
        },
    },
)
async def get_health(request: Request, response: Response) -> Health:
    limit = request.app.state.settings.health_timeout_seconds

    async def bounded(probe: Awaitable[None]) -> ComponentStatus:
        """Bir yoklamayı zaman aşımıyla sarar; her arıza -> error.

        Zaman aşımı sınırı `limit` üzerinden closure ile alınır, parametre olarak
        değil: async imzada `timeout` parametresi ruff ASYNC109 üretiyordu. İptal
        kapsamı böylece çağıranda kalıyor. Asılı kalan bir bağımlılık yanıtı süresiz
        bekletmez; `limit` dolunca `error` raporlanır.
        """
        try:
            async with asyncio.timeout(limit):
                await probe
        except Exception:
            # Sağlık ucu asla patlamaz: arıza yanıtın kendisidir, 500 değil.
            logger.warning("sağlık yoklaması başarısız", exc_info=True)
            return ComponentStatus.ERROR
        return ComponentStatus.OK

    # İki yoklama paralel ve her biri kendi zaman aşımıyla sarılı: biri asılırsa
    # veya arızalıysa diğerinin sonucunu kirletmez.
    db_status, redis_status = await asyncio.gather(
        bounded(_probe_db(request.app.state.engine)),
        bounded(_probe_redis(request.app.state.redis)),
    )

    overall = (
        ComponentStatus.OK
        if db_status is ComponentStatus.OK and redis_status is ComponentStatus.OK
        else ComponentStatus.ERROR
    )
    if overall is not ComponentStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return Health(status=overall, db=db_status, redis=redis_status)
