"""SEC-12 blok 3 — maliyet alarmı (api/services/dashboard.compute_stats, maliyet disiplini).

Eşik altı → alarm `false`; eşik aşımı → alarm `true`; eşik yok → alarm `false`. Sınır
(maliyet == eşik) tetiklemez (kesin büyük). Gerçek yerel pg (kural 6); erişilemezse SKIP.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.models import Audit, Business
from api.services.dashboard import compute_stats


async def _seed_cost(session_factory: async_sessionmaker[AsyncSession], costs: list[str]) -> None:
    """Verilen maliyetlerle audit kayıtları yazar (aylık toplam = sum(costs))."""
    async with session_factory() as session:
        biz = Business(place_id="costbiz", name="Maliyet İşletmesi")
        session.add(biz)
        await session.flush()
        for c in costs:
            session.add(
                Audit(
                    business_id=biz.id, visibility_score=50.0, findings=[], llm_cost_usd=Decimal(c)
                )
            )
        await session.commit()


async def test_esik_altinda_alarm_yok(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_cost(db_session_factory, ["0.01", "0.02"])  # toplam 0.03
    async with db_session_factory() as session:
        stats = await compute_stats(session, monthly_cost_limit=0.05)
    assert stats.monthly_cost_usd == 0.03
    assert stats.monthly_cost_alarm is False
    assert stats.monthly_cost_limit_usd == 0.05


async def test_esik_asiminda_alarm_var(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_cost(db_session_factory, ["0.01", "0.02"])  # toplam 0.03
    async with db_session_factory() as session:
        stats = await compute_stats(session, monthly_cost_limit=0.02)
    assert stats.monthly_cost_usd == 0.03
    assert stats.monthly_cost_alarm is True


async def test_esik_yoksa_alarm_yok(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Eşik tanımlı değilse alarm kapalı (bildirim isteğe bağlı)."""
    await _seed_cost(db_session_factory, ["1.00"])
    async with db_session_factory() as session:
        stats = await compute_stats(session, monthly_cost_limit=None)
    assert stats.monthly_cost_alarm is False
    assert stats.monthly_cost_limit_usd is None


async def test_esik_tam_esitse_tetiklemez_sinir(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """maliyet == eşik → alarm yok (kesin büyük; off-by-one)."""
    await _seed_cost(db_session_factory, ["0.03"])  # toplam 0.03
    async with db_session_factory() as session:
        stats = await compute_stats(session, monthly_cost_limit=0.03)
    assert stats.monthly_cost_usd == 0.03
    assert stats.monthly_cost_alarm is False


async def test_denetim_yoksa_maliyet_sifir(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Hiç audit yok → aylık maliyet 0, uydurma değil (maliyet disiplini: gerçek toplam)."""
    async with db_session_factory() as session:
        stats = await compute_stats(session, monthly_cost_limit=0.01)
    assert stats.monthly_cost_usd == 0.0
    assert stats.monthly_cost_alarm is False
