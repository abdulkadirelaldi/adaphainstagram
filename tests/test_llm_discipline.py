"""SEC-9 blok 2 — LLM mock disiplini (kural 6 + SPEC §5/§6).

Canlı Anthropic çağrısı YOK: `FixtureLLMClient` / sarmalayıcılar fixture yanıtı üretir,
ağ muhafızı (conftest) altında geçer. Haiku tek çağrıda ≤30 gönderi (batch); Sonnet
bulgu icat etmiyor (bilinmeyen kural düşürülür); şema katı; cache_control gönderiliyor.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from api.core.findings import Finding
from api.core.signals import PostData
from api.llm.classify import classify_posts
from api.llm.cost import HAIKU_MODEL, SONNET_MODEL
from api.llm.fixture_client import FixtureLLMClient
from api.llm.synthesize import synthesize_audit
from api.models.enums import Severity
from tests._mocks import CapturingLLMClient, ScriptedLLMClient

AS_OF = date(2026, 7, 15)
REF = datetime(2026, 7, 15, tzinfo=UTC)


def _posts(n: int) -> list[PostData]:
    return [
        PostData(
            posted_at=REF - timedelta(days=i),
            media_type="IMAGE",
            caption="gunluk",
            ig_id=str(i),
        )
        for i in range(n)
    ]


# --- Haiku batch: tek çağrıda ≤30 gönderi ---------------------------------------


async def test_haiku_otuz_altinda_tek_cagri() -> None:
    """N≤30 gönderi → tam 1 LLM çağrısı (gönderi başına çağrı YASAK)."""
    client = CapturingLLMClient(FixtureLLMClient())
    result = await classify_posts(client, _posts(30), as_of=AS_OF)
    assert len(client.calls) == 1
    assert result.calls == 1
    assert len(result.classifications) == 30
    # Doğru model id (CLAUDE.md).
    assert client.calls[0]["model"] == HAIKU_MODEL


async def test_haiku_otuzdan_fazla_gruplaniyor() -> None:
    """N=65 → 3 grup [30,30,5], 3 çağrı (gönderi başına değil)."""
    client = CapturingLLMClient(FixtureLLMClient())
    result = await classify_posts(client, _posts(65), as_of=AS_OF)
    assert len(client.calls) == 3
    assert len(result.classifications) == 65


async def test_haiku_bes_gonderi_yine_tek_cagri() -> None:
    client = CapturingLLMClient(FixtureLLMClient())
    await classify_posts(client, _posts(5), as_of=AS_OF)
    assert len(client.calls) == 1


# --- cache_control (prompt caching, SPEC §6) — gönderilen system bloğunda --------


async def test_haiku_cache_control_gonderiyor() -> None:
    client = CapturingLLMClient(FixtureLLMClient())
    await classify_posts(client, _posts(3), as_of=AS_OF)
    block = client.calls[0]["system_blocks"][0]
    assert block.get("cache_control") == {"type": "ephemeral"}


async def test_sonnet_cache_control_gonderiyor_ve_dogru_model() -> None:
    client = CapturingLLMClient(FixtureLLMClient())
    findings = [
        Finding(rule="reels_yok", title="Reels yok", severity=Severity.CRITICAL, detail="x")
    ]
    await synthesize_audit(
        client, findings=findings, classifications=[], metrics={}, cohort={}, as_of=AS_OF
    )
    call = client.calls[0]
    assert call["model"] == SONNET_MODEL
    assert call["system_blocks"][0].get("cache_control") == {"type": "ephemeral"}


# --- Sonnet bulgu icat etmiyor (SPEC §5) — karşı-kanıtlı ------------------------


async def test_sonnet_bilinmeyen_kural_dusuruluyor() -> None:
    """Çıktıda `findings`'te olmayan bir rule gelirse mesaj DÜŞÜRÜLÜR (icat yasak).

    KARŞI-KANIT: known_rules filtresi kaldırılsaydı uydurma kural çıktıya sızardı ve
    bu assert kırmızıya dönerdi. `synthesize` yalnız var olan kurala mesaj bağlar.
    """
    findings = [
        Finding(rule="reels_yok", title="Reels yok", severity=Severity.CRITICAL, detail="x")
    ]
    scripted = ScriptedLLMClient(
        json.dumps(
            {
                "report_text": "rapor",
                "outreach_draft": "taslak",
                "finding_messages": [
                    {"rule": "reels_yok", "message": "gerçek bulgu mesajı"},
                    {"rule": "uydurma_kural", "message": "İCAT — düşürülmeli"},
                ],
            }
        )
    )
    result = await synthesize_audit(
        scripted, findings=findings, classifications=[], metrics={}, cohort={}, as_of=AS_OF
    )
    assert set(result.finding_messages) == {"reels_yok"}
    assert "uydurma_kural" not in result.finding_messages


async def test_sonnet_bozuk_sema_reddediyor() -> None:
    """Çıktı katı şema dışıysa (fazla üst-düzey alan) ValidationError — sessiz kabul yok."""
    scripted = ScriptedLLMClient(
        json.dumps(
            {
                "report_text": "rapor",
                "outreach_draft": "taslak",
                "finding_messages": [],
                "uydurma_alan": "extra=forbid reddetmeli",
            }
        )
    )
    with pytest.raises(ValidationError):
        await synthesize_audit(
            scripted, findings=[], classifications=[], metrics={}, cohort={}, as_of=AS_OF
        )


async def test_haiku_bozuk_json_reddediyor_iki_denemeden_sonra() -> None:
    """Katı JSON: bozuk yanıt bir kez retry, yine bozuksa yükseltir (sessiz yutma yok)."""
    scripted = ScriptedLLMClient("bu JSON değil")
    with pytest.raises(ValidationError):
        await classify_posts(scripted, _posts(3), as_of=AS_OF)
    # İlk çağrı + bir retry = 2 çağrı.
    assert scripted.calls == 2


# --- Çıktıda yasak metrik yok (kural 7) -----------------------------------------


async def test_haiku_ciktisi_yalniz_izinli_dort_alan() -> None:
    """Sınıflandırma yalnız content_pillar/tone/visual_quality/has_cta taşır — yasak metrik yok."""
    result = await classify_posts(FixtureLLMClient(), _posts(3), as_of=AS_OF)
    for c in result.classifications:
        dumped = c.model_dump()
        assert set(dumped) == {"ig_id", "content_pillar", "tone", "visual_quality", "has_cta"}
