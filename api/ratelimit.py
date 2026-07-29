"""Rate limit — ağır uçlar için Redis-tabanlı sabit-pencere sayacı (Faz 6 sertleştirme).

`rate_limited("bucket")` bir FastAPI bağımlılığı üretir; ağır uçlara eklenir. İstemci
(IP) + bucket başına dakikada `rate_limit_per_minute` istek; aşılınca `429` + `Retry-After`
(pencere sonuna kalan saniye). Redis yoksa (hermetik test / redis inik) sınır **uygulanmaz**
— fail-open, uç normal çalışır.

CORS/origin listesi bu katmandan bağımsız; değişmez.
"""

from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status

from api.config import get_settings

_WINDOW_SECONDS = 60


def rate_limited(bucket: str) -> Callable[[Request], Awaitable[None]]:
    """Verilen bucket için dakikalık istek sınırı uygulayan bağımlılık üretir."""

    async def dependency(request: Request) -> None:
        # Sağlık yoklamasının redis'i (lifespan kurar). Hermetik/e2e testlerde yok →
        # fail-open (sınır uygulanmaz, uç normal çalışır).
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return

        client = request.client.host if request.client else "unknown"
        key = f"radar:ratelimit:{bucket}:{client}"
        count = await redis.incr(key)
        if count == 1:
            # Penceredeki ilk istek: TTL kur (sabit pencere).
            await redis.expire(key, _WINDOW_SECONDS)

        limit = get_settings().rate_limit_per_minute
        if count > limit:
            ttl = await redis.ttl(key)
            retry_after = ttl if isinstance(ttl, int) and ttl > 0 else _WINDOW_SECONDS
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hız sınırı aşıldı. Lütfen bir süre sonra tekrar deneyin.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
