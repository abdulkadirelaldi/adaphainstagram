"""Erişim mesajı taslağını `outreach` tablosuna yazar / okur / durumunu günceller.

CLAUDE.md hukuki sınır: kayıt **`draft`** doğar; sistem hiçbir koşulda otomatik mesaj
göndermez. Durum güncelleme **yalnız DB satırını değiştirir** — hiçbir SMTP/DM/webhook/
kuyruk-mesaj yolu tetiklemez. Bu modülde gönderme eylemi yoktur.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Outreach
from api.models.enums import OutreachStatus


async def persist_outreach(
    session: AsyncSession, *, audit_id: int, channel: str, draft: str
) -> Outreach:
    """Denetime bağlı bir taslak erişim kaydı oluşturur. `status` varsayılan `draft`."""
    outreach = Outreach(audit_id=audit_id, channel=channel, draft=draft)
    session.add(outreach)
    await session.flush()
    return outreach


async def get_outreach_for_audit(session: AsyncSession, audit_id: int) -> Outreach | None:
    """Denetimin en son erişim taslağı; yoksa `None`."""
    result: Outreach | None = await session.scalar(
        select(Outreach).where(Outreach.audit_id == audit_id).order_by(Outreach.id.desc()).limit(1)
    )
    return result


async def update_outreach_status(
    session: AsyncSession, outreach_id: int, new_status: OutreachStatus
) -> Outreach | None:
    """Erişim kaydının durumunu günceller — **yalnız kaydeder, mesaj göndermez**.

    **Geçiş grafiği zorlanmaz** (bilinçli karar): yedi durumun herhangi birine geçişe
    izin verilir. Gerekçe — bu bir insan-yönetimli CRM alanı; gerçek dünya lineer
    ilerlemez (yanıt "opened" sinyali olmadan gelebilir, doğrudan "meeting"e atlanabilir).
    Yapay bir pipeline dayatmak insanı gereksiz kısıtlar (CLAUDE.md ruhuna aykırı).
    Enum-dışı değer zaten uçta 422 ile reddedilir.

    Uygun geçişte zaman damgası ilk kez set edilir (`sent`→`sent_at`, `replied`→
    `replied_at`; SPEC §3). Kayıt yoksa `None`.
    """
    outreach = await session.get(Outreach, outreach_id)
    if outreach is None:
        return None
    outreach.status = new_status
    now = datetime.now(UTC)
    if new_status is OutreachStatus.SENT and outreach.sent_at is None:
        outreach.sent_at = now
    if new_status is OutreachStatus.REPLIED and outreach.replied_at is None:
        outreach.replied_at = now
    await session.flush()
    return outreach
