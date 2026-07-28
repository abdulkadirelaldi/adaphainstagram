"""SEC-10 — otomatik mesaj GÖNDERME yolu yok (CLAUDE.md hukuki sınır). En kritik denetim.

Sistem hiçbir koşulda otomatik mesaj göndermez: `outreach` kaydı `draft` doğar, `PATCH
/outreach/{id}` yalnız insan kararını **kaydeder**. Bu kural burada yorum değil, çalışan
bir muhafız: `api/` **kodunda** mesaj gönderen bir mekanizma belirirse test kırmızıya döner.

Tarama **AST tabanlı** — yalnız gerçek kod (import, çağrı, URL string literali) incelenir;
docstring/yorumdaki "sistem mesaj göndermez" gibi *yasaklama* metni yanlış-pozitif üretmez.
Ağ muhafızı (kural 6) ve `.gitignore` regresyonu (SEC-2) ile aynı felsefe: hukuki sınırı
iddia etmiyoruz, ölçüyoruz.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "api"

# Mesaj gönderen kütüphaneler (import edilirse gönderim kapısı). Anthropic'in `messages`
# API'si bilinçle YOK — o LLM çağrısı, mesaj gönderimi değil.
SEND_IMPORTS = frozenset(
    {"smtplib", "aiosmtplib", "twilio", "sendgrid", "mailgun", "mailchimp", "postmark", "requests"}
)
# Mesaj gönderen metot/fonksiyon adları (çağrı/attribute olarak).
SEND_CALLS = frozenset({"sendmail", "send_email", "send_message", "send_dm", "sendmessage"})
# Kod içi string literalinde mesajlaşma ucu URL'si (hangi HTTP istemcisi olursa olsun).
SEND_URL_RE = re.compile(
    r"(graph\.facebook\.com/[^\"']*/messages|/me/messages|api\.telegram\.org|"
    r"hooks\.slack\.com|discord\.com/api/webhooks)",
    re.IGNORECASE,
)


def scan_source(src: str, filename: str = "<test>") -> list[str]:
    """Bir Python kaynağını AST ile tarar; gönderim mekanizması bulgularını döndürür."""
    hits: list[str] = []
    tree = ast.parse(src, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in SEND_IMPORTS:
                    hits.append(f"import {alias.name} (satır {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in SEND_IMPORTS:
                hits.append(f"from {node.module} import ... (satır {node.lineno})")
        elif isinstance(node, ast.Attribute):
            if node.attr in SEND_CALLS:
                hits.append(f".{node.attr}(...) (satır {node.lineno})")
            # requests.post — proje httpx kullanır; requests.post kaçak gönderim işareti.
            if (
                node.attr == "post"
                and isinstance(node.value, ast.Name)
                and node.value.id == "requests"
            ):
                hits.append(f"requests.post(...) (satır {node.lineno})")
        elif isinstance(node, ast.Name) and node.id in SEND_IMPORTS:
            hits.append(f"{node.id} kullanımı (satır {node.lineno})")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and SEND_URL_RE.search(node.value)
        ):
            hits.append(f"mesajlaşma URL'si string'i (satır {node.lineno})")
    return hits


def _api_sources() -> list[Path]:
    return [p for p in API_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def test_api_kodunda_mesaj_gonderme_mekanizmasi_yok() -> None:
    """api/ altındaki hiçbir .py dosyası mesaj gönderen bir kod mekanizması içermemeli."""
    all_hits: list[str] = []
    for path in _api_sources():
        rel = path.relative_to(API_DIR.parent)
        for hit in scan_source(path.read_text(encoding="utf-8"), str(rel)):
            all_hits.append(f"{rel}: {hit}")
    assert not all_hits, (
        "api/ içinde otomatik mesaj gönderme yolu bulundu (CLAUDE.md hukuki sınır ihlali):\n"
        + "\n".join(all_hits)
    )


def test_muhafiz_gercekten_olcuyor_karsi_kanit() -> None:
    """KARŞI-KANIT: tarayıcı bilinen gönderim kodunu yakalıyor, benign kodu yakalamıyor.

    Muhafız yanlışlıkla hiçbir şeyi eşleştirmeseydi test #1 anlamsız yeşil olurdu.
    """
    # Gerçek gönderim örnekleri — yakalanmalı.
    assert scan_source("import smtplib")
    assert scan_source("import aiosmtplib")
    assert scan_source("await client.send_message(to=handle)")
    assert scan_source("import requests\nrequests.post(url, json=body)")
    assert scan_source('httpx.post("https://graph.facebook.com/v21.0/me/messages", json=x)')

    # Benign kod — YAKALANMAMALI (yanlış pozitif yok).
    assert not scan_source('channel = "instagram_dm"')
    assert not scan_source("await self._client.messages.create(model=model)")  # Anthropic LLM
    assert not scan_source(
        'base = "https://graph.facebook.com/v21.0"'
    )  # BD veri çekme, /messages değil
    assert not scan_source(
        '"""sistem hiçbir koşulda otomatik mesaj göndermez (SMTP/DM/webhook)."""'
    )
