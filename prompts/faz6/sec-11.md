# [GÜVENLİK & TEST] Faz 6 · SEC-11 — e2e testler + CI'da chromium

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (kural 6). Sadece
`tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig'lerine yazarsın. `api/**`/`web/**`'e
dokunmazsın.

**Bu görev sözleşmeden (BE-21) bağımsız — mevcut akışı test eder, hemen başlayabilirsin.**

## GÖREV SEC-11 — uçtan uca test iskeleti + CI chromium

**Oku:** `docs/SPEC.md` §1 (tam akış: keşif→skor→denetim→PDF/outreach), §8 Faz 6 (e2e).
`docs/TASKS.md` `## Bloke` → **SEC-10-N1** (CI'da chromium kararı — bu görevle kapanıyor).
Mevcut `.github/workflows/ci.yml`, BE-10 (fixture modu — e2e canlı çağrısız çalışsın).

**Dokunabileceğin dosyalar:** `tests/**`, `.github/**`, `docs/REVIEW.md`

**Yapılacaklar:**
- **CI chromium (SEC-10-N1 kapat):** `.github/workflows/ci.yml` pytest job'ına
  `playwright install --with-deps chromium` adımı ekle. Böylece PDF-render testleri (BE-18/
  SEC-10) CI'da **SKIP değil koşuyor**. Chromium kurulumunun süre/indirme maliyetini kabul
  ediyoruz (orkestra şefi kararı — SEC-10-N1 buna bağlandı).
- **E2E test iskeleti** (`tests/e2e/` veya uygun): **fixture modunda** (BE-10 `RADAR_FIXTURE_MODE`)
  uçtan uca akışı sürer — canlı IG/Apify/Anthropic çağrısı **yok** (kural 6):
  1. `POST /discovery/run` → job `done` → DB'de ~100 skorlu işletme
  2. `qualified` bir işletmeye `POST /businesses/{id}/audit` → job `done` → `GET /audits/{id}`
     bulgu + rapor metni + `llm_cost_usd>0`
  3. `GET /audits/{id}/pdf` → geçerli PDF (chromium CI'da kurulu)
  4. `PATCH /outreach/{id}` → durum güncelleniyor
- **Playwright e2e (frontend)** kapsam kararı: SPEC "Playwright e2e" diyor. Backend akışı
  yukarıda API e2e ile kapsanıyor; frontend Playwright e2e (panel tıklama akışı) eklenip
  eklenmeyeceğine karar ver — `web/` çalıştırmak gerekir. Kapsamı `docs/REVIEW.md`'ye yaz;
  büyükse ayrı görev olarak `## Bloke`'ya not düş, orkestra şefine bırak.

**Kabul kriterleri:**
- `.github/workflows/ci.yml`'de `playwright install ... chromium` adımı var; PDF testleri CI'da
  koşuyor (yerel doğrulaman + yaml).
- E2E test fixture modunda uçtan uca yeşil; **ağ kapalıyken de** (kural 6 — canlı çağrı yok).
  Gerçek pg+redis gerektiriyorsa erişilemezse dürüst SKIP, nedeni belgeli.
- `pytest` yeşil; `docs/REVIEW.md`'de e2e kapsamı + frontend-Playwright kararı.

**Kapanış:** `docs/TASKS.md`'de SEC-11'i `## Biten`'e taşı; `## Bloke` SEC-10-N1 satırına
`→ SEC-11 ile çözüldü` ekle. `git add tests/ .github/ docs/REVIEW.md docs/TASKS.md`, `sec:`
commit.
