# [GÜVENLİK & TEST] Faz 2 · SEC-4 — fixture'lar + normalize kontrat testleri

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (özellikle kural 6 ve 7).
Sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig dosyaların altına yazarsın.
`api/**`'ye dokunmazsın.

**Bu görev backend'i (BE-7/BE-8) bloke ediyor** — onlar senin yazdığın fixture'larla adaptör
gövdesini doğrulayacak. Önce bu.

## GÖREV SEC-4 — fixture'lar ve şema kontratı

**Amaç:** Üç kaynağın dış-API yanıt örneklerini sabit JSON fixture olarak yazmak ve BE-6'nın
normalize şemalarının kontrat davranışını test etmek. **Canlı çağrı yok** (kural 6).

**Oku:** `docs/SPEC.md` §2 (üç kaynak ne döndürür) ve §3 (hangi alan hangi tabloya).
`api/adapters/base.py` — BE-6'nın `NormalizedBusiness`, `NormalizedProfile`, `NormalizedPost`,
`DiscoveryQuery` şemaları ve `extra="forbid"` muhafızı burada. Fixture'ların **ham** dış-API
biçiminde olacağını unutma; normalize şema adaptörün çıktısıdır, fixture'ın kendisi değil.

**Dokunabileceğin dosyalar:** `tests/**`, `docs/REVIEW.md`

**Yapılacaklar:**

### 1. Fixture'lar (`tests/fixtures/`)
- `places_response.json` — Google Places API'nin bir işletme arama yanıtının **ham** biçimi.
  Birden çok işletme içersin (en az 3), en az biri eksik alanlı (telefon yok / website yok)
  ki normalize `None` yolu test edilebilsin. Alan adları gerçek Places API'sindeki gibi olsun.
- `ig_business_discovery.json` — IG Business Discovery API'nin bir profil + son gönderiler
  yanıtının ham biçimi. Gönderiler `like_count`/`comments_count` taşısın.
- `apify_profile.json` — Apify Instagram Scraper'ın profil + gönderi + yorum çıktısının ham
  biçimi. **Kritik:** bu fixture bilerek `CLAUDE.md` kural 7'nin yasakladığı alanları içersin
  (ör. `impressions`, `reach`, `saves`, `profile_visits`, demografi) — çünkü Apify gerçekte
  bunları döndürür. Normalize katmanının bunları **düşürdüğünü** SEC-5'te ve backend'in kendi
  doğrulamasında kanıtlamak için yasak alanların ham veride bulunması gerekir.
- Her fixture'ın yanına kısa bir not (`tests/fixtures/README.md`): hangi ham alan hangi
  normalize alanına gidiyor, hangileri `raw`'a gömülüp yüzeye çıkmıyor.

### 2. Kontrat testleri (`tests/`) — adaptör gövdesi olmadan çalışır
- `NormalizedProfile`/`NormalizedBusiness`/`NormalizedPost` doğrudan test edilir:
  - Geçerli veriyle örnekleniyor.
  - `extra="forbid"` gerçekten koruyor: yasak bir alan (`impressions` gibi) normalize modele
    verilince `ValidationError` atıyor. **Bu testi Apify fixture'ındaki gerçek yasak alan
    adıyla yaz** — böylece "yasak alan normalize yüzeye çıkarsa test kırmızı" makine kuralı olur.
  - `ge=0` sınırları çalışıyor (negatif `followers`/`like_count` reddediliyor).
  - `raw` alanı serbest dict kabul ediyor (ham veri oraya gömülebiliyor).
- Fixture'lar geçerli JSON olarak yükleniyor ve beklenen üst-düzey anahtarları taşıyor.

**Yapmayacakların:**
- Adaptörün fixture'ı normalize etmesini test etme — adaptör gövdesi BE-7/BE-8'de gelecek,
  o entegrasyon testi **SEC-5** (BE-9 sonrası). Şimdi sadece şema kontratı + fixture geçerliliği.
- `api/`'ye dokunma. Adaptör gövdesinde eksik görürsen `## Bloke`'ya yaz.
- Fixture'a **gerçek** işletme/kişi verisi koyma — uydurma ama gerçekçi Samsun örnekleri
  (kural 6 ruhu: sabit, sahte, tekrarlanabilir).

**Kabul kriterleri:**
- `tests/fixtures/` altında üç JSON + README var, hepsi geçerli JSON.
- `pytest` yeşil; en az: `extra="forbid"` yasak-alan reddi, `ge=0` reddi, fixture yükleme testi.
- Yasak-alan testi gerçekten ölçüyor: `NormalizedProfile`'a Apify'ın yasak alanını eklemeyi
  dene → `ValidationError`. (Susturma yok, gerçek red.)
- Ağ kapalıyken `pytest` yine yeşil (kural 6).
- `ruff check .` + `mypy` (test hedefliyse) temiz.

**Kapanış:** `docs/TASKS.md`'de SEC-4'ü `## Biten` altına taşı. Backend'e fixture'ların hazır
olduğunu bildiren bir satırı da not düş. `git add tests/ docs/REVIEW.md docs/TASKS.md`
(`git add -A` yasak), `sec:` prefix'iyle commit'le. Sonra orkestra şefine "SEC-4 fixture'lar
hazır, BE-7/BE-8 başlayabilir" de.
