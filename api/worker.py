"""arq worker — keşif işini yürütür.

Uzun süren keşif/scraping HTTP endpoint'te değil burada koşar (SPEC §7). `POST
/discovery/run` işi kuyruğa atar ve anında `job_id` döner; bu worker işi tüketir.

Varsayılan olarak **gerçek** adaptörleri kurar (canlı Places/IG/Apify). `RADAR_FIXTURE_MODE`
açıkken aynı job'u `tests/fixtures/` ile yürütür (kural 6) — gerçek anahtar olmadan
gerçek arq worker + durum makinesi uçtan uca çalışır. Bu, `discover_demo`'dan farklı:
demo worker'ı atlar, fixture modu gerçek job/durum makinesini kullanır.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.config import get_settings
from api.db import create_engine, create_session_factory
from api.fixture_mode import FIXTURE_REFERENCE_NOW, fixture_adapters
from api.jobstate import write_progress
from api.llm.client import AnthropicLLMClient, LLMClient
from api.llm.fixture_client import FixtureLLMClient
from api.services import DiscoverySummary, purge_old_candidates, run_audit, run_discovery
from api.services.discovery import ProgressCallback

logger = logging.getLogger(__name__)


async def _run(
    query: DiscoveryQuery,
    *,
    fixture_mode: bool,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Redis,
    cache_ttl_seconds: int,
    on_progress: ProgressCallback,
) -> DiscoverySummary:
    """Keşif akışını fixture veya gerçek adaptörlerle yürütür (tek çağrı yeri)."""
    if fixture_mode:
        # Fixture'lar sabit tarihli → skorlama sabit referansla deterministik.
        async with fixture_adapters() as (places, primary, fallback):
            return await run_discovery(
                query,
                places=places,
                profile_primary=primary,
                profile_fallback=fallback,
                session_factory=session_factory,
                redis=redis,
                cache_ttl_seconds=cache_ttl_seconds,
                reference_now=FIXTURE_REFERENCE_NOW,
                on_progress=on_progress,
            )

    settings = get_settings()
    return await run_discovery(
        query,
        places=PlacesAdapter(api_key=settings.google_places_api_key),
        profile_primary=BusinessDiscoveryAdapter(token=settings.ig_business_discovery_token),
        profile_fallback=ApifyAdapter(token=settings.apify_token),
        session_factory=session_factory,
        redis=redis,
        cache_ttl_seconds=cache_ttl_seconds,
        reference_now=datetime.now(UTC),
        on_progress=on_progress,
    )


async def discovery_task(
    ctx: dict[str, Any],
    *,
    query: str,
    region: str = "Samsun",
    limit: int | None = None,
) -> dict[str, int | None]:
    """Keşif job'u; job sonucu özet döner. Fixture modu ayardan gelir."""
    settings = get_settings()
    redis: Redis = ctx["redis"]
    job_id: str = ctx["job_id"]
    session_factory = ctx["session_factory"]

    async def on_progress(processed: int, total: int) -> None:
        await write_progress(redis, job_id, processed, total)

    if settings.radar_fixture_mode:
        logger.warning("RADAR_FIXTURE_MODE açık — keşif fixture'la yürütülüyor (canlı çağrı yok)")

    summary = await _run(
        DiscoveryQuery(query=query, region=region, limit=limit),
        fixture_mode=settings.radar_fixture_mode,
        session_factory=session_factory,
        redis=redis,
        cache_ttl_seconds=settings.snapshot_cache_ttl_seconds,
        on_progress=on_progress,
    )
    logger.info("keşif tamamlandı: %s", summary.as_dict())
    # Sözleşme JobResult'ı businesses+snapshots+audit_id ister; keşif audit üretmez.
    data = summary.as_dict()
    return {
        "businesses": data["discovered"],
        "snapshots": data["snapshots_written"],
        "audit_id": None,
    }


def _build_llm_client(fixture_mode: bool) -> LLMClient | None:
    """Denetim sentezi için LLM istemcisi seç.

    Fixture modunda sahte istemci (canlı Anthropic yok, kural 6). Değilse ve anahtar
    varsa gerçek istemci. Anahtar yoksa None → yalnız deterministik faz (llm_cost=0,
    meşru): LLM çağrılmadıysa 0 kalabilir.
    """
    if fixture_mode:
        return FixtureLLMClient()
    api_key = get_settings().anthropic_api_key
    if api_key:
        return AnthropicLLMClient(api_key)
    return None


async def audit_task(ctx: dict[str, Any], *, business_id: int) -> dict[str, int | None]:
    """Derin denetim job'u: deterministik bulgu → Haiku sınıflandırma → Sonnet sentez.

    Nitelik kontrolü (`qualified` mi) uçta yapıldı; buraya yalnız uygun işletme gelir.
    Referans zaman fixture modunda `FIXTURE_REFERENCE_NOW`, üretimde `now`.
    """
    settings = get_settings()
    session_factory = ctx["session_factory"]
    reference_now = FIXTURE_REFERENCE_NOW if settings.radar_fixture_mode else datetime.now(UTC)
    llm_client = _build_llm_client(settings.radar_fixture_mode)

    audit_id = await run_audit(
        session_factory,
        business_id,
        reference_now,
        llm_client=llm_client,
        pdf_output_dir=settings.pdf_output_dir,
    )
    # Keşif sözleşmesiyle aynı JobResult şekli; denetimde businesses/snapshots 0.
    return {"businesses": 0, "snapshots": 0, "audit_id": audit_id}


async def purge_task(ctx: dict[str, Any]) -> dict[str, int]:
    """180 günlük silme cron'u (CLAUDE.md hukuki sınır — opsiyonel değil).

    Dönüşmeyen ve `retention_days` günden eski adayları (bağlı kayıtlar + PDF) siler.
    Referans zaman üretimde `now(UTC)`; `won` adaylar korunur (retention servisinde).
    """
    settings = get_settings()
    summary = await purge_old_candidates(
        ctx["session_factory"],
        reference_now=datetime.now(UTC),
        retention_days=settings.retention_days,
    )
    return summary.as_dict()


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    ctx["engine"] = engine
    ctx["session_factory"] = create_session_factory(engine)


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()


class WorkerSettings:
    """arq bu sınıfı okur: `arq api.worker.WorkerSettings`."""

    functions: ClassVar = [discovery_task, audit_task]
    # Silme cron'u her gün 03:00'te (düşük trafik). Opsiyonel değil (hukuki sınır).
    cron_jobs: ClassVar = [cron(purge_task, hour=3, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    # arq `redis_settings`'i bir değer olarak okur (fonksiyon değil). Import anında
    # get_settings() çağırıp DB zorunluluğu getirmemek için REDIS_URL doğrudan
    # ortamdan; yoksa yerel varsayılan.
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
