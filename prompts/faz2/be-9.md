# [BACKEND] Faz 2 · BE-9 — worker + cache + handle eşleme + canlı keşif ucu

**BEKLET: SEC-6 bitene kadar gönderme.** `tests/fixtures/` içindeki Places fixture'ı ~20
işletmeye genişlemiş ve handle→profil eşlemesi `tests/fixtures/README.md`'de belgeli olmalı.
`docs/TASKS.md`'de SEC-6 `## Biten`'e taşınmışsa hazırdır.

---

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku (özellikle maliyet disiplini ve
kural 6/7). Sadece `api/**`, `docs/openapi.yaml` ve backend kök dosyalarına yazarsın. Bu görev
Faz 2'nin son iki çıkış kutusunu kapatıyor.

## GÖREV BE-9 — keşif akışını uçtan uca canlıya al

**Amaç:** `POST /discovery/run` işini gerçek bir arq worker'ında yürütmek: Places keşfi →
işletme upsert → IG handle eşleme → profil çekimi (7 gün cache'li) → snapshot/posts persist.
Tek komutla ~20 işletme keşfedilip snapshot'ı alınmalı.

**Oku:**
- `docs/openapi.yaml` — BE-6'nın `POST /discovery/run` + `GET /jobs/{id}` sözleşmesi (değişmez;
  eksik görürsen önce sözleşmeyi ayrı commit'le güncelle, kural 3).
- `docs/TASKS.md` → "**IG handle eşleme sözleşmesi (Faz 2)**" — çıkarım mantığın buna birebir
  uyacak.
- `tests/fixtures/README.md` — SEC-6'nın handle→profil eşleme yapısı; demo'da bunu kullanacaksın.
- BE-7 (`PlacesAdapter`, `upsert_businesses`), BE-8 (`api/services/profile.py` fallback,
  `persist_profile`) — bunları çağıracaksın, yeniden yazmayacaksın.
- SPEC §7 (kuyruk/job semantiği), maliyet disiplini (`CLAUDE.md`: aynı hesap 7 gün içinde
  tekrar kazınmaz).

**Dokunabileceğin dosyalar:** `api/**`, `.env.example`, `pyproject.toml` (arq bağımlılığı),
`docs/openapi.yaml` (yalnız sözleşme eksikse).

**Yapılacaklar:**

### 1. arq worker
- `api/worker.py` (veya uygun modül): arq worker, Redis'e bağlı (BE-1'in redis'i). Worker
  ayarları `pydantic-settings`'ten.
- Bir keşif job fonksiyonu: `DiscoveryQuery` alır, aşağıdaki akışı yürütür, ilerleme ve sonuç
  özetini job sonucuna yazar.

### 2. Canlı uçlar
- `POST /discovery/run` → gövdeyi `DiscoveryQuery`'ye doğrula, arq'ya **enqueue** et, `job_id`
  döndür. **Senkron scraping yok** — uç anında döner (SPEC §7).
- `GET /jobs/{id}` → arq job durumunu sözleşmedeki enum'a (`queued|running|done|error` vb.)
  eşle; ilerleme/sonuç özeti ve hata mesajını (nullable) döndür. Bilinmeyen id → 404.

### 3. Keşif orkestrasyonu (job içi akış)
1. `PlacesAdapter.discover(query)` → `NormalizedBusiness` listesi (BE-7). Demo'da adaptöre
   fixture yanıtı veren sahte HTTP client enjekte edilir — **canlı Places çağrısı yok** (kural 6).
2. `upsert_businesses(...)` (BE-7) → `businesses` yazımı/güncellemesi.
3. **Handle eşleme** — TASKS'taki sözleşme: her işletmenin `raw`'ından `instagram.com/{handle}`
   URL'sini regex'le çıkar; bulunanı `businesses.ig_handle`'a yaz; bulunmayan NULL kalır,
   snapshot alınmaz. Ada benzerliğinden **tahmin etme**.
4. Handle'ı olan her işletme için profil çek: **BE-8'in `api/services/profile.py` fallback
   servisi** (Business Discovery → boşsa Apify). Demo'da adaptörlere fixture yanıtı enjekte
   edilir.
5. **7 gün cache (maliyet disiplini):** profil çekmeden önce Redis'te
   `ig_handle` için taze (< 7 gün) bir snapshot işareti var mı bak. Varsa **dış çağrı yapma**,
   o hesabı atla (mevcut snapshot geçerli). Yoksa çek, `persist_profile` (BE-8) ile yaz,
   cache anahtarını 7 gün TTL ile set et. Cache anahtar deseni ve TTL'i `.env`/sabit olarak
   nette olsun.
6. Job sonucu: keşfedilen işletme sayısı, handle eşlenen sayı, yeni snapshot sayısı, cache
   nedeniyle atlanan sayı, fallback'e düşen sayı.

### 4. Tek komutlu demo
- Bir yönetim komutu / script (ör. `python -m api.discover_demo` veya bir arq üzerinden tetik)
  ile fixture setinden ~20 işletme keşfedilip handle'lıların snapshot'ı alınabilsin. Bu komut
  **canlı çağrı yapmaz**, SEC-6 fixture'ını kullanır. Nasıl çalıştırılacağını kapanış notuna yaz.

**Yapmayacakların:**
- Yasak metrik alanını (kural 7) hiçbir yere taşıma — BE-8'in normalize düşürmesine güven ama
  yeni bir yol açma.
- Senkron scraping ucu, süresiz job, cache'siz tekrar çekim (maliyet disiplini ihlali) yazma.
- Gerçek Places/IG/Apify çağrısı yapan test yazma. Kalıcı entegrasyon testi SEC-5'in.

**Kabul kriterleri:**
- `POST /discovery/run` `job_id` dönüyor ve **anında** (iş worker'da sürüyorken); `GET /jobs/{id}`
  durumu `queued→running→done` ilerliyor, sonuç özeti dolu; bilinmeyen id → 404.
- Demo komutu fixture setiyle çalışınca: ~20 işletme `businesses`'ta, handle'lılar
  `ig_handle` dolu + `snapshots`/`posts` yazılı, handle'sızlar `ig_handle=NULL` + snapshot yok.
  Sayıları kapanış notuna yaz.
- **7 gün cache kanıtı:** demo'yu **iki kez** çalıştır; ikinci koşuda cache'li hesaplar için
  dış çağrı yapılmıyor (enjekte client çağrı sayacıyla veya log ile göster) ve çift snapshot
  oluşmuyor. Elle doğrula, kapanış notuna yaz.
- Fallback demo'da tetikleniyor (SEC-6'nın BD-boş handle'ıyla) → o hesap `snapshots.source=apify`.
- `ruff check .` + `ruff format --check` + `mypy api/` + `pytest` yeşil (CI pin'leri).
- `git grep -nE "impressions|reach|saves|profile_views|profile_visits|demographics" -- api/` boş.

**Kapanış:** `docs/TASKS.md`'de BE-9'u `## Biten`'e taşı (demo komutu, sayılar, cache kanıtı,
fallback ile). Faz 2 çıkış kutusu #3 ve #4'ü işaretle. `git add api/ .env.example pyproject.toml
docs/openapi.yaml docs/TASKS.md`, `be:` prefix'iyle commit'le. Sonra orkestra şefine "BE-9
canlı, Faz 2 çıkış kutuları hazır; FE-4 canlı doğrulama ve SEC-5 başlayabilir" de.
