"""SEC-9 blok 3(DB)+4 — denetim uçtan uca: maliyet + gizlilik + hukuki sınır (gerçek DB).

100-hesap fixture'ıyla keşif+skorlama yapar, qualified bir işletmeyi FixtureLLMClient ile
denetler (canlı Anthropic yok, kural 6) ve doğrular:
- `audits.llm_cost_usd` > 0 ve Haiku+Sonnet toplamına eşit (maliyet disiplini).
- NOT NULL kısıtı DB seviyesinde zorlanıyor (llm_cost_usd atlanınca IntegrityError).
- `outreach` kaydı `draft` doğuyor (hukuki sınır — gönderme yok).
- Persist edilen metin/bulgularda yasak metrik (kural 7) yok.

Yalnız YEREL pg/redis; erişilemezse SKIP (conftest).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.adapters.apify import ApifyAdapter
from api.adapters.base import DiscoveryQuery
from api.adapters.business_discovery import BusinessDiscoveryAdapter
from api.adapters.places import PlacesAdapter
from api.llm.client import LLMUsage
from api.llm.cost import HAIKU_MODEL, SONNET_MODEL, compute_cost
from api.llm.fixture_client import FixtureLLMClient
from api.models import Audit, TriageScore
from api.models.enums import OutreachStatus, TriageStatus
from api.persistence import get_outreach_for_audit
from api.services import run_audit, run_discovery
from api.services.scoring import score_discovered
from tests._mocks import CallCounter, apify_client, bd_client, places_client

REFERENCE_NOW = datetime(2026, 7, 15, 0, 0, 0, tzinfo=UTC)

FORBIDDEN_TOKENS = (
    "impressions",
    "reach",
    "saves",
    "profile_visit",
    "profilevisits",
    "demographic",
    "follower_age",
    "age_range",
    "gender",
)


async def _populate_and_score(
    load_fixture: Any,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Any,
) -> None:
    places_raw = load_fixture("places_response")
    bd = load_fixture("ig_business_discovery")["profiles"]
    apify = load_fixture("apify_profile")["profiles"]
    pc, bc, ac = CallCounter(), CallCounter(), CallCounter()
    places_c = places_client(places_raw, pc)
    bd_c = bd_client(bd, bc)
    apify_c = apify_client(apify, ac)
    try:
        await run_discovery(
            DiscoveryQuery(query="samsun"),
            places=PlacesAdapter(client=places_c),
            profile_primary=BusinessDiscoveryAdapter(client=bd_c),
            profile_fallback=ApifyAdapter(client=apify_c),
            session_factory=session_factory,
            redis=redis,
            cache_ttl_seconds=7 * 24 * 60 * 60,
        )
    finally:
        await places_c.aclose()
        await bd_c.aclose()
        await apify_c.aclose()
    await score_discovered(session_factory, REFERENCE_NOW)


async def _a_qualified_business(session_factory: async_sessionmaker[AsyncSession]) -> int:
    async with session_factory() as session:
        bid: int | None = await session.scalar(
            select(TriageScore.business_id)
            .where(TriageScore.status == TriageStatus.QUALIFIED)
            .limit(1)
        )
    assert bid is not None, "Fixture'da qualified işletme bekleniyordu (SEC-8 bantları)"
    return bid


async def test_llm_cost_sifir_degil_ve_haiku_arti_sonnet(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """LLM'li denetim sonrası llm_cost_usd > 0 ve Haiku+Sonnet fixture usage toplamına eşit."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)

    audit_id = await run_audit(
        db_session_factory, bid, REFERENCE_NOW, llm_client=FixtureLLMClient()
    )
    async with db_session_factory() as session:
        audit = await session.get(Audit, audit_id)
    assert audit is not None
    assert audit.llm_cost_usd > 0  # maliyet disiplini: boş/0 kalamaz (LLM çağrıldı)

    # Beklenen = Haiku (usage 1200/300) + Sonnet (usage 1800/500), FixtureLLMClient sabitleri.
    # İşletmenin ≤30 gönderisi var → 1 Haiku çağrısı + 1 Sonnet çağrısı.
    as_of = REFERENCE_NOW.date()
    expected = (
        compute_cost(HAIKU_MODEL, LLMUsage(input_tokens=1200, output_tokens=300), as_of).cost_usd
        + compute_cost(SONNET_MODEL, LLMUsage(input_tokens=1800, output_tokens=500), as_of).cost_usd
    )
    assert audit.llm_cost_usd == expected


async def test_llm_client_yoksa_maliyet_sifir_mesru(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """LLM çağrılmayan (deterministik) denetimde llm_cost_usd=0 meşru (gerçek maliyet 0, NULL değil)."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)

    audit_id = await run_audit(db_session_factory, bid, REFERENCE_NOW, llm_client=None)
    async with db_session_factory() as session:
        audit = await session.get(Audit, audit_id)
    assert audit is not None
    assert audit.llm_cost_usd == 0
    assert audit.report_text is None  # LLM yok → rapor metni yok


async def test_llm_cost_not_null_db_seviyesinde_zorlaniyor(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """`audits.llm_cost_usd` NOT NULL — atlanınca DB IntegrityError (BE-2 kısıtı)."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)

    async with db_session_factory() as session:
        # llm_cost_usd BİLEREK verilmiyor → NOT NULL ihlali.
        session.add(Audit(business_id=bid, visibility_score=50.0, findings=[]))
        with pytest.raises(IntegrityError):
            await session.flush()


async def test_outreach_draft_doguyor(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """LLM'li denetim outreach kaydı üretir ve `status=draft` doğar (hukuki sınır)."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)
    audit_id = await run_audit(
        db_session_factory, bid, REFERENCE_NOW, llm_client=FixtureLLMClient()
    )
    async with db_session_factory() as session:
        outreach = await get_outreach_for_audit(session, audit_id)
    assert outreach is not None
    assert outreach.status is OutreachStatus.DRAFT
    assert outreach.draft  # taslak metin var


async def test_persist_edilen_denetimde_yasak_metrik_yok(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """audits.findings/report_text ve outreach.draft'ta yasak metrik (kural 7) yok."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)
    audit_id = await run_audit(
        db_session_factory, bid, REFERENCE_NOW, llm_client=FixtureLLMClient()
    )
    async with db_session_factory() as session:
        audit = await session.get(Audit, audit_id)
        outreach = await get_outreach_for_audit(session, audit_id)
    assert audit is not None and outreach is not None

    blob = " ".join(
        [
            json.dumps(audit.findings, ensure_ascii=False),
            audit.report_text or "",
            outreach.draft,
        ]
    ).lower()
    for tok in FORBIDDEN_TOKENS:
        # "outreach" içindeki "reach" yanılmasın diye kelime bağlamıyla kontrol.
        if tok == "reach":
            assert "reach" not in blob.replace("outreach", "")
        else:
            assert tok not in blob, f"denetim çıktısında yasak metrik: {tok!r}"


async def test_bulgu_mesajlari_yalniz_var_olan_kurala_bagli(
    load_fixture: Any,
    db_session_factory: async_sessionmaker[AsyncSession],
    test_redis: Any,
) -> None:
    """Persist edilen her bulgunun `message`'ı LLM'den; deterministik `detail` ayrı alan (icat yok)."""
    await _populate_and_score(load_fixture, db_session_factory, test_redis)
    bid = await _a_qualified_business(db_session_factory)
    audit_id = await run_audit(
        db_session_factory, bid, REFERENCE_NOW, llm_client=FixtureLLMClient()
    )
    async with db_session_factory() as session:
        audit = await session.get(Audit, audit_id)
    assert audit is not None
    for finding in audit.findings:
        # Her bulgu deterministik detail + LLM message ayrı taşır (BE-14 detail, BE-16 message).
        assert finding["detail"]
        assert finding["message"]  # FixtureLLMClient her kurala mesaj bağlar
        assert finding["rule"]
