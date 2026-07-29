"""`POST /businesses/{id}/audit` ve `GET /audits/{id}` — denetim uçları (SPEC §7).

POST yalnız `qualified` işletme için denetimi arq'ya atar ve **anında** `job_id` döner
(senkron değil; `/discovery/run` ile aynı desen). GET denetim sonucunu `Audit` şemasına
göre döndürür. Denetim `job_id`'si tamamlanınca `GET /jobs/{id}` sonucundaki `audit_id`
ile buraya gelinir.
"""

from pathlib import Path
from typing import Any, cast

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from api.models import Audit as AuditModel
from api.models import Outreach as OutreachModel
from api.persistence import get_audit, get_outreach_for_audit
from api.ratelimit import rate_limited
from api.schemas import Audit, Finding, JobAccepted, OutreachDraft, OutreachStatus, Severity
from api.services import NotAuditableError, assert_auditable

router = APIRouter(tags=["audits"])


def _require_pool(request: Request) -> ArqRedis:
    pool = request.app.state.arq_pool
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kuyruk servisi kullanılamıyor (redis).",
        )
    return cast(ArqRedis, pool)


@router.post(
    "/businesses/{id}/audit",
    summary="Derin denetimi kuyruğa al",
    operation_id="runAudit",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAccepted,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Böyle bir işletme yok"},
        status.HTTP_409_CONFLICT: {"description": "İşletme derin denetime uygun değil"},
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Hız sınırı aşıldı (Retry-After)"},
    },
    dependencies=[Depends(rate_limited("audit"))],
)
async def run_audit_endpoint(id: int, request: Request) -> JobAccepted:  # noqa: A002  # yol param sözleşmede `id`
    session_factory = request.app.state.session_factory
    # Nitelik kontrolü uçta (senkron): uygun değilse iş kuyruğa hiç girmez.
    async with session_factory() as session:
        try:
            await assert_auditable(session, id)
        except LookupError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except NotAuditableError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    pool = _require_pool(request)
    job = await pool.enqueue_job("audit_task", business_id=id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Denetim işi kuyruğa alınamadı (çakışan iş kimliği).",
        )
    return JobAccepted(job_id=job.job_id)


def _to_finding(raw: dict[str, Any]) -> Finding:
    return Finding(
        rule=raw["rule"],
        title=raw["title"],
        severity=Severity(raw["severity"]),
        detail=raw["detail"],
        message=raw.get("message"),
    )


def _to_outreach(model: OutreachModel | None) -> OutreachDraft | None:
    if model is None:
        return None
    return OutreachDraft(
        id=model.id,
        channel=model.channel,
        draft=model.draft,
        status=OutreachStatus(model.status.value),
    )


def _to_audit(model: AuditModel, outreach: OutreachModel | None) -> Audit:
    return Audit(
        id=model.id,
        business_id=model.business_id,
        visibility_score=float(model.visibility_score),
        findings=[_to_finding(f) for f in model.findings],
        report_text=model.report_text,
        pdf_path=model.pdf_path,
        llm_cost_usd=float(model.llm_cost_usd),
        generated_at=model.generated_at,
        outreach=_to_outreach(outreach),
    )


@router.get(
    "/audits/{id}",
    summary="Denetim sonucu",
    operation_id="getAudit",
    response_model=Audit,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Böyle bir denetim yok"}},
)
async def get_audit_endpoint(id: int, request: Request) -> Audit:  # noqa: A002  # yol param sözleşmede `id`
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        audit = await get_audit(session, id)
        if audit is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Denetim bulunamadı: {id}")
        outreach = await get_outreach_for_audit(session, id)
        return _to_audit(audit, outreach)


@router.get(
    "/audits/{id}/pdf",
    summary="Denetim raporunu PDF olarak indir",
    operation_id="getAuditPdf",
    response_class=FileResponse,
    responses={
        status.HTTP_200_OK: {"content": {"application/pdf": {}}, "description": "PDF raporu"},
        status.HTTP_404_NOT_FOUND: {"description": "Böyle bir denetim yok"},
        status.HTTP_409_CONFLICT: {"description": "PDF henüz üretilmedi"},
    },
)
async def get_audit_pdf(id: int, request: Request) -> FileResponse:  # noqa: A002  # yol param sözleşmede `id`
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        audit = await get_audit(session, id)
        if audit is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Denetim bulunamadı: {id}")
        pdf_path = audit.pdf_path
    # pdf_path boşsa (sentez/PDF fazı koşmadı) → 409 (BE-17 sözleşmesi).
    if not pdf_path or not Path(pdf_path).is_file():
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"Denetim {id} PDF'i henüz üretilmedi."
        )
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"denetim_{id}.pdf")
