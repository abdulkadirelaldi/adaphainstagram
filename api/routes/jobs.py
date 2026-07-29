"""`POST /discovery/run` ve `GET /jobs/{id}` — kuyruk uçları (SPEC §7).

POST işi arq'ya atar ve **anında** `job_id` döner; senkron scraping yok. GET arq iş
durumunu sözleşmedeki `JobState` enum'una eşler.
"""

from typing import cast

from arq import ArqRedis
from arq.jobs import Job
from arq.jobs import JobStatus as ArqJobStatus
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.jobstate import read_progress
from api.ratelimit import rate_limited
from api.schemas import (
    DiscoveryRequest,
    JobAccepted,
    JobResult,
    JobState,
    JobStatus,
)

router = APIRouter(tags=["discovery", "jobs"])

# arq iş durumu → sözleşme JobState. `complete` başarı/hata ayrımı result_info ile.
_STATE_MAP = {
    ArqJobStatus.deferred: JobState.QUEUED,
    ArqJobStatus.queued: JobState.QUEUED,
    ArqJobStatus.in_progress: JobState.RUNNING,
}


def _require_pool(request: Request) -> ArqRedis:
    """arq havuzunu döndürür; redis inikken açılamadıysa 503."""
    pool = request.app.state.arq_pool
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kuyruk servisi kullanılamıyor (redis).",
        )
    return cast(ArqRedis, pool)


@router.post(
    "/discovery/run",
    tags=["discovery"],
    summary="Keşif taraması başlat",
    operation_id="runDiscovery",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAccepted,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Hız sınırı aşıldı (Retry-After)"},
    },
    dependencies=[Depends(rate_limited("discovery"))],
)
async def run_discovery_endpoint(body: DiscoveryRequest, request: Request) -> JobAccepted:
    pool = _require_pool(request)
    job = await pool.enqueue_job(
        "discovery_task",
        query=body.query,
        region=body.region,
        limit=body.limit,
    )
    if job is None:
        # Yalnızca aynı job_id zaten kuyruktaysa olur; benzersiz kimlik vermediğimiz
        # için beklenmez ama tip güvenliği için ele alınır.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="İş kuyruğa alınamadı (çakışan iş kimliği).",
        )
    return JobAccepted(job_id=job.job_id)


@router.get(
    "/jobs/{id}",
    tags=["jobs"],
    summary="Kuyruk işinin durumu",
    operation_id="getJob",
    response_model=JobStatus,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Böyle bir iş yok"}},
)
async def get_job(id: str, request: Request) -> JobStatus:  # noqa: A002  # yol parametresi sözleşmede `id`
    redis = _require_pool(request)
    job = Job(id, redis=redis)
    arq_status = await job.status()

    if arq_status == ArqJobStatus.not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"İş bulunamadı: {id}",
        )

    progress = await read_progress(redis, id)
    state = _STATE_MAP.get(arq_status)
    result: JobResult | None = None
    error: str | None = None

    if arq_status == ArqJobStatus.complete:
        info = await job.result_info()
        if info is not None and info.success:
            state = JobState.DONE
            data = info.result
            audit_id = data.get("audit_id")
            result = JobResult(
                businesses=int(data.get("businesses", 0)),
                snapshots=int(data.get("snapshots", 0)),
                audit_id=int(audit_id) if audit_id is not None else None,
            )
        else:
            state = JobState.ERROR
            error = str(info.result) if info is not None else "bilinmeyen hata"

    if state is None:  # pragma: no cover - arq beklenmedik durum
        state = JobState.RUNNING

    return JobStatus(
        job_id=id,
        status=state,
        progress=progress,
        result=result,
        error=error,
    )
