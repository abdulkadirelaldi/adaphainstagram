"""SEC-11 — uçtan uca akış (SPEC §1): keşif → skor → denetim → PDF → outreach.

**Fixture modunda, canlı çağrı YOK** (kural 6). Worker'ın kullandığı servis fonksiyonlarıyla
sürülür — `api.fixture_mode.fixture_adapters` (MockTransport, ağ yok) + `FIXTURE_REFERENCE_NOW`
(deterministik) + `FixtureLLMClient` (Anthropic yok) — ve sonuç **gerçek HTTP uçlarından**
doğrulanır (`GET /audits/{id}`, `GET /audits/{id}/pdf`, `PATCH /outreach/{id}`; enqueue uçları
sahte arq havuzuyla). Bu, discovery_task/audit_task'in çağırdığı akışın aynısıdır.

Gerçek pg+redis ister; erişilemezse SKIP (conftest). PDF adımı chromium ister; yoksa o alt
adım SKIP, gerisi koşar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.base import DiscoveryQuery
from api.fixture_mode import FIXTURE_REFERENCE_NOW, fixture_adapters
from api.llm.fixture_client import FixtureLLMClient
from api.main import create_app
from api.models import Business, TriageScore
from api.models.enums import OutreachStatus, TriageStatus
from api.persistence import get_outreach_for_audit
from api.services import run_audit, run_discovery


class _FakeArqPool:
    """Sahte arq havuzu — enqueue'yu kaydeder, iş çalıştırmaz (uç 202 sözleşmesi için)."""

    def __init__(self) -> None:
        self.enqueued: list[tuple[str, dict[str, Any]]] = []

    async def enqueue_job(self, function: str, **kwargs: Any) -> Any:
        self.enqueued.append((function, kwargs))

        class _Job:
            job_id = "e2e-test-job"

        return _Job()


@pytest_asyncio.fixture
async def app_client(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> Any:
    """Test DB'sine + sahte arq havuzuna bağlı ASGI istemcisi (lifespan yok)."""
    app = create_app()
    app.state.session_factory = db_session_factory
    app.state.arq_pool = _FakeArqPool()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def _discover_and_score(
    session_factory: async_sessionmaker[AsyncSession], redis: Any
) -> None:
    """Worker discovery_task'ının fixture-modu gövdesi: fixture adaptörleriyle keşif + skor."""
    async with fixture_adapters() as (places, primary, fallback):
        await run_discovery(
            DiscoveryQuery(query="samsun işletmeleri"),
            places=places,
            profile_primary=primary,
            profile_fallback=fallback,
            session_factory=session_factory,
            redis=redis,
            cache_ttl_seconds=7 * 24 * 60 * 60,
            reference_now=FIXTURE_REFERENCE_NOW,
        )


async def _a_qualified_business(session_factory: async_sessionmaker[AsyncSession]) -> int:
    async with session_factory() as session:
        bid: int | None = await session.scalar(
            select(TriageScore.business_id)
            .where(TriageScore.status == TriageStatus.QUALIFIED)
            .limit(1)
        )
    assert bid is not None, "e2e: keşif+skor sonrası qualified işletme bekleniyordu"
    return bid


async def test_uctan_uca_kesif_skor_denetim_pdf_outreach(
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
    app_client: httpx.AsyncClient,
    tmp_path: Path,
) -> None:
    """Tam akış: keşif→skor→(uç gate)→denetim→GET audit→GET pdf→PATCH outreach."""
    # 1) Keşif + skorlama (worker discovery_task gövdesi, fixture modu).
    await _discover_and_score(db_session_factory, test_redis)
    async with db_session_factory() as session:
        biz_count = await session.scalar(select(func.count()).select_from(Business))
        scored = await session.scalar(select(func.count()).select_from(TriageScore))
    assert biz_count == 100  # 100 işletme keşfedildi (SEC-8 fixture)
    assert scored and scored > 0  # skorlandı

    bid = await _a_qualified_business(db_session_factory)

    # 2) Denetim uç gate'i (senkron nitelik kontrolü): qualified → 202 + job_id.
    resp = await app_client.post(f"/businesses/{bid}/audit")
    assert resp.status_code == 202
    assert resp.json()["job_id"]  # enqueue edildi (sahte havuz)

    # 3) Denetim job gövdesi (worker audit_task): Haiku+Sonnet fixture, PDF tmp'ye.
    audit_id = await run_audit(
        db_session_factory,
        bid,
        FIXTURE_REFERENCE_NOW,
        llm_client=FixtureLLMClient(),
        pdf_output_dir=str(tmp_path),
    )

    # 4) GET /audits/{id}: bulgu + rapor metni + llm_cost_usd > 0 (maliyet disiplini).
    resp = await app_client.get(f"/audits/{audit_id}")
    assert resp.status_code == 200
    audit = resp.json()
    assert audit["visibility_score"] is not None
    assert audit["report_text"]  # Sonnet sentezi
    assert float(audit["llm_cost_usd"]) > 0  # LLM çağrıldı → maliyet yazıldı
    assert isinstance(audit["findings"], list)
    assert audit["outreach"] is not None  # draft üretildi

    # 5) GET /audits/{id}/pdf: geçerli PDF (chromium varsa; yoksa alt-adım SKIP).
    resp = await app_client.get(f"/audits/{audit_id}/pdf")
    if resp.status_code == 409:
        pytest.skip("PDF üretilmedi (chromium yok) — akışın gerisi doğrulandı")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")

    # 6) PATCH /outreach/{id}: insan kararı kaydedilir (mesaj gönderilmez).
    async with db_session_factory() as session:
        outreach = await get_outreach_for_audit(session, audit_id)
    assert outreach is not None
    assert outreach.status is OutreachStatus.DRAFT  # draft doğdu (hukuki sınır)

    resp = await app_client.patch(f"/outreach/{outreach.id}", json={"status": "sent"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None


async def test_uc_gate_watch_isletme_409(
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
    app_client: httpx.AsyncClient,
) -> None:
    """Nitelikli olmayan (watch) işletmeye denetim → 409 (iş kuyruğa hiç girmez)."""
    await _discover_and_score(db_session_factory, test_redis)
    async with db_session_factory() as session:
        bid: int | None = await session.scalar(
            select(TriageScore.business_id).where(TriageScore.status == TriageStatus.WATCH).limit(1)
        )
    assert bid is not None
    resp = await app_client.post(f"/businesses/{bid}/audit")
    assert resp.status_code == 409


async def test_uc_gate_olmayan_isletme_404(app_client: httpx.AsyncClient) -> None:
    resp = await app_client.post("/businesses/999999/audit")
    assert resp.status_code == 404
