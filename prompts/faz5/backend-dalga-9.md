# [BACKEND] Faz 5 · Dalga 9 — BE-18 (PDF) + BE-19 (PATCH outreach)

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku (özellikle hukuki sınırlar:
sistem otomatik mesaj göndermez). Sadece `api/**`, `pyproject.toml`, `.env.example` altına
yazarsın. `docs/openapi.yaml` BE-17'de dondu — yeni uç yoksa dokunma (kural 3). İki görev,
sırayla, ayrı commit'ler.

---

## GÖREV BE-18 — Playwright PDF üretimi + indirme

**Amaç:** Denetim raporunu HTML'den PDF'e render etmek, `audits.pdf_path`'e yazmak,
`GET /audits/{id}/pdf` ile stream etmek.

**Oku:** `docs/openapi.yaml` (BE-17: `GET /audits/{id}/pdf` → `application/pdf`, PDF-yok → 409),
`docs/SPEC.md` §3 (`audits.pdf_path`), §5 (rapor bulguları). BE-16 (`report_text` + bulgu
mesajları — PDF içeriği bunlardan). `CLAUDE.md` teknoloji (Playwright PDF).

**Dokunabileceğin dosyalar:** `api/**`, `pyproject.toml`, `.env.example`

**Yapılacaklar:**
- Rapor **HTML şablonu**: görünürlük skoru + bulgular (önem sıralı, deterministik tetik + LLM
  ajans-dili metni) + `report_text`. Şablon `api/` içinde versiyonlu bir dosya; koda gömülü
  dev HTML string değil.
- **Playwright** (headless Chromium) ile HTML→PDF. Üretilen PDF bir dizine yazılır, yol
  `audits.pdf_path`'e kaydedilir. Dizin ayarlanabilir (`.env`), `.env.example`'a değersiz ekle.
- PDF üretimi audit akışının fazı: Sonnet sentezi (BE-16) sonrası PDF üretilir, `pdf_path` dolar.
  Fixture modunda (BE-10) da çalışır — PDF render dış veri çağrısı **değil**, yerel; kural 6
  ihlali yok.
- `GET /audits/{id}/pdf`: `pdf_path`'ten PDF'i `application/pdf` olarak stream eder. `pdf_path`
  boşsa (üretilmemiş) **409** (BE-17 sözleşmesi); denetim yoksa 404.
- **Yasak alan yok** (kural 7): PDF içeriği erişim/gösterim/demografi göstermez.

**ÖNEMLİ — Playwright kısıtı (Docker/CI ile aynı desen):** headless Chromium bu makinede kurulu
olmayabilir (`playwright install chromium` gerekebilir). Kurulu değilse ve kuramıyorsan:
`docs/TASKS.md` `## Bloke`'ya **BE-18-B1** olarak yaz (ne kurulu, ne değil, hangi doğrulama
yapılamadı), kararı orkestra şefine bırak. Kodu yine tamamla; PDF üretimini mümkün olan yere
kadar doğrula ve neyi doğrulayamadığını kapanış notuna yaz — sahte "yeşil" raporlama yok.

**Kabul kriterleri:**
- Bir denetim akışı sonrası `audits.pdf_path` doluyor; `GET /audits/{id}/pdf` geçerli bir PDF
  stream ediyor (magic bytes `%PDF-`), `content-type: application/pdf`.
- `pdf_path` boş audit'te `GET /audits/{id}/pdf` → 409; olmayan audit → 404.
- PDF içeriği bulguları ve rapor metnini taşıyor (en az bir bulgu başlığı PDF'te — Playwright
  varsa üretilen PDF'ten metin çıkarımıyla doğrula; yoksa Bloke + kapanış notu).
- `ruff` + `mypy api/` + `pytest` yeşil; yasak-metrik + anahtar-sızıntı grep boş.

**Kapanış:** `docs/TASKS.md`'de BE-18'i `## Biten`'e taşı (Playwright doğrulandı mı, neyi
doğrulayamadın). Faz 5 kutusu #1'i işaretle (Playwright bloke'liyse koşullu). `git add api/
pyproject.toml .env.example docs/TASKS.md`, `be:` commit. Sonra BE-19'a geç.

---

## GÖREV BE-19 — `PATCH /outreach/{id}` durum güncelleme

**Amaç:** Erişim kaydının durumunu güncellemek — **yalnız kaydeder, mesaj göndermez**.

**Oku:** `docs/openapi.yaml` (BE-17: `PATCH /outreach/{id}`, `status` enum, gönderme alanı yok),
`docs/SPEC.md` §3 (durum kümesi `draft|sent|opened|replied|meeting|won|lost`). `CLAUDE.md`
hukuki sınırlar (**sistem hiçbir koşulda otomatik mesaj göndermez** — bu uç insan kararını
*kaydeder*).

**Dokunabileceğin dosyalar:** `api/**`

**Yapılacaklar:**
- `PATCH /outreach/{id}`: `status`'ü günceller. Geçersiz enum değeri → 422 (sözleşme). Uygun
  geçişte zaman damgası set et (`sent`→`sent_at`, `replied`→`replied_at`; SPEC §3). Bir geçiş
  grafiği zorlayacaksan (ör. `draft`'tan doğrudan `won`'a atlamayı engelle) kararını **belgele**;
  insanı gereksiz kısıtlama — makul tut.
- **KESİNLİKLE mesaj göndermez.** Bu uç yalnız DB satırını günceller. Hiçbir SMTP/HTTP-DM/
  webhook/kuyruk-mesaj-gönderme yolu tetiklenmez. Bulunmayan denetim/outreach → 404.

**Kabul kriterleri:**
- `PATCH /outreach/{id}` durumu güncelliyor; `sent`→`sent_at` doluyor; geçersiz `status` → 422;
  olmayan kayıt → 404.
- **Gönderme yok — makine kanıtı:** `git grep -niE "smtp|sendmail|mail\.send|dm|webhook|
  requests\.post|httpx.*post.*(instagram|message)" -- api/` mesaj gönderen bir yol
  döndürmüyor (yalnız veri çekme/normalize/LLM bağlamı). Kapanış notuna yaz; şüphe varsa SEC-10
  bağımsız denetleyecek.
- `ruff` + `mypy api/` + `pytest` yeşil.

**Kapanış:** `docs/TASKS.md`'de BE-19'u `## Biten`'e taşı (geçiş grafiği kararını belgele).
Faz 5 kutusu #3 ve #4'ü işaretle. `git add api/ docs/TASKS.md`, `be:` commit. Sonra orkestra
şefine "BE-18+BE-19 bitti; SEC-10 ve FE-7 canlı doğrulama yapabilir" de.
