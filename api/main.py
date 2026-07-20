"""FastAPI uygulama girişi."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.cache import create_redis
from api.config import get_settings
from api.db import create_engine, create_session_factory
from api.routes import health

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

    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Radar API",
        version="0.1.0",
        description="Kıyı Medya aday tarama ve denetim sistemi.",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    return app


app = create_app()
