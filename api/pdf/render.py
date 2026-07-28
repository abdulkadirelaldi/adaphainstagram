"""Denetim raporu HTML→PDF (Playwright, headless Chromium) — SPEC §7, Faz 5.

HTML şablonu versiyonlu dosyada (`report_template_v1.html`), koda gömülü değil.
PDF render **yereldir** (dış veri çağrısı değil); fixture modunda da çalışır, kural 6
ihlali yok. `build_report_html` saf/senkron (test edilebilir); `render_pdf` Chromium
başlatır.

Yasak metrik yok (kural 7): PDF yalnız görünürlük skoru + bulgular + rapor metnini
gösterir; erişim/gösterim/demografi geçmez.
"""

import html
from collections.abc import Sequence
from pathlib import Path

from api.core.findings import Finding
from api.models.enums import Severity

_TEMPLATE = (Path(__file__).resolve().parent / "report_template_v1.html").read_text(
    encoding="utf-8"
)

# Önem sırası (kritik önce) + CSS sınıfı için ASCII karşılık (ı/ü/ş içermeyen).
_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}
_SEVERITY_CSS: dict[Severity, str] = {
    Severity.CRITICAL: "kritik",
    Severity.HIGH: "yuksek",
    Severity.MEDIUM: "orta",
    Severity.LOW: "dusuk",
}


def _finding_html(finding: Finding) -> str:
    css = _SEVERITY_CSS[finding.severity]
    title = html.escape(finding.title)
    detail = html.escape(finding.detail)
    # message LLM'den (BE-16); yoksa yalnız deterministik detail gösterilir.
    message = html.escape(finding.message) if finding.message else ""
    message_block = f'<div class="message">{message}</div>' if message else ""
    return (
        f'<div class="finding {css}">'
        f'<span class="finding-title">{title}</span>'
        f'<span class="severity {css}">{html.escape(finding.severity.value)}</span>'
        f'<div class="detail">{detail}</div>'
        f"{message_block}"
        f"</div>"
    )


def build_report_html(
    *,
    business_name: str,
    visibility_score: float,
    findings: Sequence[Finding],
    report_text: str | None,
) -> str:
    """Denetim verisinden rapor HTML'i üretir (saf fonksiyon, Playwright gerektirmez)."""
    ordered = sorted(findings, key=lambda f: _SEVERITY_ORDER[f.severity])
    findings_html = (
        "".join(_finding_html(f) for f in ordered)
        if ordered
        else '<div class="detail">Tetiklenen bulgu yok.</div>'
    )
    return (
        _TEMPLATE.replace("{{business_name}}", html.escape(business_name))
        .replace("{{visibility_score}}", f"{visibility_score:.0f}")
        .replace("{{report_text}}", html.escape(report_text or "Rapor metni henüz üretilmedi."))
        .replace("{{findings_html}}", findings_html)
    )


async def render_pdf(report_html: str) -> bytes:
    """HTML'i A4 PDF'e render eder (headless Chromium). Playwright lazy import."""
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            await page.set_content(report_html, wait_until="load")
            return await page.pdf(format="A4", print_background=True)
        finally:
            await browser.close()


async def generate_audit_pdf(
    *,
    audit_id: int,
    output_dir: str,
    business_name: str,
    visibility_score: float,
    findings: Sequence[Finding],
    report_text: str | None,
) -> str:
    """Raporu render edip dosyaya yazar; `audits.pdf_path`'e yazılacak yolu döndürür."""
    report_html = build_report_html(
        business_name=business_name,
        visibility_score=visibility_score,
        findings=findings,
        report_text=report_text,
    )
    pdf_bytes = await render_pdf(report_html)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"audit_{audit_id}.pdf"
    path.write_bytes(pdf_bytes)
    return str(path)
