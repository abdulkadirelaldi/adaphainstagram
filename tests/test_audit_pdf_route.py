"""SEC-10 blok 1 (route) — GET /audits/{id}/pdf indirme (SPEC §7, BE-17 sözleşmesi).

Üretilmiş audit → 200 + application/pdf + magic bytes; pdf_path boş → 409; olmayan → 404.
200 yolu gerçek PDF dosyası ister (headless Chromium); yoksa SKIP. Yalnız yerel pg (kural 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.main import create_app
from api.models import Audit, Business
from api.pdf import render_pdf


@pytest_asyncio.fixture
async def client(db_session_factory: async_sessionmaker[AsyncSession]) -> Any:
    app = create_app()
    app.state.session_factory = db_session_factory
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def _make_audit(
    session_factory: async_sessionmaker[AsyncSession], *, pdf_path: str | None
) -> int:
    async with session_factory() as session:
        biz = Business(place_id="ChIJpdfroute", name="PDF İşletme")
        session.add(biz)
        await session.flush()
        audit = Audit(
            business_id=biz.id,
            visibility_score=41.0,
            findings=[],
            llm_cost_usd=0,
            pdf_path=pdf_path,
        )
        session.add(audit)
        await session.flush()
        aid = audit.id
        await session.commit()
    return aid


async def test_pdf_yoksa_409(
    client: httpx.AsyncClient, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """pdf_path=None (deterministik denetim, sentez koşmadı) → 409."""
    aid = await _make_audit(db_session_factory, pdf_path=None)
    resp = await client.get(f"/audits/{aid}/pdf")
    assert resp.status_code == 409


async def test_olmayan_audit_404(client: httpx.AsyncClient) -> None:
    resp = await client.get("/audits/999999/pdf")
    assert resp.status_code == 404


async def test_pdf_yol_var_ama_dosya_yok_409(
    client: httpx.AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """pdf_path dolu ama dosya diskte yok → 409 (route dosya varlığını doğruluyor)."""
    aid = await _make_audit(db_session_factory, pdf_path=str(tmp_path / "olmayan_dosya.pdf"))
    resp = await client.get(f"/audits/{aid}/pdf")
    assert resp.status_code == 409


async def test_uretilmis_pdf_200_ve_magic_bytes(
    client: httpx.AsyncClient,
    db_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """Gerçek PDF dosyası olan audit → 200 + application/pdf + %PDF-. Chromium yoksa SKIP."""
    try:
        pdf_bytes = await render_pdf("<html><body><h1>Denetim Raporu</h1></body></html>")
    except Exception as exc:
        pytest.skip(f"Headless Chromium yok: {exc!r}")

    pdf_file = tmp_path / "audit.pdf"
    pdf_file.write_bytes(pdf_bytes)
    aid = await _make_audit(db_session_factory, pdf_path=str(pdf_file))

    resp = await client.get(f"/audits/{aid}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
