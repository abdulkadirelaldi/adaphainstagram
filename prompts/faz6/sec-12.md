# [GÜVENLİK & TEST] Faz 6 · SEC-12 — sertleştirme testleri + son denetim

**BEKLET: BE-22 ve BE-23 bitene kadar gönderme.** İkisi de `## Biten`'de olmalı.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (hukuki sınırlar, kural
6/7, maliyet disiplini). Sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig'lerine
yazarsın. `api/**`'ye dokunmazsın — bulgu `## Bloke`'ya.

## GÖREV SEC-12 — Faz 6'yı bağımsız doğrula + proje-sonu gizlilik/maliyet denetimi

**Oku:** `docs/SPEC.md` §8 Faz 6, `docs/TASKS.md` `## Biten` → BE-22/BE-23. `CLAUDE.md` değişmez
kurallar (bu son denetimde hepsini tara). `api/` içindeki silme cron'u, rate limit, kohort ucu,
maliyet alarmını **oku**.

**Dokunabileceğin dosyalar:** `tests/**`, `.github/**`, `docs/REVIEW.md`

**Yapılacaklar (her biri kalıcı test):**

### 1. 180 günlük silme cron'u (hukuki — kritik)
- Fixture + enjekte referans zamanla: 180 günden eski **dönüşmemiş** aday ve bağlı tüm kayıtları
  (+ PDF dosyası) siliniyor; `won` aday **korunuyor**; 180 günden yeni aday korunuyor. Sınır
  (180. gün) off-by-one. Karşı-kanıt: `won` filtresi kalksa dönüşen müşteri silinir → test
  kırmızı olmalı.

### 2. Rate limit
- Sınır aşımında `429` + `Retry-After`; sınır altında normal. Sayaç sıfırlanınca tekrar geçiyor.

### 3. Maliyet alarmı
- Eşik altı → alarm `false`; eşik aşımı → alarm `true` + log. Eşik ayarlanabilir (test'te düşük
  eşikle tetikle).

### 4. Proje-sonu gizlilik + hukuki + maliyet denetimi — `docs/REVIEW.md`
Bu Faz 6, son faz — tüm sistemi bir kez daha tara:
- **Yasak metrik (kural 7):** `impressions`/`reach`/`saves`/`profile_views`/demografi hiçbir
  şema/DB/API/PDF/promptta yok. Kohort ucu dahil.
- **Otomatik mesaj yok (hukuki):** `api/` içinde mesaj gönderen kod yolu yok (SEC-10 AST
  tarayıcısını Faz 6 dosyalarına da uygula); `outreach` `draft` doğuyor, PATCH yalnız kaydeder.
- **180-silme (hukuki):** dönüşmeyen veri 180 günde siliniyor — cron var ve çalışıyor.
- **Maliyet disiplini:** `audits.llm_cost_usd` LLM çağrılan denetimde dolu; alarm çalışıyor;
  gönderi başına LLM çağrısı yok (Haiku batch — SEC-9'dan hâlâ geçerli).
- **Sır:** `.env.example` tüm yeni anahtarlar değersiz; kod/log/fixture/commit'te gerçek anahtar
  yok; git geçmişinde `.env` izlenmemiş.
- **Kural 6:** hiçbir test canlı IG/Apify/Anthropic çağrısı yapmıyor; ağ kapalıyken suite yeşil
  (Playwright/DB SKIP'leri nedeni belgeli).

**Kabul kriterleri:**
- 4 blok testleri `tests/`'te; `pytest` yeşil, ağ kapalıyken de. Silme + alarm karşı-kanıtla ölçülü.
- `docs/REVIEW.md`: proje-sonu denetim — altı madde (yasak metrik, otomatik-mesaj-yok, 180-silme,
  maliyet, sır, kural 6) PASS/kanıtla. Bu, projenin kapanış güvenlik raporu.
- Yeni bulgu → `## Bloke`'ya sahibiyle.

**Kapanış:** `docs/TASKS.md`'de SEC-12'yi `## Biten`'e taşı. `git add tests/ .github/
docs/REVIEW.md docs/TASKS.md`, `sec:` commit. Sonra "SEC-12 bitti, Faz 6 + proje-sonu denetim
tamam" de.
