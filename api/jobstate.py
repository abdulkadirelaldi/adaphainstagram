"""İş ilerleme durumu — Redis'te.

arq bir işin ilerlemesini (kaç öğe işlendi) yerel olarak tutmaz; job yürürken bu
sayaçları Redis'e yazarız, `GET /jobs/{id}` de buradan okur. İş sonucu (özet) arq'nın
kendi sonuç deposundadır; burası yalnız ara ilerleme.
"""

import json

from redis.asyncio import Redis

from api.schemas import JobProgress

_PROGRESS_KEY = "radar:job:{job_id}:progress"
# İlerleme kaydı işin ömrüyle sınırlı; bir saat sonra kendini temizler.
_PROGRESS_TTL_SECONDS = 60 * 60


def _key(job_id: str) -> str:
    return _PROGRESS_KEY.format(job_id=job_id)


async def write_progress(redis: Redis, job_id: str, processed: int, total: int) -> None:
    payload = json.dumps({"processed": processed, "total": total})
    await redis.set(_key(job_id), payload, ex=_PROGRESS_TTL_SECONDS)


async def read_progress(redis: Redis, job_id: str) -> JobProgress | None:
    raw = await redis.get(_key(job_id))
    if raw is None:
        return None
    data = json.loads(raw)
    return JobProgress(processed=data["processed"], total=data["total"])
