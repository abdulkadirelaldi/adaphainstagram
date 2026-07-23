"""arq worker — keşif işini yürütür.

Uzun süren keşif/scraping HTTP endpoint'te değil burada koşar (SPEC §7). `POST
/discovery/run` işi kuyruğa atar ve anında `job_id` döner; bu worker işi tüketir.

Bu modül **gerçek** adaptörleri kurar (canlı Places/IG/Apify). Fixture'lı demo canlı
çağrı yapmaz ve `api/discover_demo.py` üzerinden aynı `run_discovery` akışını sahte
client'larla çalıştırır — worker'ı atlar (kural 6).
"""

import logging
import os
from typing import Any, ClassVar

from arq.connections import RedisSettings
from redis.asyncio import Redis

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.config import get_settings
from api.db import create_engine, create_session_factory
from api.jobstate import write_progress
from api.services import run_discovery

logger = logging.getLogger(__name__)


async def discovery_task(
    ctx: dict[str, Any],
    *,
    query: str,
    region: str = "Samsun",
    limit: int | None = None,
) -> dict[str, int]:
    """Keşif akışını gerçek adaptörlerle yürütür; job sonucu özet döner."""
    settings = get_settings()
    redis: Redis = ctx["redis"]
    job_id: str = ctx["job_id"]
    session_factory = ctx["session_factory"]

    async def on_progress(processed: int, total: int) -> None:
        await write_progress(redis, job_id, processed, total)

    summary = await run_discovery(
        DiscoveryQuery(query=query, region=region, limit=limit),
        places=PlacesAdapter(api_key=settings.google_places_api_key),
        profile_primary=BusinessDiscoveryAdapter(token=settings.ig_business_discovery_token),
        profile_fallback=ApifyAdapter(token=settings.apify_token),
        session_factory=session_factory,
        redis=redis,
        cache_ttl_seconds=settings.snapshot_cache_ttl_seconds,
        on_progress=on_progress,
    )
    logger.info("keşif tamamlandı: %s", summary.as_dict())
    # Sözleşme JobResult'ı businesses+snapshots ister; zengin sayaçlar log'da.
    data = summary.as_dict()
    return {"businesses": data["discovered"], "snapshots": data["snapshots_written"]}


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    ctx["engine"] = engine
    ctx["session_factory"] = create_session_factory(engine)


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()


class WorkerSettings:
    """arq bu sınıfı okur: `arq api.worker.WorkerSettings`."""

    functions: ClassVar = [discovery_task]
    on_startup = startup
    on_shutdown = shutdown
    # arq `redis_settings`'i bir değer olarak okur (fonksiyon değil). Import anında
    # get_settings() çağırıp DB zorunluluğu getirmemek için REDIS_URL doğrudan
    # ortamdan; yoksa yerel varsayılan.
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
