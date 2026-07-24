"""Haiku 4.5 toplu gönderi sınıflandırma (SPEC §6).

Tek `complete` çağrısında ≤30 gönderi — gönderi başına ayrı çağrı YASAK (CLAUDE.md
maliyet disiplini). 30'dan fazla gönderi 30'luk gruplara bölünür, her grup bir çağrı.
Çıktı katı JSON, Pydantic ile doğrulanır; bozuk yanıtta bir kez retry.

Sistem promptu `cache_control` ile sabitlenir (prompt caching, SPEC §6). Not: Haiku
minimum cacheable prefix ~4096 token; sistem promptu bunun altındaysa cache tetiklenmez
(`cache_read_input_tokens=0`) — bu bir hata değil, küçük prompt'ta beklenen davranış.
"""

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, ValidationError

from api.core.signals import PostData
from api.llm.client import LLMClient
from api.llm.cost import HAIKU_MODEL, compute_cost
from api.llm.prompts import load_prompt

_SYSTEM_PROMPT = load_prompt("classify_system_v1.md")
_BATCH_SIZE = 30
_MAX_TOKENS = 4096


class PostClassification(BaseModel):
    """Haiku'nun tek gönderi için ürettiği sınıflandırma (katı JSON alanları)."""

    model_config = ConfigDict(extra="forbid")

    ig_id: str
    content_pillar: str
    tone: str
    visual_quality: str
    has_cta: bool


class _ClassificationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classifications: list[PostClassification]


@dataclass
class ClassifyResult:
    classifications: list[PostClassification] = field(default_factory=list)
    cost_usd: Decimal = Decimal(0)
    calls: int = 0  # kaç LLM çağrısı yapıldı (batch kanıtı)


def _batches(posts: list[PostData], size: int) -> list[list[PostData]]:
    return [posts[i : i + size] for i in range(0, len(posts), size)]


def _system_blocks() -> list[dict[str, object]]:
    # cache_control: sabit sistem promptu prefix'i cache'lenir (SPEC §6).
    return [{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]


def _user_message(batch: list[PostData]) -> dict[str, object]:
    items = [
        {"ig_id": p.ig_id, "media_type": p.media_type, "caption": p.caption or ""} for p in batch
    ]
    return {"role": "user", "content": json.dumps({"posts": items}, ensure_ascii=False)}


def _parse(text: str) -> list[PostClassification]:
    return _ClassificationBatch.model_validate_json(text).classifications


async def classify_posts(
    client: LLMClient, posts: list[PostData], *, as_of: date
) -> ClassifyResult:
    """Gönderileri ≤30'luk gruplarla sınıflandırır; toplam maliyeti ve çağrı sayısını döndürür."""
    result = ClassifyResult()
    for batch in _batches(posts, _BATCH_SIZE):
        response = await client.complete(
            model=HAIKU_MODEL,
            system_blocks=_system_blocks(),
            messages=[_user_message(batch)],
            max_tokens=_MAX_TOKENS,
        )
        result.calls += 1
        result.cost_usd += compute_cost(HAIKU_MODEL, response.usage, as_of).cost_usd
        try:
            result.classifications.extend(_parse(response.text))
        except ValidationError:
            # Katı JSON şart; bir kez daha dene, yine bozuksa yükselt.
            retry = await client.complete(
                model=HAIKU_MODEL,
                system_blocks=_system_blocks(),
                messages=[_user_message(batch)],
                max_tokens=_MAX_TOKENS,
            )
            result.calls += 1
            result.cost_usd += compute_cost(HAIKU_MODEL, retry.usage, as_of).cost_usd
            result.classifications.extend(_parse(retry.text))
    return result
