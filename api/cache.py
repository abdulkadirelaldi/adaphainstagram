"""Redis istemcisi.

Faz 1'de yalnızca sağlık yoklaması için kullanılır. Faz 2'de adaptör seviyesindeki
7 günlük scrape cache'i de bu bağlantı havuzunu paylaşacak (CLAUDE.md maliyet
disiplini).
"""

from typing import cast

from redis.asyncio import Redis

from api.config import Settings


def create_redis(settings: Settings) -> Redis:
    # from_url stub'ı Any döndürüyor (redis 5.x); açık cast warn_return_any'i susturur.
    return cast(
        Redis,
        Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=settings.health_timeout_seconds,
        ),
    )
