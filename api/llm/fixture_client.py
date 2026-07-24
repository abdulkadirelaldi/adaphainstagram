"""Fixture LLM istemcisi — fixture modunda (BE-10) canlı Anthropic yerine (kural 6).

Haiku çağrısını (girdide `posts`) sınıflandırmayla, Sonnet çağrısını (girdide
`findings`) sentezle karşılar. Sıfır olmayan `usage` döndürür ki maliyet > 0 çıksın
(maliyet disiplini uçtan uca test edilebilsin). Anahtar gerekmez, ağ yok.
"""

import json
from typing import Any

from api.llm.client import LLMResponse, LLMUsage

_CTA_HINT = ("dm", "ara", "sipariş", "randevu", "link", "whatsapp")


def _has_cta(caption: str) -> bool:
    lowered = caption.lower()
    return any(k in lowered for k in _CTA_HINT)


class FixtureLLMClient:
    async def complete(
        self,
        *,
        model: str,
        system_blocks: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        payload = json.loads(messages[0]["content"])
        if "posts" in payload:  # Haiku sınıflandırma
            text = self._classify(payload["posts"])
            usage = LLMUsage(input_tokens=1200, output_tokens=300)
        else:  # Sonnet sentez
            text = self._synthesize(payload["findings"])
            usage = LLMUsage(input_tokens=1800, output_tokens=500)
        return LLMResponse(text=text, usage=usage)

    def _classify(self, posts: list[dict[str, Any]]) -> str:
        classifications = [
            {
                "ig_id": p["ig_id"],
                "content_pillar": "tanitim",
                "tone": "notr",
                "visual_quality": "orta",
                "has_cta": _has_cta(p.get("caption") or ""),
            }
            for p in posts
        ]
        return json.dumps({"classifications": classifications})

    def _synthesize(self, findings: list[dict[str, Any]]) -> str:
        finding_messages = [
            {"rule": f["rule"], "message": f"[fixture] {f['title']}: ajans dilinde açıklama."}
            for f in findings
        ]
        return json.dumps(
            {
                "report_text": "[fixture] Hesabın denetim raporu: bulgular ve öneriler burada.",
                "outreach_draft": "[fixture] Merhaba! Hesabınızı inceledik, birkaç önerimiz var.",
                "finding_messages": finding_messages,
            }
        )
