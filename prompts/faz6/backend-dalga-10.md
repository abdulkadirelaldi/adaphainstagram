# [BACKEND] Faz 6 · Dalga 10 — BE-22 (silme cron + maliyet alarmı) + BE-23 (rate limit + kohort)

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku (hukuki sınırlar + maliyet
disiplini + kural 6/7). Sadece `api/**`, `.env.example`, `pyproject.toml`. İki görev, sırayla,
ayrı commit'ler. `openapi.yaml` BE-21'de dondu — yeni uç yoksa dokunma.

---

## GÖREV BE-22 — 180 günlük silme cron'u + maliyet alarmı

**Amaç:** Dönüşmeyen adayın verisini 180 gün sonra silen cron; aylık LLM maliyeti eşiği aşınca
alarm.

**Oku:** `CLAUDE.md` hukuki sınırlar (**dönüşmeyen adayın verisi 180 gün sonra otomatik silinir
— cron, opsiyonel değil**) + maliyet disiplini. `docs/SPEC.md` §3 (tablolar, FK zinciri).
BE-9 (arq worker — scheduled job buraya). `docs/openapi.yaml` (BE-21 `Stats` alarm alanı).

**Dokunabileceğin dosyalar:** `api/**`, `.env.example`

**Yapılacaklar:**

### 180 günlük silme cron'u (opsiyonel değil)
- arq **scheduled** job: `discovered_at` 180 günden eski **ve** dönüşmemiş
  (`outreach.status != 'won'`) işletmeleri ve bağlı tüm kayıtları siler
  (`snapshots`/`posts`/`triage_scores`/`audits`/`outreach` — FK zinciri, CASCADE veya sıralı).
- "180 gün" ve "şimdi" **enjekte edilen referans zamandan** (BE-11 deseni) — üretimde `now()`,
  testte sabit referans. `datetime.now()`'ı saf silme mantığına gömme.
- `won` olan aday **silinmez** (dönüşen müşteri verisi korunur). Kararı belgele.
- Üretilen PDF dosyası da silinsin (`audits.pdf_path` diskteki dosya) — yetim dosya bırakma.

### Maliyet alarmı
- Aylık `audits.llm_cost_usd` toplamı bir eşiği (`.env`, ayarlanabilir) aşınca alarm: **log**
  (net uyarı) + `Stats` yanıtındaki alarm alanı (BE-21 sözleşmesi) `true`.
- `.env.example`'a eşik anahtarını **değersiz** ekle. Alarm bir *bildirim*; sistemi durdurmaz.

**Kabul kriterleri:**
- Silme cron'u fixture + referans zamanla: 180 günden eski dönüşmemiş aday **siliniyor**
  (bağlı kayıtlar + PDF dahil); `won` aday **korunuyor**; 180 günden yeni aday korunuyor.
  Elle/deterministik doğrula, kapanış notuna yaz.
- Maliyet alarmı: eşik altı → `Stats` alarm `false`; eşik aşımı → `true` + log.
- `ruff` + `mypy api/` + `pytest` yeşil; yasak-metrik + anahtar-sızıntı grep boş.

**Kapanış:** `docs/TASKS.md`'de BE-22'yi `## Biten`'e taşı (silme + `won` koruması + alarm).
Faz 6 kutusu #1 (silme) + #4 (alarm) işaretle. `git add api/ .env.example docs/TASKS.md`,
`be:` commit. Sonra BE-23'e geç.

---

## GÖREV BE-23 — rate limit middleware + kohort ucu

**Amaç:** API yüzeyini aşırı istekten korumak (`429`+`Retry-After`) ve kohort ucunu (FE-3-B1)
uygulamak.

**Oku:** `docs/openapi.yaml` (BE-21: `429`/`Retry-After` hangi uçlarda; kohort ucu şeması).
`docs/TASKS.md` `## Bloke` → FE-3-B1. `docs/SPEC.md` §4 (kohort medyanı — kategori bazlı).
BE-1 (redis — rate limit sayacı için).

**Dokunabileceğin dosyalar:** `api/**`, `.env.example`

**Yapılacaklar:**
- **Rate limit:** BE-21 sözleşmesindeki uçlarda (en az `/discovery/run`, `/businesses/{id}/audit`)
  istek sınırı. Redis-tabanlı sayaç; aşılınca **`429` + `Retry-After`**. Sınır `.env`'den
  ayarlanabilir, `.env.example` değersiz. Origin/CORS listesi değişmiyor.
- **Kohort ucu (FE-3-B1):** BE-21 sözleşmesindeki uç (ör. `GET /stats/categories`) → kategori
  başına skor/etkileşim dağılımı (medyan + çeyrekler; SPEC §4). DB'den; kohort<5 kategori
  işaretli (SPEC §4 — yetersiz kohort). Yasak alan yok (kural 7).

**Kabul kriterleri:**
- Sınır aşımında `429` + `Retry-After` başlığı; sınır altında normal. `curl`/test ile doğrula.
- `GET /stats/categories` (veya sözleşmedeki ad) kategori dağılımını döndürüyor; erişim/gösterim/
  demografi **yok** (kural 7); üretilen `/openapi.json` sözleşmeyle uyumlu.
- `ruff` + `mypy api/` + `pytest` yeşil; yasak-metrik grep boş.

**Kapanış:** `docs/TASKS.md`'de BE-23'ü `## Biten`'e taşı; `## Bloke` FE-3-B1'e `→ BE-23 ile
çözüldü` ekle. Faz 6 kutusu #2 (rate limit) işaretle. `git add api/ .env.example docs/TASKS.md`,
`be:` commit. Sonra orkestra şefine "BE-22+BE-23 bitti; SEC-12 ve FE-8 canlı doğrulayabilir" de.
