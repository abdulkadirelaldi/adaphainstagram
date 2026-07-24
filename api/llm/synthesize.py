"""Sonnet 5 sentez — rapor metni + erişim taslağı + bulgu mesajları (SPEC §6).

Girdi: deterministik bulgular (BE-14) + metrikler + Haiku sınıflandırması (BE-15) +
kohort istatistikleri. Çıktı: rapor metni, outreach taslağı, var olan bulgulara
bağlı ajans-dili mesajlar.

**LLM bulgu icat etmez** (SPEC §5): çıktıdaki mesajlar yalnızca girdideki `rule`
kimliklerine bağlanır; bilinmeyen kural **düşürülür** (yeni bulgu oluşturulamaz —
bulgu listesi BE-14'ten sabit gelir, Sonnet yalnız yazıya döker). Sistem promptu
`cache_control` ile sabitlenir (prompt caching); oynak girdi breakpoint'ten sonra.
"""

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from api.core.findings import Finding
from api.llm.classify import PostClassification
from api.llm.client import LLMClient
from api.llm.cost import SONNET_MODEL, compute_cost
from api.llm.prompts import load_prompt

_SYSTEM_PROMPT = load_prompt("synthesize_system_v1.md")
_MAX_TOKENS = 4096


class _FindingMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: str
    message: str


class _SynthesisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_text: str
    outreach_draft: str
    finding_messages: list[_FindingMessage]


@dataclass
class SynthesisResult:
    report_text: str
    outreach_draft: str
    # rule → ajans-dili mesaj; yalnızca bilinen kurallar (icat düşürülür).
    finding_messages: dict[str, str] = field(default_factory=dict)
    cost_usd: Decimal = Decimal(0)


def _classification_summary(classifications: list[PostClassification]) -> dict[str, Any]:
    """Haiku çıktısını sayısal özete indirger (tek tek gönderi yerine dağılım)."""
    pillars: dict[str, int] = {}
    tones: dict[str, int] = {}
    cta_count = 0
    for c in classifications:
        pillars[c.content_pillar] = pillars.get(c.content_pillar, 0) + 1
        tones[c.tone] = tones.get(c.tone, 0) + 1
        cta_count += int(c.has_cta)
    return {
        "post_count": len(classifications),
        "content_pillars": pillars,
        "tones": tones,
        "cta_posts": cta_count,
    }


def _user_message(
    findings: list[Finding],
    classifications: list[PostClassification],
    metrics: dict[str, Any],
    cohort: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "findings": [
            {"rule": f.rule, "title": f.title, "severity": f.severity.value, "detail": f.detail}
            for f in findings
        ],
        "metrics": metrics,
        "classification_summary": _classification_summary(classifications),
        "cohort": cohort,
    }
    return {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}


async def synthesize_audit(
    client: LLMClient,
    *,
    findings: list[Finding],
    classifications: list[PostClassification],
    metrics: dict[str, Any],
    cohort: dict[str, Any],
    as_of: date,
) -> SynthesisResult:
    """Tek Sonnet çağrısıyla rapor + taslak + bulgu mesajları üretir."""
    system_blocks = [
        {"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
    ]
    response = await client.complete(
        model=SONNET_MODEL,
        system_blocks=system_blocks,
        messages=[_user_message(findings, classifications, metrics, cohort)],
        max_tokens=_MAX_TOKENS,
    )
    parsed = _SynthesisOutput.model_validate_json(response.text)

    # İcat düşürme: yalnız var olan bulgu kurallarına mesaj bağla. Bilinmeyen rule
    # yeni bulgu OLUŞTURMAZ — listesi BE-14'ten sabit (kural: LLM icat etmez).
    known_rules = {f.rule for f in findings}
    messages = {
        item.rule: item.message for item in parsed.finding_messages if item.rule in known_rules
    }

    return SynthesisResult(
        report_text=parsed.report_text,
        outreach_draft=parsed.outreach_draft,
        finding_messages=messages,
        cost_usd=compute_cost(SONNET_MODEL, response.usage, as_of).cost_usd,
    )
