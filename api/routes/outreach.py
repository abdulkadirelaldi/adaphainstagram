"""`PATCH /outreach/{id}` — erişim kaydının durumunu günceller (SPEC §7).

**Bu uç mesaj GÖNDERMEZ.** Yalnız DB satırındaki `status`'ü (ve ilgili zaman
damgasını) günceller; insan kararını *kaydeder*. Hiçbir SMTP/DM/webhook/kuyruk-mesaj
yolu tetiklenmez (CLAUDE.md hukuki sınır). Geçersiz enum değeri Pydantic tarafından
422 ile reddedilir.
"""

from fastapi import APIRouter, HTTPException, Request, status

from api.models import Outreach as OutreachModel
from api.persistence import update_outreach_status
from api.schemas import Outreach, OutreachUpdate

router = APIRouter(tags=["outreach"])


def _to_outreach(model: OutreachModel) -> Outreach:
    # model.status ve şema alanı aynı enum (schemas OutreachStatus'ü models.enums'tan
    # re-export ediyor); doğrudan geçilir.
    return Outreach(
        id=model.id,
        audit_id=model.audit_id,
        channel=model.channel,
        draft=model.draft,
        status=model.status,
        sent_at=model.sent_at,
        replied_at=model.replied_at,
    )


@router.patch(
    "/outreach/{id}",
    summary="Erişim taslağının durumunu güncelle",
    operation_id="updateOutreach",
    response_model=Outreach,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Böyle bir erişim kaydı yok"},
    },
)
async def update_outreach_endpoint(
    id: int,  # noqa: A002  # yol parametresi sözleşmede `id`
    body: OutreachUpdate,
    request: Request,
) -> Outreach:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        # Yalnız durum kaydı — mesaj gönderme yok.
        outreach = await update_outreach_status(session, id, body.status)
        if outreach is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Erişim kaydı bulunamadı: {id}")
        await session.commit()
        return _to_outreach(outreach)
