# [GÜVENLİK & TEST] Faz 2 · SEC-5 — entegrasyon + cache + gizlilik denetimi

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku (özellikle kural 6, 7 ve
maliyet disiplini). Sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig
dosyalarına yazarsın. `api/**`'ye dokunmazsın — bulgu `## Bloke`'ya.

## GÖREV SEC-5 — Faz 2'yi bağımsız doğrula

**Amaç:** BE-7/BE-8/BE-9'un iddialarını (normalize, fallback, 7 gün cache, yasak-alan düşürme)
kendi testlerinle, backend'in elle doğrulamasından bağımsız olarak makineye bağlamak.

**Oku:** `docs/SPEC.md` §2/§3, `docs/TASKS.md` `## Biten` → BE-7/BE-8/BE-9 satırları (ne iddia
ettiler), `## Bloke` → SEC-6-N1. `tests/fixtures/README.md`. `api/` içindeki adaptör, servis,
handle, cache ve persist fonksiyonlarını **oku** (yazma).

**Dokunabileceğin dosyalar:** `tests/**`, `docs/REVIEW.md`

**Yapılacaklar:**

### 1. Adaptör entegrasyon testleri (artık gövde var)
- Her adaptörün fixture'ı gerçekten normalize ettiğini test et (SEC-4'te şema kontratıydı,
  şimdi adaptör→normalize): Places fixture → `NormalizedBusiness` listesi, alan eşlemesi
  README ile; BD/Apify fixture → `NormalizedProfile` + `posts`, alan adı dönüşümleri
  (`comments_count→comment_count`, `videoViewCount→view_count`, `type→media_type`) doğru.
- Enjekte edilen sahte HTTP client'la; **canlı çağrı yok** (kural 6, ağ muhafızı altında geçmeli).

### 2. Handle eşleme sözleşme testi
- `api/core/handle.py` çıkarımını fixture'ın 20 işletmesiyle test et: 14 handle, 6 NULL, dört
  yanlış-pozitif tuzağı (facebook, `help.instagram.com`, `instagramm…`, düz site) **NULL**.
- **Sözleşme regresyon testi:** ada benzeyen ama instagram olmayan bir link için handle
  üretilmediğini kalıcı test yap — "ad tahmini yok" maddesi bir daha sessizce kırılmasın.

### 3. Fallback testi
- Business Discovery boş dönen handle'da (SEC-6'nın `sahilkahveevi`/`cadde19kafe`) Apify'a
  düşüldüğünü ve `snapshots.source=apify` olduğunu; BD dolu handle'da `business_discovery`
  kaldığını test et. Ağ/HTTP hatasının **yükselmeye devam ettiğini** (yanlış kaynağa sessiz
  düşüş olmadığını) da doğrula.

### 4. 7 gün cache denetimi (maliyet disiplini)
- `run_discovery`'yi **iki kez** çalıştıran bir test: ikinci koşuda cache'li handle'lar için
  dış profil çağrısı **yapılmıyor** (enjekte client çağrı sayacı = 0) ve **çift snapshot
  oluşmuyor**. BE-9 bunu elle gösterdi; sen kalıcı teste bağla.
- Cache TTL'inin 7 gün (`snapshot_cache_ttl_seconds`) olduğunu ve süre dolunca yeniden
  çekildiğini doğrula (TTL'i test için kısaltıp ya da cache anahtarını düşürüp tetikle —
  gerçek zaman bekleme yok).

### 5. Uçtan uca gizlilik denetimi (kural 7) — `docs/REVIEW.md`
- Apify fixture'ı yasak alanlar taşıyor. Zinciri baştan sona izle: **ham fixture → normalize →
  persist → `snapshots`/`posts` sütunları → `/businesses` yanıtı.** Yasak alanların
  (`impressions`/`reach`/`saves`/`profile_visits`/demografi) hiçbir aşamada normalize yüzeye,
  DB sütununa veya API yanıtına çıkmadığını; yalnız `snapshots.raw` JSON'unda kaldığını
  doğrula. Her aşama için PASS/kanıt satırı.
- `.env.example` denetimi: BE-7/BE-8/BE-9'un eklediği yeni anahtarlar (Places, Apify, cache
  TTL, arq) **değersiz** mi? Gerçek anahtar sızıntısı var mı?

**Kabul kriterleri:**
- Yukarıdaki 5 blok için testler `tests/`'te; `pytest` yeşil, ağ kapalıyken de yeşil.
- Handle sözleşme regresyon testi gerçekten ölçüyor: çıkarımı ad-tahminine açacak bir değişiklik
  testi kırmızıya döndürür (karşı-kanıtı kapanış notunda anlat, kodu bozma).
- Cache testi gerçekten ölçüyor: cache sarmalı devre dışı bırakılınca ikinci koşu dış çağrı
  yapar ve test kırmızıya döner.
- `docs/REVIEW.md` gizlilik zinciri (5 aşama) ve `.env.example` denetimi PASS/kanıt satırlarıyla.
- Yeni bulgu varsa `## Bloke`'ya sahibiyle yazıldı.

**Kapanış:** `docs/TASKS.md`'de SEC-5'i `## Biten`'e taşı. `git add tests/ .github/
docs/REVIEW.md docs/TASKS.md` (`git add -A` yasak), `sec:` prefix'iyle commit'le. Sonra
orkestra şefine "SEC-5 bitti, Faz 2 bağımsız doğrulandı" de.
