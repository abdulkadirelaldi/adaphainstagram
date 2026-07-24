"""Erişim mesajı taslağını `outreach` tablosuna yazar / okur.

CLAUDE.md hukuki sınır: kayıt **`draft`** doğar ve orada kalır; sistem hiçbir koşulda
otomatik mesaj göndermez. Burada gönderme eylemi yoktur.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Outreach


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
