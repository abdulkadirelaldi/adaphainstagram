"""LLM maliyet hesabı — Decimal, float değil (para yuvarlaması yasak).

Oranlar tablosu kaynak + tarih yorumlu (SPEC §6, maliyet disiplini). Sonnet 5 tanıtım
fiyatı 2026-08-31'e kadar; oran pencereye göre seçilir ve hangi tier'ın kullanıldığı
`CostBreakdown.rate_tier` ile izlenebilir kalır.

Model id'leri sabit (CLAUDE.md): sınıflandırma `claude-haiku-4-5`, sentez `claude-sonnet-5`.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from api.llm.client import LLMUsage

HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-5"

# Sonnet 5 tanıtım penceresi son günü (dahil) — bu tarihe kadar $2/$10, sonrası $3/$15.
_SONNET_INTRO_LAST_DAY = date(2026, 8, 31)

# Milyon token başına USD oranları (girdi, çıktı). Kaynak: model kartı, 2026-06.
_HAIKU_RATE = (Decimal("1.00"), Decimal("5.00"))
_SONNET_STANDARD = (Decimal("3.00"), Decimal("15.00"))
_SONNET_INTRO = (Decimal("2.00"), Decimal("10.00"))

# Prompt caching çarpanları (SPEC §6 / maliyet formülü).
_CACHE_WRITE_MULT = Decimal("1.25")
_CACHE_READ_MULT = Decimal("0.10")
_PER_MILLION = Decimal("1000000")


@dataclass(frozen=True)
class CostBreakdown:
    model: str
    rate_tier: str  # "haiku" | "sonnet-intro" | "sonnet-standard" — izlenebilirlik
    cost_usd: Decimal


def _rates(model: str, as_of: date) -> tuple[Decimal, Decimal, str]:
    if model == HAIKU_MODEL:
        return (*_HAIKU_RATE, "haiku")
    if model == SONNET_MODEL:
        if as_of <= _SONNET_INTRO_LAST_DAY:
            return (*_SONNET_INTRO, "sonnet-intro")
        return (*_SONNET_STANDARD, "sonnet-standard")
    raise ValueError(f"Bilinmeyen model, oran yok: {model!r}")


def compute_cost(model: str, usage: LLMUsage, as_of: date) -> CostBreakdown:
    """Bir çağrının gerçek maliyetini `usage`'dan hesaplar (SPEC §6 formülü)."""
    in_rate, out_rate, tier = _rates(model, as_of)
    raw = (
        Decimal(usage.input_tokens) * in_rate
        + Decimal(usage.cache_creation_input_tokens) * in_rate * _CACHE_WRITE_MULT
        + Decimal(usage.cache_read_input_tokens) * in_rate * _CACHE_READ_MULT
        + Decimal(usage.output_tokens) * out_rate
    )
    return CostBreakdown(model=model, rate_tier=tier, cost_usd=raw / _PER_MILLION)
