# Görev tahtası

Ajanlar arası tek senkronizasyon noktası. Her ajan görevine başlarken bu dosyayı okur,
bitirince günceller. Orkestra şefi yeni görev ekler, diğerleri kendi satırını taşır.

Görev id formatı: `BE-1`, `FE-1`, `SEC-1`. Numara asla geri kullanılmaz.

---

## Aktif faz

**Faz 1 — iskelet. ✅ TAMAMLANDI** · **Faz 2 — veri. ✅ TAMAMLANDI (SPEC bitiş kriteri)** ·
**Faz 3 — skorlama açık** (SPEC §8).

Faz 1 kutuları (4/4): `/health` + postgres/redis, `/stats`+`/businesses` sahte veri, panel
gerçek istekle çiziyor, lint+tip+test lokal yeşil. Docker ve CI kutuları makine kısıtına göre
dürüstçe daraltıldı (remote/Docker yok), bkz. `## Bloke`.

Faz 2 kutuları (4/4): adaptör protokolü + normalize şema, `/discovery/run`+`/jobs/{id}`
sözleşmesi, keşif→snapshot+cache, tek komutla 20 işletme (`discover_demo`). **Panel-canlı
entegrasyonu (FE-4 done) Faz 2 bitiş kutusunun *dışında*** — SPEC §8 Faz 2 panelde göstermeyi
istemiyor. İki entegrasyon boşluğu (`FE-4-B1`, `FE-4-B2`) Faz 3'e taşındı, bkz. aşağıda.

## Açık

### Faz 3 — skorlama (SPEC §4, §8). Bitiş kriteri kutusu:

- [ ] Triyaj motoru üç alt skoru (aktiflik, potansiyel, kapasite) ve ağırlıklı **çarpım**
      birleşik skorunu hesaplıyor (SPEC §4). Mutlak etkileşim eşiği **yok** — kohort medyanı
      kullanılıyor; kohort<5 → potansiyel hesaplanmaz, hesap `watch`.
- [ ] Durum atama: skor<40 `rejected`, 40–69 `watch`, ≥70 `qualified`; `triage_scores`'a yazılıyor.
- [ ] `/businesses` ve `/stats` **DB'den** okuyor (fake_data değil), son skoru/durumu gösteriyor
      (FE-4-B1 kapanır).
- [ ] **100 hesap taranıp panelde skorlarıyla listeleniyor** — fixture'la, LLM yok (SPEC §8).

| id | ajan | görev | bağımlı |
|---|---|---|---|
| BE-11 | backend | Triyaj skorlama motoru (aktiflik/potansiyel/kapasite/çarpım + kohort medyanı + durum) + `triage_scores` persist + discovery job'a tetikleme fazı (SPEC §4) | — |
| BE-12 | backend | `/businesses` + `/stats`'ı DB'ye bağla, son skoru göster (FE-4-B1) | BE-11 |
| SEC-7 | güvenlik | Skorlama testleri: çarpım çökme davranışı, kohort<5→watch, eşikler, mutlak-eşik yokluğu | BE-11 |
| FE-5 | frontend | FE-4 done canlı doğrulama (BE-10) + panel gerçek skorları gösteriyor (BE-12) | BE-10, BE-12 |

### Triyaj tetikleme kararı (Faz 3 — orkestra şefi sabitledi)

Skorlama *ne zaman* çalışır SPEC'te açık değil. İki ajanı (BE skorlama + FE panel) bağladığı
için sabitleniyor: **triyaj skorlama, discovery job'unun snapshot yazımından sonraki son
fazıdır.** Ayrı bir "skorla" ucu Faz 3'te yok — `POST /discovery/run` işi tamamlandığında DB'de
skorlanmış işletmeler durur, panel `done` invalidate'inde onları gösterir. Bu FE-4-B1'i de
kapatır: job biter → `/businesses` DB'den skorlu okur → tablo gerçek keşifle tazelenir.

### Sıralama notu (Faz 3)

BE-10 (worker fixture) ve SEC-8 (fixture 100) skorlamadan bağımsız, hemen paralel başlar.
BE-11 skorlama motoru fixture içeriğinden bağımsız (SPEC §4'e bakar), o da paralel; 100-hesap
demo'su SEC-8 fixture'ıyla birleşince kapanır. BE-12 uçları DB'ye bağlar (BE-11'in yazdığı
skorları okur). SEC-7 skorlama motorunu bağımsız test eder. FE-5 en sonda: BE-10 ile canlı done,
BE-12 ile gerçek skorlar.

### IG handle eşleme sözleşmesi (Faz 2 — orkestra şefi sabitledi)

SPEC §1 akışında "IG handle eşleme" adımı var ama *nasıl* eşleneceği tanımsız. İki ajanı
(SEC-6 fixture + BE-9 çıkarım) bağladığı için sözleşme burada donuyor:

- Handle **yalnızca açık bir bağlantıdan** türetilir: Places sonucunun `raw` alanındaki website
  veya sosyal bağlantılardan `instagram.com/{handle}` biçimindeki URL regex'le çıkarılır.
- Ad benzerliğinden **tahmin edilmez** — yanlış eşleme = yanlış işletmeye rapor = SPEC hukuki
  sınır ihlali. Belirsizse eşleme yok.
- Handle bulunamayan işletme `ig_handle=NULL` kalır ve snapshot alınmaz (keşfedilir ama
  taranmaz).
- İşletme/kişisel hesap ayrımı (SPEC §1) profil çekiminde `is_professional` ile netleşir;
  handle eşleme aşamasında değil.
- SEC-6 fixture'ı bu sözleşmeye uyar: ~20 işletmenin bir kısmı `raw`'da instagram URL taşır
  (handle + snapshot yolu), bir kısmı taşımaz (NULL yolu). BE-9 çıkarımı aynı sözleşmeye bakar.

### Sıralama notu (Faz 2)

**Fixture bağımlılığı düzeltmesi:** `tests/fixtures/` güvenlik sahipliğinde ama BE-7/BE-8
adaptörleri fixture'la doğrulanacak — bu yüzden **SEC-4 (fixture) BE-7/BE-8'den önce gelir**.
Backend adaptör gövdesini SEC-4'ün yazdığı dış-API yanıt örneklerine göre yazar. Kontrat
testlerinin adaptör-entegrasyon kısmı (adaptör fixture'ı gerçekten normalize ediyor mu, cache
7 günü tutuyor mu) BE-9'dan sonra `SEC-5`'te tamamlanır — o an gerçek gövde ve worker var.

Sıra: BE-6 (dondu) → **SEC-4 fixture ‖ FE-4 sözleşme UI** (paralel) → BE-7 ‖ BE-8 (fixture
gelince) → BE-9 (birleştirme + canlı uç) → SEC-5 + FE-4 canlı doğrulama.

BE-3 artık BE-2'yi beklemez. `CLAUDE.md` §3 gereği sözleşme koddan önce gelir; ayrıca
frontend'in BE-1..BE-2 zincirinin tamamını beklemesi paralelliği gereksiz yere öldürüyordu.

### Araç konfigürasyonu sahipliği (çakışma önleme)

Aynı dosyaya iki ajan yazmasın diye kesin ayrım:

- `pyproject.toml` → **backend**. İçinde `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`
  bölümü **bulunmaz**.
- `ruff.toml`, `mypy.ini`, `pytest.ini` → **güvenlik & test**. Lint/tip/test ayarları burada durur.
- `.env.example` → yazan **backend**, denetleyen **güvenlik & test** (bulgu `docs/REVIEW.md`'ye
  yazılır, dosya düzeltilmez).
- `.gitignore` → **güvenlik & test** (SEC-1-B3 ile karara bağlandı). Repo hijyeni onun alanı;
  diğer ajanlar bir yol eklenmesi gerektiğinde `## Bloke`'ya yazar, kendisi eklemez.

## Devam eden

_(ajan görevi alınca satırı buraya taşır ve yanına oturum tarihini yazar)_

- **FE-4** · frontend · Keşif tetikleme + `/jobs/{id}` yoklama UI'ı. **UI tamam; canlı doğrulama KISMİ — done/tazeleme iki backend/ortam bloğuna takıldı (FE-4-B1, FE-4-B2).** `gen:api` ile iki yeni uç tipi üretildi; `runDiscovery` (mutation) + `useJob` (poll) hook'ları; keşif çubuğu (sorgu/bölge/en-fazla + Tara) üst şeridin üstünde. Durum makinesi dört `JobState` değerini de görünür kılıyor; **poll `done`/`error`'da duruyor**; iş bitince liste+üst şerit+kohort invalidate ediliyor. `NEXT_PUBLIC_API_URL` kullanılıyor; hata rengi oksit değil mürekkep (DESIGN §1). `gen:api`+build+`tsc`+lint sıfır; hex/yasak-metrik grep boş.
  - **Gerçek backend'e karşı doğrulanan** (uvicorn+arq worker, yerel pg/redis; API 8001'e alındı çünkü 8000'de yabancı bir servis vardı — panel `NEXT_PUBLIC_API_URL=:8001` ile build edildi, CORS temiz): ① **gerçek `job_id`** uç anında 202 ile dönüyor; ② panel gerçek `POST /discovery/run` ve `GET /jobs/{id}` çağırıyor; ③ **error dalı gerçek** — worker Places anahtarı olmadan `error` döndürüyor, panel gerçek mesajı ("Places API anahtarı yok…") gösteriyor; ④ **poll `error`'da gerçekten durdu** (/jobs istekleri 2→2); ⑤ gerçek `/stats`+`/businesses` istekleri gidiyor.
  - **Route-mock ile kanıtlanan (canlı üretilemeyen kısım):** queued→running(4/9 progress)→done("N işletme")→poll durdu(4→4)→tablo tazelendi(2→4). Bu akış gerçek backend'de görünmüyor çünkü FE-4-B2 (anahtar yok → job anında error, running/done hiç oluşmuyor).
  - **Kalan:** done + gerçek DB tazeleme (~20 işletme) FE-4-B1 (uçlar DB okumuyor) ve FE-4-B2 (anahtar/worker-fixture) çözülünce doğrulanacak. UI tarafında yapılacak bir şey yok; görev bu iki blok kalkınca `## Biten`'e taşınır.

## Bloke

_(başka ajanın dizininde sorun gördüğünde buraya yaz, kendin düzeltme)_

- **FE-4-B1** · `orta` · **backend** — `GET /businesses` ve `GET /stats` hâlâ **fake_data'dan** okuyor, gerçek DB'den değil. Kanıt: `python -m api.discover_demo` DB'ye 20 işletme + 14 snapshot + 29 post yazdıktan sonra bile `/businesses?limit=200` **total=8** ve "Atakum Diş Kliniği" (score 82.4) gibi fake_data kayıtlarını döndürüyor; `businesses` tablosunda ise demo'nun yazdığı 20 gerçek kayıt duruyor. Sonuç: keşif işi DB'ye yazsa bile panel gerçek keşfi göremiyor → **FE-4 kabul kriteri 5 (iş bitince tablo ~20 gerçek işletmeyle tazeleniyor) doğrulanamıyor.** FE tarafı doğru: `done`'da `/businesses`/`/stats`/kohort invalidate edip yeniden çekiyor — ama backend DB yerine sabit listeyi döndürüyor. BE bu iki ucu DB'ye bağlamalı (muhtemelen Faz 3 skorlama ile birlikte; ama FE-4 canlı done doğrulaması buna bağımlı). `api/`'ye dokunmadım.
- **FE-4-B2** · `orta` · **backend/ortam** — Canlı keşif `done`'a hiç ulaşamıyor: arq worker gerçek `PlacesAdapter(api_key=…)` kuruyor ve `GOOGLE_PLACES_API_KEY` `.env`'de yok → iş **anında `error`**'a düşüyor ("Places API anahtarı yok"). Kural 6 canlı Places/IG/Apify çağrısını zaten yasakladığı için gerçek anahtarla da test edilmemeli. `discover_demo` MockTransport kullanıyor ama **worker'ı atlıyor** (job akışı yok); `api/worker.py`'de adaptör client'ını fixture'a çevirecek bir env bayrağı **yok**. Sonuç: gerçek `job` üzerinden `queued→running→done` doğrulaması bu makinede mümkün değil — done UI'ı yalnızca route-mock'ta kanıtlı. **Karar orkestra şefinin:** ya worker'a bir fixture/mock-transport modu (env flag) eklensin (BE), ya da FE-4'ün done doğrulaması için route-mock kanıtı kabul edilsin. `api/`'ye dokunmadım. → **BE-10 ile çözüldü** (`RADAR_FIXTURE_MODE`; gerçek worker anahtarsız fixture'la `queued→running→done`, sonuç 20 işletme — FE-5 canlı done'u bununla doğrulayabilir).

### Karara bağlananlar (orkestra şefi, dalga 1 sonu)

- **FE-4-B2** (canlı `discovery/run`→done bu makinede doğrulanamıyor) → *worker fixture modu
  eklenecek.* `BE-10` görevi açıldı: env-bayraklı fixture/mock-transport modu, kural 6 uyumlu.
  Faz 6 e2e de bunu kullanacak. FE-4 done doğrulaması BE-10 + BE-12 (DB bağı) sonrası `FE-5`'te.
- **FE-4-B1** (`/businesses`+`/stats` fake_data'dan okuyor, DB'den değil) → *Faz 3'e devredildi.*
  `BE-12` görevi: skorlama `triage_scores` yazdıktan sonra uçlar DB'den skorlu okur. Şimdi
  yarım bağlamak (skor NULL) yerine skorla birlikte tam bağlanır. FE-4 `## Devam eden`'de kaldı,
  `FE-5` ile kapanacak.

- **Docker** → *yerel servislerle kabul edildi.* Faz 1 çıkış kriteri yeniden yazıldı: doğrulama
  yerel postgres@16 + redis ve CI servis konteyneri üzerinden yapılır. `docker-compose.yml` ve
  `Dockerfile` repoda kalır ama **doğrulanmamış** sayılır; gerçek `docker compose up` doğrulaması
  Faz 6 (sertleştirme) kapsamına alındı. Faz atlanmadı — kriter makine kısıtına göre dürüstçe
  daraltıldı, gevşetilmedi.
- **SEC-1-B1 + SEC-1-B2** → `BE-5` görevi açıldı, backend'e verildi.
- **SEC-1-B3** → `.gitignore` sahipliği **güvenlik & test**'e atandı, `SEC-2` görevi açıldı.
- **BE-2-B1 + UP042** → ikisi de `ruff.toml` sahibinin (güvenlik & test) alanında; `SEC-3`
  görevine toplandı. UP042 kararı: ruff pin **yükseltilmiyor** — CI 0.12.0'da sabit kalır,
  `schemas.py` `StrEnum` düzeltmesi ruff bir üst pine çıktığında yapılır. Şimdi sadece
  BE-2-B1 (exclude yolu) kritik, çünkü her yeni migration'da tekrar eder.
- **CI (Faz 1 kutu #4)** → *lokal kapılarla kabul edildi.* Repoda git remote yok, GitHub
  Actions hiç çalışmadı. `ci.yml` yazıldı+doğrulandı ve ruff/mypy/pytest her dalgada lokal
  yeşil; gerçek Actions koşusu remote bağlanınca ilk push'ta olacak. Docker kutusuyla aynı
  dürüst daraltma — kriter gevşetilmedi, makine kısıtına göre yeniden yazıldı. **Remote
  kurulunca ilk iş:** push + Actions yeşilini gözle doğrula (Faz 6 sertleştirmeye de yazıldı).

- **Docker bu geliştirme makinesinde kurulu değil** (backend, BE-1 sırasında fark edildi).
  `/usr/local/bin/docker` var ama kaldırılmış `Docker.app`'e işaret eden kopuk bir symlink.
  Sonucu: `docker-compose.yml` ve `Dockerfile` yazıldı fakat **hiç çalıştırılamadı** —
  Faz 1 çıkış kriterlerinden "`docker compose up` ile üç servis healthy" kutusu bu makinede
  doğrulanamaz. `/health` bunun yerine brew ile kurulu yerel postgres@16 + redis'e karşı
  doğrulandı (sağlıklı yol, iki ayrı arıza yolu ve toparlanma — hepsi geçti). Compose
  dosyasında yazım hatası kalmış olabilir; ilk `docker compose up` deneyen ajan bunu
  hesaba katsın. Karar orkestra şefinin: Docker Desktop kurulacak mı, yoksa Faz 1 çıkış
  kriteri yerel servislerle mi kabul edilecek?

- **SEC-1-B1** · `orta` · **backend** — `api/routes/health.py:22` ve `:34` ruff `ASYNC109`: async fonksiyon `timeout` parametresi alıyor. Davranış doğru, üslup uyarısı. Ya `timeout` kaldırılıp çağıran `asyncio.timeout()` ile sarmalı, ya da kuralın muaf tutulması istenmeli. Çözülmeden `ruff check .` yeşile dönmez. Detay: `docs/REVIEW.md`. → **BE-5 ile çözüldü** (tercih 1: `timeout` parametresi kaldırıldı, `get_health` içinde closure ile sarıldı).
- **SEC-1-B2** · `orta` · **backend** — `api/config.py:47` mypy `unused-ignore`: `# type: ignore[call-arg]` gereksiz, `pydantic.mypy` eklentisi zaten biliyor. Yorumun silinmesi yeterli. Çözülmeden `mypy` yeşile dönmez. Detay: `docs/REVIEW.md`. → **BE-5 ile çözüldü** (yorum silindi).

- **BE-2-B1** · `düşük` · **güvenlik & test** — `ruff.toml:15` `extend-exclude` içindeki `migrations/versions` yolu Alembic çıktısını dışlamak için yazılmış ("Alembic üretir, elle yazılmaz") ama migration dizini backend sahipliğindeki `api/migrations/versions`'ta duruyor; bu yol eşleşmiyor, dolayısıyla autogenerate dosyaları lint'leniyor. Bu turdaki migration elle `ruff --fix`+format ile temizlendi ve `ruff check .` yeşil, ama **gelecekte üretilecek her migration** aynı gürültüyü doğurabilir. Kalıcı çözüm: exclude'u `api/migrations/versions` yap (dosya senin, ben dokunmadım). mypy tarafında sorun yok — `api/migrations/**` strict mypy'den temiz geçiyor, exclude gerekmez. → **SEC-3 ile çözüldü** (exclude `api/migrations/versions` yapıldı; dummy sonda dosyayla `versions/` atlandığı, `env.py`'ye geçici hata enjekte edilerek lint kapsamında kaldığı ölçüldü, ikisi de doğru).

- **UP042** · `düşük` · **bilgi, güvenlik & test'e** — Yerel ruff **0.15.22** `api/schemas.py:12`'de `ComponentStatus(str, Enum)` için `UP042` üretiyor (öneri: `enum.StrEnum`). CI'nın sabit ruff'unda (**0.12.0**) bu kural tetiklenmiyor, bu yüzden kapı yeşil ve BE-5 kapsamına girmedi (BE-5 yalnızca health.py + config.py). Düzeltme doğru ve zararsız (`StrEnum`, py312) ama `schemas.py` sahibi backend; ruff sürümü yükseltildiğinde tek satırlık değişiklikle kapatılır. Ruff pin'ini yükseltme kararı `ruff.toml`/CI sahibinin. → **SEC-3 ile ertelendi** (karar: pin 0.12.0'da sabit; UP042 `ignore`'a **eklenmedi** — susturulmadı, pin çıkınca gerçekten düzeltilecek. `docs/REVIEW.md` SEC-3'te belgelendi).
- **FE-3-B1** · `düşük` · **backend, gelecek faz** — Kohort rayı (imza öğesi) "aynı kategorideki taranmış tüm hesapların skorları"nı ister; sözleşmede kategori-dağılım ucu yok. Panel şimdilik filtresiz `/businesses?limit=200` çekip kategori bazlı türetiyor. **Sınır:** taranmış hesap sayısı 200'ü aşınca kohort eksik kalır (Faz 1 sahte verisinde 8 kayıt, sorun yok). Ölçek büyüdüğünde hafif bir uç yardımcı olur: kategori→skor-dağılımı (ya da yalnız medyan + çeyrekler). Zorunlu değil, Faz 2+ tarama hacmi netleşince değerlendirilir. FE kendi tarafında çözdü, engel değil — kayıt için.
- **SEC-1-B3** · `orta` · **güvenlik & test** — `.gitignore:1-5` içinde `.env.local` ve `.env.*.local` yok. `web/` Next.js projesi ve Next bu dosyayı standart kullanıyor; frontend yerel anahtar koyduğunda dosya izlenmeye açık. `.gitignore` sahipliği "Araç konfigürasyonu sahipliği" tablosunda tanımsız — orkestra şefi sahip atamalı. → **SEC-2 ile çözüldü** (`.env.local`+`.env.*.local`+`*.pem`/`*.key`/coverage/Playwright/`.DS_Store` eklendi; `tests/test_gitignore.py` regresyon testi, silme→kırmızı ile doğrulandı).

## Biten

_(tek satır sonuç notuyla)_

- **SEC-8** · Skorlama fixture'ı 20→100 hesap; SEC-6'nın ilk 20'si aynen korundu, 80 yeni deterministik eklendi. Kategori dağılımı 12 kategori (9× ≥5 kohort medyanı; florist/gift_shop/pet_store <5 → **kohort<5 watch** yolu). **83 handle / 17 NULL** (4 tuzak korundu). Skor sinyalleri arketiplerle çeşitli (SPEC §4): aktiflik dead(0 gönderi→rejected)/active/moderate/dormant, potansiyel bad(reels yok+düşük etkileşim+CTA yok→yüksek)/good/avg, kapasite kategori+takipçi+rating. **Referans zaman sözleşmesi: `REFERENCE_NOW=2026-07-15`** (tüm tarihler sabit ISO, göreli "bugün" yok) — BE-11 90 gün penceresini buna göre kurar, README'de. Skor-bandı hedefleri README'de (≈18 rejected/8 qualified/57 watch/17 skorlanmaz; yaklaşık, kesin skor BE-11'den). Apify yasak alanları (12 profil) korundu. **Sayı-tabanlı testler `tests/_fixture_facts.py`'den türetilir** (magic number yok; fixture büyüyünce uyar); handle sözleşme testi production'ı bağımsız referans regex'le 100 işletmede karşılaştırır. Yeni test dosyaları: `_fixture_facts.py`, `test_discovery_fixture.py` (100'e güncellendi). ruff+mypy(49 dosya)+pytest(94) yeşil, BD/places yasak-metrik taraması boş, gerçek anahtar yok. **BE-11: fixture 100 hesap, referans zaman README'de, skorlamayı 100 ile doğrulayabilir.** Detay: `docs/REVIEW.md` SEC-8.
- **BE-10** · Worker fixture modu (FE-4-B2 çözüldü). `RADAR_FIXTURE_MODE` ayar bayrağı (pydantic-settings, üretimde `false`): açıkken worker keşif job'u adaptörlere `tests/fixtures/`-besleyen MockTransport client enjekte eder (kural 6, anahtar gerekmez), kapalıyken gerçek client (üretim yolu). Mock-client mantığı tek kaynağa çıkarıldı (`api/fixture_mode.py`); `discover_demo` de oradan kullanıyor (kopya yok). Worker **atlanmıyor** — `discover_demo`'dan farkı bu: gerçek arq job + durum makinesi çalışıyor. Doğrulama (yerel pg16+redis, **anahtar unset**): gerçek `WorkerSettings` burst + `POST /discovery/run` → job_id anında (0.007s); `GET /jobs/{id}` worker öncesi `queued`, sonrası `done`, sonuç `{businesses:20, snapshots:14}`, progress `14/14` (running fazı ilerleme yazdı). Bayrak kapalı + anahtar yok → `PlacesAdapter` beklenen `RuntimeError` (üretim yolu sağlam). Demo refactor sonrası hâlâ çalışıyor (cache kanıtı korunuyor). ruff 0.12.0+mypy 2.3.0+pytest 93/93 yeşil, `.env.example`'da bayrak `false`, grep boş, sızıntı yok. **FE-5 canlı done'u bununla doğrulayabilir** (BE-12 DB bağından sonra tam tazeleme).

- **SEC-5** · Faz 2 backend'i (BE-7/BE-8/BE-9) bağımsız doğrulandı — 33 yeni test (93 toplam). **Blok 1** adaptör→normalize: Places→20 + None yolu, BD/Apify alan dönüşümleri (`comments_count→comment_count`, `videoViewCount→view_count`, `type→media_type`). **Blok 2** handle sözleşmesi: 14 handle/6 NULL, 4 tuzak NULL, **ad-tahmini regresyon testi** (facebook+ad-metni → NULL; çıkarım ad-tahminine açılırsa kırmızı). **Blok 3** fallback: `snapshots.source` fallback→apify/diğer→business_discovery; HTTP hatası **yükseliyor** (sessiz düşüş yok). **Blok 4** 7 gün cache (gerçek pg+redis): 2. koşu 0 profil çağrısı + çift snapshot yok, TTL≈7 gün, süre dolunca yeniden çekiliyor; **karşı-kanıt** cache silinince 2. koşu çağrı yapıyor (test ölçüyor). **Blok 5** gizlilik zinciri ham→normalize→persist→sütun→API 5 aşama PASS: yasak metrik yalnız `snapshots.raw` JSONB'de, tipli sütunlarda/posts'ta/`/businesses` yanıtında yok. DB testleri yalnız yerel pg/redis (kural 6 uyumlu, MockTransport), erişilemezse SKIP — CI'da servis konteyneri+env ile koşar. `.env.example` yeni anahtarlar değersiz, `api/` sır/opus yok. ruff+mypy(47 dosya)+pytest(93) yeşil, ağ muhafızı altında. Yeni bulgu yok. Detay: `docs/REVIEW.md` SEC-5.
- **BE-9** · Keşif akışı uçtan uca canlı. **arq worker** (`api/worker.py`) + **canlı uçlar** (`api/routes/jobs.py`): `POST /discovery/run` işi enqueue edip **anında** (0.006s) `job_id` döner (senkron scraping yok), `GET /jobs/{id}` arq durumunu `JobState`'e eşler (queued→running→done/error), bilinmeyen→404, redis inikse→503. **Orkestrasyon** `api/services/discovery.py::run_discovery` (bağımlılıklar enjekte — worker gerçek adaptör, demo/verify fixture'lı sahte client; kural 6). **Handle eşleme** `api/core/handle.py` saf fonksiyon: yalnız açık `instagram.com/{handle}` URL'sinden, host tam anchoring'li regex — 20 fixture'da 14 handle + 6 NULL, dört yanlış-pozitif tuzağı (`help.instagram.com`, `instagramm…`, facebook, düz site) hepsi NULL kaldı (sözleşmenin "ad tahmini yok" maddesi makine hali). **7 gün cache** `run_discovery` içinde Redis anahtarıyla sarılı (`radar:snapshot:{handle}`, TTL `snapshot_cache_ttl_seconds`), çağıran bilmez. **Demo:** `python -m api.discover_demo` (DATABASE_URL+REDIS_URL, migration uygulanmış) — 1. koşu: 20 işletme/14 handle/14 snapshot(2 apify fallback)/29 post, dış çağrı BD=14 apify=2; **2. koşu: 14 cache-skip, 0 snapshot yazıldı, dış profil çağrısı BD=0 apify=0, çift snapshot yok** (maliyet disiplini kanıtı). **Canlı uç doğrulaması** (burst worker + fixture): POST 202 anında, GET queued→done(`{businesses:20,snapshots:14}`), 404. `openapi.yaml` BE-6'da eksiksizdi, dokunulmadı; üretilen `/openapi.json` sözleşmeyle uyumlu. arq bağımlılığı `pyproject.toml`'a (redis<6 pinlendi). ruff 0.12.0+mypy 2.3.0+pytest 60/60 yeşil, task grep boş, sızıntı yok. **FE-4 canlı doğrulama + SEC-5 başlayabilir.**

- **SEC-6** · Keşif demo fixture'ı 4→20 işletme + handle eşleme. Kategori çeşitliliği (cafe 5, hair_salon 5, jewelry 3, real_estate 3, dental 2, car_dealer 2 → kohort<5 ve ≥5 ikisi de test edilebilir). **14 handle'lı, 6 handle'sız**: handle yalnız `raw.websiteUri`'deki `instagram.com/{handle}` URL'sinden; 6 handle'sızın 4'ü **yanlış-pozitif tuzağı** (facebook ad-eşleşme, `help.instagram.com` alt alan adı, `instagramm` benzer alan adı, düz site) → hepsi handle üretmiyor (sözleşmenin "ad tahmini yok" maddesinin makine hali). İki profil fixture'ı **handle-anahtarlı** (`profiles` sözlüğü): BD 12 dolu + 2 boş `{}`, Apify 2 (fallback hedefi). **Fallback:** `sahilkahveevi`+`cadde19kafe` BD boş→Apify. **Cache (SEC-5):** `atakumdisklinigi` tekrar-çekim handle'ı README'de işaretli. 8 yeni test (60 toplam); genişletilmiş fixture'la eski kontrat testleri hâlâ yeşil, ağ kapalı geçti, ruff+mypy temiz. Fixture backend'in saf normalize fonksiyonlarıyla elle doğrulandı (api/'ye yazmadan): Places→20, BD 12 dolu/2 fallback, Apify yasak-alan normalize'de yok/raw'da korunuyor. **1 kayıt notu (SEC-6-N1, düşük):** Places alan maskesi sosyal-bağlantı çekmiyor, handle tek taşıyıcısı `websiteUri` — BE-9 buna göre taramalı, `docs/REVIEW.md`'de. **Backend: fixture 20'ye genişledi, handle→profil eşlemesi README'de, BE-9 başlayabilir.**
- **BE-7** · Google Places adaptörü + işletme upsert. `normalize_places()` saf fonksiyon (README eşlemesi), eksik alanlar `None`, normalize-dışı alanlar yalnız `raw`'da. HTTP client enjekte edilebilir (test MockTransport, canlı çağrı yok). `upsert_businesses()`: `INSERT ... ON CONFLICT (place_id) DO UPDATE`; `discovered_at`+`ig_handle` SET dışı (ilk keşif anı ve IG eşlemesi korunur). Doğrulandı (pg16): normalize 4 işletme (Sahil Kahve Evi phone/website None), MockTransport discover 4; upsert iki kez → hâlâ 4 kayıt (çift yok), rating_count güncellendi, discovered_at sabit. Anahtar `.env.example`'da değersiz. Kalıcı test SEC'te.
- **BE-8** · İki profil adaptörü + snapshot/posts persist + fallback. `normalize_business_discovery()`/`normalize_apify()` saf; **yasak metrik düşürme** birincil savunma (bilerek okunmaz), `extra="forbid"` güvenlik ağı — doğrulandı: her iki normalize yüzeyinde (raw hariç) erişim/gösterim/kaydetme/demografi YOK, yalnız `raw`'da. **Fallback adaptör DIŞINDA** (`api/services/profile.py`): BD önce, `ProfileUnavailableError`'da Apify'a düşer; ağ/HTTP hatası yükselmeye devam eder (yanlış kaynağa sessiz düşüş yok) — her adaptör tek kaynağı bilir, orkestrasyon servis kararı. `persist_profile()` içerik-temelli idempotent (son snapshot `raw`'ı aynıysa yeni satır yok) → BE-9 cache'i sardığında çift snapshot oluşmaz; Redis cache burada yazılmadı (BE-9). Doğrulandı (pg16): BD 3 post/is_professional=True, Apify video view_count=8710; fallback BD-boş→apify, BD-dolu→business_discovery; persist 2 snap/6 post, BD tekrar→idempotent, `source` doğru. Tokenlar `.env.example`'da değersiz; task grep api/'de boş. **BE-9 hazır** (worker+cache+uç birleştirme).

- **SEC-4** · Üç ham fixture + normalize kontrat testleri. `tests/fixtures/`: `places_response.json` (4 işletme, biri telefonsuz+websitesiz → None yolu), `ig_business_discovery.json` (temiz kaynak, gönderiler `like_count`+`comments_count`), `apify_profile.json` (**yasak alanlar bilerek var**: profil `impressions`/`reach`/`saves`/`profileVisits`/`followerDemographics`, gönderi `impressions`/`reach`/`saved`), `README.md` (ham→normalize eşleme). 30 yeni test (52 toplam): `extra="forbid"` yasak-alan reddi, `ge=0` reddi, `raw` serbest dict, fixture geçerliliği. **Yasak-alan testi ölçüyor** — karşı-kanıt: `extra="allow"`'a çevrilmiş alt sınıfla `impressions` sızdı, test o durumda kırmızı olurdu. Girdi biçimi `model_validate(dict)` (adaptörün izleyeceği yol). ruff+mypy+pytest yeşil, ağ muhafızı altında geçti, fixture'larda gerçek anahtar yok. **Backend: BE-7/BE-8 başlayabilir** — eşleme `tests/fixtures/README.md`'de, yasak alanları `raw`'a göm, alan adı farkları (`comments_count→comment_count`, `type→media_type`, `videoViewCount→view_count`) notta.
- **BE-6** · Adaptör soyutlaması + sözleşme. **İki protokol seçildi** (`DiscoverySource`→`NormalizedBusiness`, `ProfileSource`→`NormalizedProfile`), tek protokol değil: Places keşif yapar (place_id/kategori, follower/post yok), IG+Apify profil çeker (snapshot+posts, place_id yok). Tek şemaya zorlamak alanların yarısı daima null olan sahte-birleşik bir model doğururdu; iki protokol her normalize şemayı dürüst tutuyor ve ikisi de aynı registry desenini paylaşıyor (yeni kaynak = tek dosya + dekoratör, dağınık `if source==` yok). Normalize şemalar `extra="forbid"` — yasak metrik (kural 7) taşıma girişimi doğrulamada patlar, fazlalık `raw`'a gömülür. `openapi.yaml`: `POST /discovery/run` (→`JobAccepted`, 202) + `GET /jobs/{id}` (→`JobStatus`, `JobState` enum queued/running/done/error), hepsi adlandırılmış şema, redocly temiz. Üç iskelet adaptör `NotImplementedError` (gövdeler BE-7/BE-8). Doğrulandı: normalize modeller örnekleniyor, `extra="forbid"` yasak alanı reddediyor, registry bilinen addan örnek veriyor + bilinmeyen adda `UnknownSourceError`, mypy protokol uyumunu zorluyor (bozuk imzalı bir adaptör mypy'yi patlattı, örnekle gösterildi). ruff 0.12.0 + mypy 2.3.0 + pytest 22/22 yeşil. **openapi.yaml YAML tuzağı:** backtick ile başlayan bir `description` değeri parse'ı bozuyordu — çift tırnakla sarıldı.

- **SEC-3** · İki ruff bloğu kapatıldı. **BE-2-B1:** `ruff.toml` exclude yolu `migrations/versions` → `api/migrations/versions` (gerçek yol); ölçüldü — `versions/`'a konan kasıtlı-hatalı dummy `ruff check .`'te atlandı, `env.py`'ye enjekte edilen geçici hata raporlandı (lint kapsamında), ikisi de doğru; `env.py` bit-bit geri yüklendi, dummy silindi. **UP042:** karar gereği ertelendi — pin 0.12.0'da sabit, `ignore`'a eklenmedi (susturulmadı). `ruff check .` + `pytest` (22/22) yeşil. Detay: `docs/REVIEW.md` SEC-3.
- **BE-4** · `/stats` ve `/businesses` uçları, sahte veri, BE-3 sözleşmesine birebir + CORS. `openapi.yaml` Faz 1 için eksiksizdi, **dokunulmadı** (sözleşme commit'i gerekmedi). Yanıt modelleri `response_model=` ile bağlı; üretilen `/openapi.json` sözleşmeyle uyuşuyor (12 `required` alan, `additionalProperties:false`, `TriageStatus` enum, yasak alan yok). Query paramları gerçekten uygulanıyor (saf `select_businesses`): `status=qualified`→[1,2], `status=rejected`→[5,6], `category=kafe`→[5,7], `min_score=70`→[1,2], `min_score=60&status=watch`→[4]; `limit`/`offset` sayfalıyor, `total` filtrelenmiş gerçek toplam; `?min_score=100&status=rejected`→`items:[]` (boş durum). Geçersiz param→422. **CORS:** açık origin listesi ayrı `CorsSettings` (pydantic-settings) ile `.env`'den, varsayılan `http://localhost:3000`, `["*"]` değil; izinli origin echo ediliyor, izinsiz edilmiyor, preflight 200. **Mimari not:** CORS'u ana `Settings`'e koymak `create_app()`'i her kurulumda db/redis config'i istemeye zorluyordu ve hermetik testleri (env'siz) kırıyordu — ayrı zorunlu-alansız `CorsSettings`'e taşındı, `Settings` fail-fast'i korundu. ruff 0.12.0 + mypy 2.3.0 + pytest(22/22, env'siz de) yeşil. FE-3 canlı doğrulama yapabilir.
- **SEC-2** · SEC-1-B3 kapatıldı. Kök `.gitignore` doğru kuruldu: `.env.local`+`.env.*.local` (asıl bulgu), `*.pem`/`*.key`, pytest-cov çıktısı, Playwright (Faz 6), `.DS_Store`. `tests/test_gitignore.py` regresyon testi `git check-ignore`'a soruyor (desen taklidi değil); testin ölçtüğü kanıtlandı — `.env.local` satırı geçici silinince kırmızı, geri konunca yeşil, `.gitignore` bit-bit geri yüklendi. `.env.example` ters-yön koruması da eklendi (fazla geniş `.env` deseni şablonu yutmasın). pytest 11→22 yeşil, ruff+mypy temiz. `.gitignore` sahipliği artık güvenlik & test'te.
- **BE-2** · SPEC §3 altı tablosu (`businesses`, `snapshots`, `posts`, `triage_scores`, `audits`, `outreach`) SQLAlchemy 2.0 `Mapped[]` stiliyle; tek Alembic migration (`a8d531be140e`). **Enum kararı: CHECK constraint** (`Enum(native_enum=False)`), native PG ENUM değil — gerekçe: (1) geri alınabilirlik temiz kalır, downgrade tabloyu düşürünce CHECK onunla gider, native tipin bıraktığı yetim `DROP TYPE` sorunu yok; (2) `alembic check` varchar+CHECK'i sahte diff üretmeden round-trip ediyor; (3) DB seviyesinde domain yine de zorlanıyor ve Python'da `Mapped[TriageStatus]` tiplemesi korunuyor. `values_callable` ile değerler küçük harf saklanıyor (SPEC/openapi ile aynı) — onsuz SQLAlchemy üye adını ('DRAFT') saklayıp `server_default='draft'` CHECK'ini kırardı. Doğrulandı: upgrade→check(boş diff)→downgrade→upgrade temiz; `outreach.status` varsayılansız satırda `draft`; `audits.llm_cost_usd` (Numeric, NOT NULL) boş bırakılınca hata; geçersiz status CHECK hatası; ruff+mypy+pytest(11/11) yeşil. Not: ruff exclude yolu düzeltilmeli, bkz. `## Bloke` BE-2-B1. BE-4 hazır.
- **BE-5** · SEC-1-B1 (`ASYNC109`) ve SEC-1-B2 (`unused-ignore`) kapatıldı. `_check_*` fonksiyonları `timeout` parametresini bıraktı; `get_health` içindeki `bounded` closure zaman aşımını `asyncio.timeout()` ile sarıyor, her yoklama ayrı sarıldığı için granülerlik korundu (asılı db → 503 `db=error` ama `redis=ok`, 0.3s sınırda kesildiği elle doğrulandı). Sabit CI sürümleriyle (ruff 0.12.0, mypy 2.3.0) `ruff check .` + `ruff format --check` + `mypy` + `pytest` (11/11) hepsi yeşil.
- **BE-1** · FastAPI iskeleti, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`. `/health` postgres'e `SELECT 1` ve redis'e `PING` atıyor; sağlıklı yol 200, her iki arıza yolu 503 olarak yerel servislerle doğrulandı. `docker compose` doğrulanamadı — bkz. `## Bloke`. BE-2 hazır.
- **BE-3** · `docs/openapi.yaml` v0 yazıldı: `/health`, `/stats`, `/businesses`; 8 adlandırılmış şema, inline gövde yok, redocly lint 0 hata. FE-3 tip üretimi için hazır. Faz 1'de auth yok, `security: []` ile açıkça beyan edildi.
- **SEC-1** · `ruff.toml` + `mypy.ini` (strict) + `pytest.ini` + `.github/workflows/ci.yml` (3 paralel job, postgres 16 + redis 7 servis konteyneri). 11 test geçiyor: `/health` sağlıklı/db-arızalı/redis-arızalı/ikisi-de-arızalı yolları sahte bağımlılıklarla, artı ağ muhafızı. Kural 6 artık makine tarafından uygulanıyor — `tests/conftest.py` dış soket çağrısını düşürüyor, `tests/test_network_guard.py` bunun regresyon testi. Dört gizlilik denetim maddesi de PASS (`.env.example` temiz, `.env` izlenmemiş, gömülü sır yok, yasak metrik yok). `ruff` ve `mypy` **kırmızı** — 3 bulgu `api/` içinde, sahibine bırakıldı (SEC-1-B1/B2, bkz. `## Bloke`). SQLAlchemy mypy eklentisi bilinçli açılmadı (2.0'da kaldırıldı) — gerekçe `docs/REVIEW.md`.
- **FE-1** · Next 15.5 + React 19 + Tailwind v4 + TanStack Query iskeleti, token'lar `web/styles/tokens.css`'te tek kaynakta; `docs/DESIGN.md` yazıldı. İleri taşınan eksen: patina düz değerden 40/70 eşiklerine bağlı üç duraklı skalaya dönüştü — komşu duraklar 1.38:1 ölçüldüğü için bant ayrıca ray konumu ve çentik yüksekliğiyle kodlanıyor, rakam okunabilirlik için daima mürekkep. build + `tsc --noEmit` + lint sıfır hata, `/` 200 dönüyor. FE-2 hazır.
- **FE-2** · Panel kabuğu: üst şerit (`Stats`) + aday tablosu + filtre + sayfalama, mock veriyle. Mock `web/lib/mock-veri.ts`'te tek dosyada, alan adları `openapi.yaml` `Business`/`Stats` ile birebir; FE-3'te tek yerden sökülecek (yerel tipler `// FE-3'te üretilen tiplerle değiştirilecek` notlu). Filtre durumu URL query'de (`status`/`category`/`min_score`/`limit`/`offset`, openapi adlarıyla birebir), yenilemede korunuyor. **Bant `status`'tan, ray konumu `score`'dan** — kohort<5'te skor eşiği yanıltıcı (SPEC §4), o durumda “—” + status etiketi. Üç durum (yükleniyor/hata/boş) birinci sınıf; boş durum çıkış kriteri (`MOCK_ISLETMELER=[]` → çökmeden boş). **FE-1 hatası düzeltildi:** “Takipçi”/“Son gönderi” sütunları `Business`'ta yok (snapshots/posts), sözleşmeye uygun sütunlarla (Değerlendirme/Keşfedildi) değiştirildi. **İkinci FE-1 hatası düzeltildi:** font değişkenleri `@theme`'den `:root`'a + `next/font` `<html>`'e taşındı; öncesinde tüm sayılar sessizce sans yüze düşüyordu (mono disiplini kırıktı) — headless tarayıcıda computed-font ile doğrulandı. build + `tsc` + lint sıfır hata; filtre/sayfalama/kohort saf mantığı ve üç durum ayrı ayrı headless doğrulandı. FE-3 hazır (canlı doğrulama BE-4 bekler).
- **Bloke → FE (BE'ye):** yok. `openapi.yaml` `Business` şeması takipçi/gönderi taşımıyor; bu doğru (onlar snapshots/posts). Panelin tabloda gösterebileceği tek nicel Business sinyali `rating_count` — triyaj skoru dışında. FE bunu bir eksik olarak görmüyor, not olarak bırakıyor.
- **FE-3** · Sözleşmeden tip + canlı bağlantı. `npm run gen:api` (`openapi-typescript`) `docs/openapi.yaml`→`lib/api/schema.ts` üretiyor; alias'lar `lib/api/tipler.ts`, elle tip yok, `schema.ts` lint'ten muaf. **Mock söküldü:** `lib/mock-veri.ts` silindi, veri kaynağı olarak mock yok (`git grep mock` yalnızca iki eskimeyen yorum → onlar da güncellendi). TanStack Query hook'ları (`useStats`/`useBusinesses`/`useKohortKaynagi`); filtre/sayfalama URL durumundan isteğe birebir geçiyor; taban URL `NEXT_PUBLIC_API_URL` (varsayılan `:8000`), sabit kod yok. Üç durum artık gerçek (`isPending`/`isError`/`items:[]`). **Kohort filtreden bağımsız** ayrı filtresiz istekten besleniyor (görece konum bozulmasın); 200 üstü için hafif uç önerisi `## Bloke` FE-3-B1 (engel değil). **Canlı e2e (API+panel ayakta):** üst şerit gerçek `/stats` (7), tablo `/businesses`, filtre→yeni query isteği, `?min_score=100&status=rejected`→boş, API kapatınca hata durumu, CORS temiz — hepsi headless doğrulandı. `gen:api`+build+`tsc`+lint sıfır hata; hex ve yasak metrik grep boş. **Faz 1'in son çıkış kutusu kapandı.**
