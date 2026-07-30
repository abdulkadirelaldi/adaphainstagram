"""SEC-12 blok 1 — 180 günlük silme cron'u (api/services/retention.py, hukuki sınır).

Dönüşmeyen ve `retention_days` günden eski aday + bağlı tüm kayıtlar (CASCADE) + PDF
siliniyor; **`won` aday korunuyor**; taze aday korunuyor; sınır (180. gün) off-by-one.
Referans zaman **enjekte** — `datetime.now()` yok, deterministik. Yalnız yerel pg (kural 6).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.models import Audit, Business, Outreach
from api.models.enums import OutreachStatus
from api.services.retention import _cutoff, _deletable_business_ids, purge_old_candidates

REFERENCE_NOW = datetime(2026, 7, 15, 0, 0, 0, tzinfo=UTC)
RETENTION_DAYS = 180
CUTOFF = REFERENCE_NOW - timedelta(days=RETENTION_DAYS)  # 2026-01-16


async def _make_business(
    session: AsyncSession,
    *,
    place_id: str,
    discovered_at: datetime,
    won: bool = False,
    pdf_path: str | None = None,
) -> int:
    biz = Business(place_id=place_id, name=f"İşletme {place_id}", discovered_at=discovered_at)
    session.add(biz)
    await session.flush()
    if won or pdf_path is not None:
        audit = Audit(
            business_id=biz.id,
            visibility_score=50.0,
            findings=[],
            llm_cost_usd=0,
            pdf_path=pdf_path,
        )
        session.add(audit)
        await session.flush()
        if won:
            session.add(
                Outreach(
                    audit_id=audit.id,
                    channel="instagram_dm",
                    draft="x",
                    status=OutreachStatus.WON,
                )
            )
    await session.flush()
    return biz.id


def test_cutoff_saf_hesap() -> None:
    """_cutoff saf ve deterministik: referans − retention_days."""
    assert _cutoff(REFERENCE_NOW, 180) == CUTOFF
    assert _cutoff(REFERENCE_NOW, 1) == REFERENCE_NOW - timedelta(days=1)


async def test_eski_donusmemis_silinir_won_ve_taze_korunur(
    db_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    """180 günden eski dönüşmemiş → silinir (PDF dahil); won ve taze → korunur."""
    old_pdf = tmp_path / "old.pdf"
    old_pdf.write_bytes(b"%PDF-old")
    won_pdf = tmp_path / "won.pdf"
    won_pdf.write_bytes(b"%PDF-won")

    async with db_session_factory() as session:
        old_id = await _make_business(
            session,
            place_id="old",
            discovered_at=REFERENCE_NOW - timedelta(days=200),
            pdf_path=str(old_pdf),
        )
        won_id = await _make_business(
            session,
            place_id="won",
            discovered_at=REFERENCE_NOW - timedelta(days=200),
            won=True,
            pdf_path=str(won_pdf),
        )
        fresh_id = await _make_business(
            session,
            place_id="fresh",
            discovered_at=REFERENCE_NOW - timedelta(days=10),
        )
        await session.commit()

    summary = await purge_old_candidates(
        db_session_factory, reference_now=REFERENCE_NOW, retention_days=RETENTION_DAYS
    )

    async with db_session_factory() as session:
        remaining = set((await session.execute(select(Business.id))).scalars().all())
    assert old_id not in remaining  # eski dönüşmemiş silindi
    assert won_id in remaining  # dönüşen müşteri korundu (hukuki karar)
    assert fresh_id in remaining  # taze aday korundu
    assert summary.deleted_businesses == 1
    # Silinen adayın PDF'i diskten gitti; won'unki durdu.
    assert not old_pdf.exists()
    assert won_pdf.exists()
    assert summary.removed_pdfs == 1


async def test_cascade_bagli_kayitlari_siliyor(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Silinen işletmenin audit/outreach zinciri CASCADE ile gidiyor (yetim kayıt yok)."""
    async with db_session_factory() as session:
        bid = await _make_business(
            session,
            place_id="cascade",
            discovered_at=REFERENCE_NOW - timedelta(days=200),
            pdf_path=None,
        )
        audit = Audit(business_id=bid, visibility_score=10.0, findings=[], llm_cost_usd=0)
        session.add(audit)
        await session.flush()
        session.add(Outreach(audit_id=audit.id, channel="x", draft="y"))
        await session.commit()

    await purge_old_candidates(
        db_session_factory, reference_now=REFERENCE_NOW, retention_days=RETENTION_DAYS
    )
    async with db_session_factory() as session:
        assert await session.scalar(select(Audit).where(Audit.business_id == bid)) is None
        # Outreach de gitti (audit CASCADE).
        orphan = await session.scalar(select(Outreach))
        assert orphan is None


async def test_sinir_yuz_sekseninci_gun_off_by_one(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Tam cutoff'ta (< cutoff False) korunur; cutoff'tan 1sn önce silinir."""
    async with db_session_factory() as session:
        exact_id = await _make_business(session, place_id="exact", discovered_at=CUTOFF)
        before_id = await _make_business(
            session, place_id="before", discovered_at=CUTOFF - timedelta(seconds=1)
        )
        await session.commit()

    await purge_old_candidates(
        db_session_factory, reference_now=REFERENCE_NOW, retention_days=RETENTION_DAYS
    )
    async with db_session_factory() as session:
        remaining = set((await session.execute(select(Business.id))).scalars().all())
    assert exact_id in remaining  # tam sınır korunur (< kesin küçük)
    assert before_id not in remaining  # sınırdan eski silinir


async def test_won_filtresi_karsi_kanit(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """KARŞI-KANIT: won işletme tarih olarak silme adayı ama won filtresi onu koruyor.

    Tarih-tabanlı aday kümesi (won filtresiz) won'u İÇERİR; gerçek fonksiyon (won filtreli)
    onu DIŞLAR. Filtre kalksa dönüşen müşteri silinirdi → hukuki ihlal.
    """
    async with db_session_factory() as session:
        won_id = await _make_business(
            session,
            place_id="wononly",
            discovered_at=REFERENCE_NOW - timedelta(days=300),
            won=True,
        )
        await session.commit()

        # won filtreli gerçek sorgu: won'u dışlar.
        deletable = await _deletable_business_ids(session, CUTOFF)
        assert won_id not in deletable, "won filtreli sorgu dönüşen müşteriyi dışlamalı"

        # Tarih koşulu tek başına (won filtresiz): won yeterince eski → aday olurdu.
        date_only = set(
            (await session.execute(select(Business.id).where(Business.discovered_at < CUTOFF)))
            .scalars()
            .all()
        )
        assert won_id in date_only, "won tarih olarak silme adayı (filtre olmasa silinirdi)"

    await purge_old_candidates(
        db_session_factory, reference_now=REFERENCE_NOW, retention_days=RETENTION_DAYS
    )
    async with db_session_factory() as session:
        still = await session.scalar(select(Business.id).where(Business.id == won_id))
    assert still == won_id  # won korundu
