"""SEC-10 blok 1 — denetim raporu PDF üretimi (api/pdf/render.py, SPEC §7).

`build_report_html` saf/deterministik → içerik + kaçış + sıralama + yasak-metrik yokluğu
DB'siz test edilir. `render_pdf`/`generate_audit_pdf` headless Chromium ister; kuruluysa
gerçek PDF üretilip magic bytes + metin doğrulanır (pdftotext varsa), yoksa SKIP + neden.

PDF render **yereldir** (dış veri çağrısı değil, kural 6). Chromium indirme gerektirdiğinden
CI'da `playwright install chromium` yoksa bu testler atlanır — sahte yeşil yok.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess

import pytest
import pytest_asyncio

from api.core.findings import Finding
from api.models.enums import Severity
from api.pdf import build_report_html, generate_audit_pdf, render_pdf

FORBIDDEN_TOKENS = (
    "impressions",
    "reach",
    "saves",
    "profile_visit",
    "demographic",
    "follower_age",
    "gender",
)

_FINDINGS = [
    Finding(rule="cta_yok", title="CTA'sız caption", severity=Severity.MEDIUM, detail="CTA %10."),
    Finding(
        rule="reels_yok",
        title="Reels yok",
        severity=Severity.CRITICAL,
        detail="Reels %0.",
        message="Reels üretimine başlayın.",
    ),
]


# --- Saf HTML üretimi (Playwright gerektirmez) ----------------------------------


def test_html_icerik_ve_siralama() -> None:
    html = build_report_html(
        business_name="Elmas Kuyumculuk",
        visibility_score=41.0,
        findings=_FINDINGS,
        report_text="Ajans dilinde rapor metni.",
    )
    assert "Elmas Kuyumculuk" in html
    assert "41" in html  # görünürlük skoru
    assert "Ajans dilinde rapor metni." in html
    # "Reels yok" özel karakter içermez; "caption" ("CTA'sız caption"ın apostrofsuz parçası)
    # html.escape'ten sağ çıkar (apostrof &#x27; olur — kaçış doğru davranış).
    assert "Reels yok" in html and "caption" in html
    assert "Reels üretimine başlayın." in html  # LLM mesajı
    # Önem sırası: kritik (Reels) orta'dan (caption) önce gelmeli.
    assert html.index("Reels yok") < html.index("caption")


def test_html_kacis_uyguluyor() -> None:
    """Kullanıcı verisi HTML'e enjekte edilmeden önce kaçırılmalı (XSS/şablon kırılması)."""
    html = build_report_html(
        business_name="<script>alert(1)</script>",
        visibility_score=50.0,
        findings=[],
        report_text="<b>x</b>",
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_html_bulgu_yoksa_mesaj() -> None:
    html = build_report_html(
        business_name="X", visibility_score=100.0, findings=[], report_text=None
    )
    assert "Tetiklenen bulgu yok." in html


def test_html_yasak_metrik_icermiyor() -> None:
    """Rapor HTML'i yalnız skor + bulgu + rapor metni; erişim/gösterim/demografi yok (kural 7)."""
    html = build_report_html(
        business_name="Kafe", visibility_score=60.0, findings=_FINDINGS, report_text="rapor"
    ).lower()
    for tok in FORBIDDEN_TOKENS:
        assert tok not in html.replace("outreach", ""), f"raporda yasak metrik: {tok}"


# --- Gerçek PDF render (Playwright / headless Chromium) --------------------------


@pytest_asyncio.fixture
async def chromium_ready() -> None:
    """Headless Chromium kullanılabilir mi; değilse testi atla (sahte yeşil yok)."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await browser.close()
    except Exception as exc:
        pytest.skip(f"Headless Chromium yok (playwright install chromium gerekli): {exc!r}")


async def test_render_pdf_gecerli_pdf_uretiyor(chromium_ready: None) -> None:
    """render_pdf geçerli PDF baytları döndürüyor (magic bytes %PDF-)."""
    html = build_report_html(
        business_name="Elmas Kuyumculuk",
        visibility_score=41.0,
        findings=_FINDINGS,
        report_text="rapor",
    )
    pdf = await render_pdf(html)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000  # önemsiz olmayan bir belge


async def test_generate_audit_pdf_dosyaya_yaziyor_ve_icerik_tasiyor(
    chromium_ready: None, tmp_path: object
) -> None:
    """generate_audit_pdf dosya yazıyor; PDF metni bulgu başlığını taşıyor (pdftotext varsa)."""
    from pathlib import Path

    out_dir = str(tmp_path)
    path = await generate_audit_pdf(
        audit_id=7,
        output_dir=out_dir,
        business_name="Elmas Kuyumculuk",
        visibility_score=41.0,
        findings=_FINDINGS,
        report_text="Ajans raporu.",
    )
    pdf_file = Path(path)
    assert pdf_file.is_file()
    assert pdf_file.read_bytes().startswith(b"%PDF-")

    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        pytest.skip(
            "pdftotext yok — PDF metin içeriği çıkarılamadı (HTML testi içeriği kanıtlıyor)"
        )

    # subprocess bloklar; async testte thread'e al (ASYNC221).
    def _extract() -> str:
        return subprocess.run(  # noqa: S603 — pdftotext which'ten, argümanlar sabit
            [pdftotext, str(pdf_file), "-"], capture_output=True, text=True, check=True
        ).stdout

    text = await asyncio.to_thread(_extract)
    assert "Reels yok" in text  # kritik bulgu PDF metninde
    assert "Elmas Kuyumculuk" in text
