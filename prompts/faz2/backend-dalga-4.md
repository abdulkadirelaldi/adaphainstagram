# [BACKEND] Faz 2 · Dalga 4 — BE-7 + BE-8

**BEKLET: SEC-4 bitene kadar gönderme.** `tests/fixtures/` altında `places_response.json`,
`ig_business_discovery.json`, `apify_profile.json` var olmalı — adaptörlerini bu fixture'lara
göre yazıp doğrulayacaksın. `docs/TASKS.md`'de SEC-4 `## Biten`'e taşınmışsa hazırdır.

---

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku. Sadece `api/**` ve
`docs/openapi.yaml` altına yazarsın. İki görev, sırayla, ayrı commit'ler. `openapi.yaml`
BE-6'da donmuştu — yeni uç yoksa dokunma (`CLAUDE.md` kural 3).

BE-6'nın soyutlamasını oku ve **uy**: `api/adapters/base.py` içindeki `DiscoverySource`/
`ProfileSource` protokolleri, `NormalizedBusiness`/`NormalizedProfile`/`NormalizedPost`
şemaları, `register_discovery`/`register_profile` dekoratörleri. İskelet adaptör dosyaları
(`api/adapters/places.py`, `business_discovery.py`, `apify.py`) zaten kayıtlı; sen gövdelerini
dolduruyorsun. İmzayı bozarsan `api/adapters/__init__.py`'deki uyum atamaları mypy'de patlar.

---

## GÖREV BE-7 — Google Places adaptörü + işletme kaydı yazımı

**Amaç:** `PlacesAdapter.discover()`'ı gerçek gövdeyle doldurmak ve keşfedilen işletmeleri
`businesses` tablosuna yazmak.

**Oku:** `docs/SPEC.md` §2 (Places ne verir: ad, kategori, adres, telefon, site, değerlendirme
sayısı), §1 (keşif akışı), §3 (`businesses` alanları). `tests/fixtures/places_response.json`.

**Dokunabileceğin dosyalar:** `api/**` (özellikle `api/adapters/places.py` ve persist katmanı),
`.env.example` (Places API anahtar adı — **değersiz**).

**Yapılacaklar:**
- `PlacesAdapter.discover(query)` → `httpx` ile Places API'yi çağırır, yanıtı
  `NormalizedBusiness` listesine normalize eder. HTTP client dışarıdan enjekte edilebilir
  olsun (test fixture'la çağırabilsin, `CLAUDE.md` kural 6 — testte canlı çağrı yok).
- API anahtarı `pydantic-settings` ile `.env`'den; koda gömme (kural 4). `.env.example`'a
  anahtar adını değersiz ekle.
- **Persist:** normalize işletmeleri `businesses`'a yaz. `place_id` benzersiz (BE-2 unique
  constraint) — aynı `place_id` tekrar gelince **upsert** (çift kayıt yok). `discovered_at`
  ilk keşifte set, tekrar keşifte korunur.
- Fixture'daki eksik-alanlı işletme `None` alanlarla temiz normalize olmalı (patlamamalı).

**Kabul kriterleri:**
- `PlacesAdapter().discover(...)` fixture yanıtıyla (enjekte edilmiş sahte client) çağrılınca
  `NormalizedBusiness` listesi dönüyor; alan eşlemesi SPEC §3 ile uyumlu; eksik alanlar `None`.
- Aynı fixture iki kez persist edilince `businesses`'ta çift kayıt yok (upsert doğrulandı).
- `.env.example`'da Places anahtarı **değersiz** var; `git grep` ile gerçek anahtar sızıntısı yok.
- `ruff check .` + `ruff format --check` + `mypy api/` + `pytest` yeşil (CI pin'leri).
- **Kalıcı test güvenlik ajanınındır** (`tests/`); sen elle doğrula ve kapanış notuna nasıl
  doğruladığını yaz. `api/` içine test dosyası yazma.

---

## GÖREV BE-8 — IG Business Discovery + Apify adaptörleri + snapshot yazımı

**Amaç:** İki profil adaptörünün gövdesini doldurmak ve `NormalizedProfile`'ı `snapshots` +
`posts` tablolarına yazmak.

**Oku:** `docs/SPEC.md` §2 (Business Discovery önce, çalışmazsa Apify — fallback), §3
(`snapshots`, `posts` alanları). `tests/fixtures/ig_business_discovery.json` ve
`tests/fixtures/apify_profile.json`.

**Dokunabileceğin dosyalar:** `api/**` (`business_discovery.py`, `apify.py`, persist katmanı),
`.env.example` (Apify token adı — değersiz).

**Yapılacaklar:**
- `BusinessDiscoveryAdapter.fetch_profile(handle)` ve `ApifyAdapter.fetch_profile(handle)` →
  ham yanıtı `NormalizedProfile`'a çevirir (`posts` listesi dahil). HTTP client enjekte
  edilebilir.
- **Yasak alan muhafızı (kural 7):** Apify fixture'ı bilerek `impressions`/`reach`/`saves`/
  demografi taşıyor. Normalize katmanı bunları **`raw`'a gömer, normalize yüzeye çıkarmaz.**
  `NormalizedProfile.extra="forbid"` olduğu için yanlışlıkla taşırsan doğrulama patlar — bu
  bir güvenlik ağı, ona güvenme, alanı bilerek düşür.
- **Fallback (SPEC §2):** bir profil çekiminde önce Business Discovery denenir, o veri
  vermezse Apify'a düşülür. Bu orkestrasyonu nereye koyduğunu (adaptör dışı bir servis
  katmanı) kapanış notunda belirt.
- **Persist:** `NormalizedProfile` → bir `snapshots` satırı (+ `raw` JSON) ve bağlı `posts`
  satırları. `snapshots.source` alanı hangi adaptörün ürettiğini yazsın
  (`business_discovery` | `apify`).
- **Maliyet disiplini kancası:** aynı hesabın 7 gün içinde tekrar çekilmemesi BE-9'un cache
  işidir; sen persist'i idempotent tut ki BE-9 cache'i sardığında çift snapshot oluşmasın.
  Cache'i **burada yazma** — sadece BE-9'un sarabileceği temiz bir çekim fonksiyonu bırak.

**Kabul kriterleri:**
- Her iki adaptör fixture'la (enjekte client) çağrılınca `NormalizedProfile` dönüyor; `posts`
  doğru sayıda ve alan eşlemesi SPEC §3 ile uyumlu.
- **Apify normalize çıktısında yasak alan yok:** `NormalizedProfile`/`NormalizedPost`
  serialize edilince `impressions`/`reach`/`saves`/`profile_visits`/demografi anahtarı
  bulunmuyor; bu veriler yalnızca `raw` altında. Elle doğrula, kapanış notuna yaz.
- Fallback yolu: Business Discovery boş dönerse Apify'a düşülüyor (fixture'la ikisini de tetikle).
- `snapshots` + `posts` persist ediliyor; `snapshots.source` doğru; tekrar persist idempotent.
- `git grep -nE "impressions|reach|saves|profile_views|profile_visits|demographics|follower_age|gender" -- api/`
  **boş** (yasak alanlar yalnız fixture'da/`raw` verisinde, koda gömülü alan olarak değil).
- `ruff` + `mypy api/` + `pytest` yeşil.

**Kapanış:** `docs/TASKS.md`'de BE-7 ve BE-8'i `## Biten`'e ayrı satırlarla taşı (fallback'i
nereye koyduğunu ve yasak-alan düşürmeyi nasıl doğruladığını yaz). Her görevi ayrı `be:`
commit'le. `git add api/ .env.example docs/TASKS.md`. Sonra orkestra şefine "BE-7+BE-8 bitti,
BE-9 (worker+cache+uç) hazır" de.
