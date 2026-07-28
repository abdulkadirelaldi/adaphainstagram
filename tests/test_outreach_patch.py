"""SEC-10 blok 2 — PATCH /outreach/{id} durum geçişi + persist (gerçek DB).

`PATCH /outreach/{id}` yalnız durumu kaydeder (mesaj göndermez, hukuki sınır); geçerli
geçişte zaman damgası (`sent`→`sent_at`, `replied`→`replied_at`), geçersiz enum→422,
fazladan alan→422 (extra=forbid), olmayan kayıt→404. BE-19 geçiş grafiğini zorlamıyor.

Yalnız YEREL pg (kural 6); erişilemezse SKIP. Route ASGI taşımasıyla, canlı sunucu yok.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.main import create_app
from api.models import Audit, Business, Outreach
from api.models.enums import OutreachStatus
from api.persistence.outreach import update_outreach_status


async def _make_outreach(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Bir işletme→audit→outreach(draft) zinciri kurar; outreach id döner."""
    async with session_factory() as session:
        biz = Business(place_id="ChIJsec10", name="Test İşletme")
        session.add(biz)
        await session.flush()
        audit = Audit(business_id=biz.id, visibility_score=50.0, findings=[], llm_cost_usd=0)
        session.add(audit)
        await session.flush()
        outreach = Outreach(audit_id=audit.id, channel="instagram_dm", draft="Merhaba!")
        session.add(outreach)
        await session.flush()
        oid = outreach.id
        await session.commit()
    return oid


@pytest_asyncio.fixture
async def client(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> Any:
    """`app.state.session_factory`'yi test DB'sine bağlar; ASGI istemcisi verir (lifespan yok)."""
    app = create_app()
    app.state.session_factory = db_session_factory
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# --- Persist fonksiyonu (DB, route'suz) -----------------------------------------


async def test_persist_sent_zaman_damgasi(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    oid = await _make_outreach(db_session_factory)
    async with db_session_factory() as session:
        row = await update_outreach_status(session, oid, OutreachStatus.SENT)
        await session.commit()
    assert row is not None
    assert row.status is OutreachStatus.SENT
    assert row.sent_at is not None
    assert row.replied_at is None


async def test_persist_replied_sent_at_korunuyor(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """draft→sent→replied: replied_at damgalanır, sent_at ilk değeriyle korunur."""
    oid = await _make_outreach(db_session_factory)
    async with db_session_factory() as session:
        await update_outreach_status(session, oid, OutreachStatus.SENT)
        await session.commit()
    async with db_session_factory() as session:
        row = await session.get(Outreach, oid)
        assert row is not None
        first_sent = row.sent_at
    async with db_session_factory() as session:
        row = await update_outreach_status(session, oid, OutreachStatus.REPLIED)
        await session.commit()
    assert row is not None
    assert row.replied_at is not None
    assert row.sent_at == first_sent  # yeniden damgalanmadı


async def test_persist_olmayan_kayit_none(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with db_session_factory() as session:
        assert await update_outreach_status(session, 999999, OutreachStatus.SENT) is None


# --- Route (PATCH /outreach/{id}) -----------------------------------------------


async def test_patch_gecerli_gecis_200_ve_damga(
    client: httpx.AsyncClient, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    oid = await _make_outreach(db_session_factory)
    resp = await client.patch(f"/outreach/{oid}", json={"status": "sent"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None
    # Yanıt yalnız SPEC §3 alanları — gönderme/eylem alanı yok.
    assert set(body) == {"id", "audit_id", "channel", "draft", "status", "sent_at", "replied_at"}


async def test_patch_gecis_grafigi_zorlanmiyor(
    client: httpx.AsyncClient, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """BE-19 kararı: draft'tan doğrudan 'meeting'e geçiş serbest (insan-yönetimli CRM)."""
    oid = await _make_outreach(db_session_factory)
    resp = await client.patch(f"/outreach/{oid}", json={"status": "meeting"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "meeting"


async def test_patch_gecersiz_enum_422(client: httpx.AsyncClient, db_session_factory: Any) -> None:
    oid = await _make_outreach(db_session_factory)
    resp = await client.patch(f"/outreach/{oid}", json={"status": "gonderildi_bilinmeyen"})
    assert resp.status_code == 422


async def test_patch_fazladan_gonderme_alani_422(
    client: httpx.AsyncClient, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """extra=forbid: gövdeye 'send'/kanal-tetikleme alanı eklemek yapısal olarak reddedilir."""
    oid = await _make_outreach(db_session_factory)
    resp = await client.patch(f"/outreach/{oid}", json={"status": "sent", "send": True})
    assert resp.status_code == 422


async def test_patch_olmayan_kayit_404(client: httpx.AsyncClient) -> None:
    resp = await client.patch("/outreach/999999", json={"status": "sent"})
    assert resp.status_code == 404
