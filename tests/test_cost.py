"""SEC-9 blok 3 — LLM maliyet hesabı (api/llm/cost.py, SPEC §6 + maliyet disiplini).

Maliyet `usage`'dan doğru USD üretiyor mu (cache 1.25×/0.10× dahil); Sonnet tanıtım
fiyatı penceresi doğru tier'ı seçiyor mu. Beklenen USD magic number değil, cost.py'nin
belgelediği oran tablosundan **türetilir** (aynı formül, bağımsız).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.llm.client import LLMUsage
from api.llm.cost import HAIKU_MODEL, SONNET_MODEL, compute_cost

# cost.py'nin belgelediği oranlar (milyon token başına USD) — testte bağımsız türetme.
HAIKU_IN, HAIKU_OUT = Decimal("1.00"), Decimal("5.00")
SONNET_INTRO_IN, SONNET_INTRO_OUT = Decimal("2.00"), Decimal("10.00")
SONNET_STD_IN, SONNET_STD_OUT = Decimal("3.00"), Decimal("15.00")
CACHE_WRITE, CACHE_READ = Decimal("1.25"), Decimal("0.10")
PER_M = Decimal("1000000")

INTRO_DAY = date(2026, 8, 31)  # dahil → intro
AFTER_INTRO = date(2026, 9, 1)  # standart


def _expected(usage: LLMUsage, in_rate: Decimal, out_rate: Decimal) -> Decimal:
    """SPEC §6 formülünü bağımsız uygular (cost.py'nin kopyası değil, aynı sözleşme)."""
    return (
        Decimal(usage.input_tokens) * in_rate
        + Decimal(usage.cache_creation_input_tokens) * in_rate * CACHE_WRITE
        + Decimal(usage.cache_read_input_tokens) * in_rate * CACHE_READ
        + Decimal(usage.output_tokens) * out_rate
    ) / PER_M


def test_haiku_maliyeti_cache_dahil_dogru() -> None:
    usage = LLMUsage(
        input_tokens=1000,
        output_tokens=500,
        cache_creation_input_tokens=200,
        cache_read_input_tokens=4000,
    )
    got = compute_cost(HAIKU_MODEL, usage, INTRO_DAY)
    assert got.cost_usd == _expected(usage, HAIKU_IN, HAIKU_OUT)
    assert got.rate_tier == "haiku"
    # Elle sağlama: (1000 + 200*1.25 + 4000*0.10 + 500*5)/1e6 = 4150/1e6.
    assert got.cost_usd == Decimal("4150") / PER_M


def test_cache_read_ucuz_cache_write_pahali() -> None:
    """Cache-read (0.1×) input'tan ucuz; cache-write (1.25×) input'tan pahalı — çarpanlar doğru yönde."""
    base = compute_cost(
        HAIKU_MODEL, LLMUsage(input_tokens=1000, output_tokens=0), INTRO_DAY
    ).cost_usd
    read = compute_cost(
        HAIKU_MODEL,
        LLMUsage(input_tokens=0, output_tokens=0, cache_read_input_tokens=1000),
        INTRO_DAY,
    ).cost_usd
    write = compute_cost(
        HAIKU_MODEL,
        LLMUsage(input_tokens=0, output_tokens=0, cache_creation_input_tokens=1000),
        INTRO_DAY,
    ).cost_usd
    assert read < base < write
    assert read == base * CACHE_READ
    assert write == base * CACHE_WRITE


def test_sonnet_tanitim_penceresi_tier_seciyor() -> None:
    usage = LLMUsage(input_tokens=1000, output_tokens=1000)
    intro = compute_cost(SONNET_MODEL, usage, INTRO_DAY)
    standard = compute_cost(SONNET_MODEL, usage, AFTER_INTRO)

    assert intro.rate_tier == "sonnet-intro"
    assert standard.rate_tier == "sonnet-standard"
    assert intro.cost_usd == _expected(usage, SONNET_INTRO_IN, SONNET_INTRO_OUT)
    assert standard.cost_usd == _expected(usage, SONNET_STD_IN, SONNET_STD_OUT)
    # Tanıtım penceresi standarttan ucuz olmalı.
    assert intro.cost_usd < standard.cost_usd


def test_sonnet_pencere_siniri_son_gun_dahil() -> None:
    """2026-08-31 dahil intro; 2026-09-01 standart (off-by-one)."""
    usage = LLMUsage(input_tokens=100, output_tokens=100)
    assert compute_cost(SONNET_MODEL, usage, date(2026, 8, 31)).rate_tier == "sonnet-intro"
    assert compute_cost(SONNET_MODEL, usage, date(2026, 9, 1)).rate_tier == "sonnet-standard"


def test_bilinmeyen_model_reddediliyor() -> None:
    with pytest.raises(ValueError, match="Bilinmeyen model"):
        compute_cost("gpt-uydurma", LLMUsage(input_tokens=1, output_tokens=1), INTRO_DAY)


def test_maliyet_decimal_float_degil() -> None:
    """Para Decimal olmalı (yuvarlama yasak) — float sızması regresyonu."""
    got = compute_cost(HAIKU_MODEL, LLMUsage(input_tokens=333, output_tokens=333), INTRO_DAY)
    assert isinstance(got.cost_usd, Decimal)
