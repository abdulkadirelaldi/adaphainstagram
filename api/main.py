"""FastAPI uygulama girişi."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.cache import create_redis
from api.config import get_cors_settings, get_settings
from api.db import create_engine, create_session_factory
from api.routes import audits, businesses, health, jobs, stats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Bağlantı havuzlarını açar ve kapatır.

    Havuzlar açılırken bağımlılıklara erişilebildiği doğrulanmaz — bilinçli. Servis
    postgres veya redis geçici olarak inikken de ayağa kalkmalı ve bunu /health
    üzerinden 503 ile bildirmeli; açılışta çökerse durumu raporlayacak kimse kalmaz.
    """
    settings = get_settings()
    engine = create_engine(settings)
    redis = create_redis(settings)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.redis = redis

    # arq havuzu enqueue + job durumu için. create_pool bağlanmaya çalışır; redis
    # inikse uygulama yine ayağa kalkmalı (/health durumu bildirebilsin), keşif
    # uçları redis gelene kadar 503 döner.
    try:
        app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    except Exception:
        logger.warning("arq havuzu açılamadı; keşif uçları 503 dönecek", exc_info=True)
        app.state.arq_pool = None

    try:
        yield
    finally:
        if app.state.arq_pool is not None:
            await app.state.arq_pool.aclose()
        await redis.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Radar API",
        version="0.1.0",
        description="Kıyı Medya aday tarama ve denetim sistemi.",
        lifespan=lifespan,
    )

    # CORS: panel (web/) bu API'ye tarayıcıdan istek atar. Açık origin listesi
    # ayarlardan gelir; `allow_origins=["*"]` bilinçli olarak kullanılmaz.
    # get_cors_settings() zorunlu alan içermez → uygulama canlı config olmadan da
    # kurulabilir (hermetik testler bozulmaz).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_settings().origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(stats.router)
    app.include_router(businesses.router)
    app.include_router(jobs.router)
    app.include_router(audits.router)
    return app


app = create_app()
