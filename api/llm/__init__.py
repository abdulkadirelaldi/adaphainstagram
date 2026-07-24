"""LLM katmanı — Haiku sınıflandırma (BE-15), Sonnet sentez (BE-16), maliyet.

İstemci enjekte edilebilir (`LLMClient` protokolü); test sahte istemci + fixture ile
çalışır, canlı Anthropic çağrısı yapmaz (kural 6). Promptlar `prompts/` altında
versiyonlu dosyalarda (SPEC §6).
"""

from api.llm.classify import ClassifyResult, PostClassification, classify_posts
from api.llm.client import AnthropicLLMClient, LLMClient, LLMResponse, LLMUsage
from api.llm.cost import HAIKU_MODEL, SONNET_MODEL, CostBreakdown, compute_cost

__all__ = [
    "HAIKU_MODEL",
    "SONNET_MODEL",
    "AnthropicLLMClient",
    "ClassifyResult",
    "CostBreakdown",
    "LLMClient",
    "LLMResponse",
    "LLMUsage",
    "PostClassification",
    "classify_posts",
    "compute_cost",
]
