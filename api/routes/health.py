"""`GET /health` — bağımlılıkları gerçekten yoklar.

Sabit string dönmez: Postgres'e `SELECT 1`, Redis'e `PING` gider. Bağımlılıklardan
biri erişilemezse yanıt 503 olur ve ilgili alan `error` döner.
"""

import asyncio
import logging

from fastapi import APIRouter, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from api.schemas import ComponentStatus, Health

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


async def _check_db(engine: AsyncEngine, timeout: float) -> ComponentStatus:
    try:
        async with asyncio.timeout(timeout):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
    except Exception:
        # Sağlık ucu asla patlamaz: arıza yanıtın kendisidir, 500 değil.
        logger.warning("sağlık yoklaması başarısız: postgres", exc_info=True)
        return ComponentStatus.ERROR
    return ComponentStatus.OK


async def _check_redis(redis: Redis, timeout: float) -> ComponentStatus:
    try:
        async with asyncio.timeout(timeout):
            await redis.ping()
    except Exception:
        logger.warning("sağlık yoklaması başarısız: redis", exc_info=True)
        return ComponentStatus.ERROR
    return ComponentStatus.OK


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
    timeout = request.app.state.settings.health_timeout_seconds

    # İki yoklama paralel: biri zaman aşımına uğrarsa diğerini bekletmesin.
    db_status, redis_status = await asyncio.gather(
        _check_db(request.app.state.engine, timeout),
        _check_redis(request.app.state.redis, timeout),
    )

    overall = (
        ComponentStatus.OK
        if db_status is ComponentStatus.OK and redis_status is ComponentStatus.OK
        else ComponentStatus.ERROR
    )
    if overall is not ComponentStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return Health(status=overall, db=db_status, redis=redis_status)
