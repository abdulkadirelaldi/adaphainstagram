"""LLM istemci soyutlaması — enjekte edilebilir (test canlı çağrı yapmaz, kural 6).

Kendi dar protokolümüz Anthropic SDK'sının şeklinden bağımsız: `complete()` sistem
blokları + mesajlar alır, metin + token kullanımı döndürür. Gerçek uygulama
`AsyncAnthropic`'i sarar; test sahte bir istemci verir ve fixture yanıtı döndürür.
"""

from dataclasses import dataclass
from typing import Any, Protocol, cast


@dataclass(frozen=True)
class LLMUsage:
    """Bir çağrının token kullanımı — maliyet buradan hesaplanır (SPEC §6, maliyet disiplini)."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass(frozen=True)
class LLMResponse:
    text: str
    usage: LLMUsage


class LLMClient(Protocol):
    """Sınıflandırma ve sentezin ihtiyaç duyduğu tek metot."""

    async def complete(
        self,
        *,
        model: str,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse: ...


class AnthropicLLMClient:
    """Gerçek istemci — `AsyncAnthropic`'i sarar. Yalnızca üretim yolunda kullanılır.

    Anahtar `.env`'den enjekte edilir (kural 4). Sistem blokları `cache_control`
    taşıyabilir (prompt caching, SPEC §6); mesajlar breakpoint'ten sonra gelir.
    """

    def __init__(self, api_key: str) -> None:
        # Lazy import: anthropic yalnızca üretim yolunda gerekli; test sahte istemci verir.
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        *,
        model: str,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        # SDK sınırı: TypedDict'ler yerine düz dict geçiyoruz (runtime kabul ediyor);
        # cast tek noktada tip köprüsünü kurar.
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=cast(Any, system_blocks),
            messages=cast(Any, messages),
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        usage = response.usage
        return LLMResponse(
            text=text,
            usage=LLMUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
                cache_read_input_tokens=usage.cache_read_input_tokens or 0,
            ),
        )
