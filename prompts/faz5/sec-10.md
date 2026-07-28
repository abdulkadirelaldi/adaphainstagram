# [GÜVENLİK & TEST] Faz 5 · SEC-10 — PDF + outreach + hukuki denetim

**BEKLET: BE-18 ve BE-19 bitene kadar gönderme.** İkisi de `docs/TASKS.md` `## Biten`'de olmalı.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (özellikle hukuki
sınırlar + kural 6). Sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig'lerine
yazarsın. `api/**`'ye dokunmazsın — bulgu `## Bloke`'ya.

## GÖREV SEC-10 — Faz 5'i bağımsız doğrula

**Oku:** `docs/SPEC.md` §7/§3, `docs/TASKS.md` `## Biten` → BE-18/BE-19, `## Bloke` → varsa
BE-18-B1 (Playwright). `api/` içindeki PDF üretimi, `GET /audits/{id}/pdf`, `PATCH /outreach/{id}`
kodunu **oku**.

**Dokunabileceğin dosyalar:** `tests/**`, `.github/**`, `docs/REVIEW.md`

**Yapılacaklar (her biri kalıcı test):**

### 1. PDF üretimi + indirme
- `GET /audits/{id}/pdf`: üretilmiş audit → geçerli PDF (magic bytes `%PDF-`), `content-type:
  application/pdf`; `pdf_path` boş → 409; olmayan audit → 404.
- PDF içeriği rapor bulgusu/metni taşıyor (Playwright kuruluysa üretilen PDF'ten metin çıkar;
  değilse ne doğrulanabildiğini `docs/REVIEW.md`'ye yaz — sahte yeşil yok).
- **Playwright durumu:** headless Chromium testte var mı? Yoksa PDF-üretim testi SKIP + REVIEW'de
  nedeni; CI'da kurulup kurulmayacağı kararı `## Bloke`'ya (orkestra şefine).

### 2. Outreach durum geçişi
- `PATCH /outreach/{id}`: geçerli geçiş durumu güncelliyor + zaman damgası (`sent`→`sent_at`);
  geçersiz enum → 422; olmayan kayıt → 404. BE-19'un geçiş grafiği kararını (varsa) test et.

### 3. Hukuki sınır denetimi — `docs/REVIEW.md` (kritik)
- **Otomatik mesaj GÖNDERİLMİYOR:** tüm `api/` içinde mesaj gönderen bir kod yolu **yok** —
  SMTP, e-posta, Instagram DM POST, webhook-gönderim, kuyruk-mesaj-tetikleme. `PATCH /outreach`
  yalnız DB satırını güncelliyor, hiçbir dış gönderim tetiklemiyor. `git grep` + kod okumayla
  kanıtla; PASS/kanıt satırı yaz. **Bu Faz 5'in en önemli denetimi** (CLAUDE.md hukuki sınır).
- `outreach` kaydı hâlâ `draft` doğuyor (BE-16); PATCH insan kararını kaydeder, göndermez.
- Yasak metrik (kural 7): PDF içeriği/şablonu ve outreach kaydında erişim/gösterim/demografi yok.
- Yeni anahtarlar (`.env.example`, PDF dizini vb.) değersiz; sır sızıntısı yok.

### 4. Kural 6
- Yeni testler canlı çağrı yapmıyor; ağ kapalıyken yeşil (PDF render yerel, dış veri çağrısı
  değil — ama Playwright chromium indirme gerektiriyorsa bunu REVIEW'de ayır).

**Kabul kriterleri:**
- Testler `tests/`'te; `pytest` yeşil, ağ kapalıyken de (Playwright SKIP'leri hariç, nedeni
  belgeli). Geçiş/422/404/409 testleri ölçülü.
- `docs/REVIEW.md`: **otomatik-mesaj-yok** (en önemli), yasak-metrik, sır, Playwright durumu —
  hepsi PASS/kanıt.
- Yeni bulgu → `## Bloke`'ya sahibiyle.

**Kapanış:** `docs/TASKS.md`'de SEC-10'u `## Biten`'e taşı. `git add tests/ .github/
docs/REVIEW.md docs/TASKS.md`, `sec:` commit. Sonra "SEC-10 bitti, Faz 5 bağımsız doğrulandı" de.
