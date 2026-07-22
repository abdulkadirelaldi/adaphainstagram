# Görev tahtası

Ajanlar arası tek senkronizasyon noktası. Her ajan görevine başlarken bu dosyayı okur,
bitirince günceller. Orkestra şefi yeni görev ekler, diğerleri kendi satırını taşır.

Görev id formatı: `BE-1`, `FE-1`, `SEC-1`. Numara asla geri kullanılmaz.

---

## Aktif faz

**Faz 1 — iskelet. ✅ TAMAMLANDI** (SPEC §8) — dört çıkış kutusu da kapandı, Faz 2 açık.

Bitiş kriteri kutusu:

- [x] Servisler ayağa kalkıyor, `GET /health` 200 dönüyor — yerel postgres@16 + redis ile
      doğrulandı (sağlıklı yol + iki arıza yolu), CI'da servis konteyneriyle tekrarlanıyor.
      **`docker compose` bu makinede doğrulanmadı**, bkz. `## Bloke` → Docker kararı.
- [x] `GET /stats` ve `GET /businesses` sahte veriyle 200 dönüyor ve `docs/openapi.yaml` ile birebir uyuşuyor
      — BE-4 ile kapandı; canlı curl'le doğrulandı, üretilen `/openapi.json` sözleşmedeki `required`/
      `additionalProperties`/enum ile uyuşuyor, yasak alan yok.
- [x] Panel üst şeridi `/stats` verisini, tablo `/businesses` boş listesini gerçek istekle çiziyor
      — FE-3 ile kapandı; API `localhost:8000`, panel `localhost:3000` ayaktayken headless doğrulandı:
      üst şerit gerçek `/stats` (Taranan 7), tablo `/businesses`, filtre değişince yeni query ile istek,
      `?min_score=100&status=rejected`→boş durum, API kapatılınca hata durumu, CORS engeli yok.
- [x] Lint+tip+test kapıları **lokal yeşil** (ruff 0.12.0, mypy 2.3.0, pytest 22/22) ve
      `.github/workflows/ci.yml` yazıldı+doğrulandı (3 paralel job, postgres 16 + redis 7
      servis konteyneri). **GitHub Actions koşusu bu makinede yapılmadı** — repoda remote yok;
      gerçek Actions doğrulaması remote bağlanınca ilk push'ta olur. Docker kutusuyla aynı
      dürüst daraltma, bkz. `## Bloke` → CI kararı.

## Açık

### Faz 2 — veri (SPEC §8). Bitiş kriteri kutusu:

- [x] `SourceAdapter` protokolü + tek normalize çıktı şeması var; üç adaptör bu protokolü
      uyguluyor, yeni kaynak eklemek tek dosya (SPEC §2)
      — BE-6 ile kapandı. İki protokol seçildi (`DiscoverySource`/`ProfileSource`); üç iskelet
      adaptör uyumu mypy'de kanıtlandı, kayıt (registry) tek-dosya desenini koruyor. Gerçek
      HTTP gövdeleri BE-7/BE-8.
- [x] `POST /discovery/run` ve `GET /jobs/{id}` `openapi.yaml`'da tanımlı; iş kuyruğa gidiyor,
      uç anında `job_id` dönüyor (senkron scraping yok, SPEC §7)
      — **sözleşme** BE-6 ile kapandı (iki uç + adlandırılmış şemalar, redocly temiz). Kuyruk
      yürütücüsü (arq, gerçek `job_id` üretimi) **BE-9**'da; uç henüz FastAPI'de canlı değil.
- [ ] Places keşfi işletme kaydı yazıyor; IG/Apify snapshot + posts yazıyor; aynı hesap 7 gün
      içinde tekrar kazınmıyor (Redis cache, `CLAUDE.md` maliyet disiplini)
- [ ] **Tek komutla 20 işletme keşfedilip snapshot'ı alınıyor** — hepsi fixture'la, canlı
      IG/Apify çağrısı yok (`CLAUDE.md` kural 6)

| id | ajan | görev | bağımlı |
|---|---|---|---|
| BE-7 | backend | Google Places adaptörü + işletme kaydı yazımı, SEC-4 fixture'ıyla doğrulanır | BE-6 ✅, SEC-4 ✅ |
| BE-8 | backend | IG Business Discovery + Apify adaptörleri, snapshot + posts yazımı | BE-6 ✅, SEC-4 ✅ |
| BE-9 | backend | arq worker + 7 günlük Redis cache + `POST /discovery/run` job, tek komutla 20 işletme | BE-7, BE-8 |
| SEC-5 | güvenlik | Adaptör entegrasyon testleri + 7 gün cache denetimi + gizlilik denetimi | BE-9 |
| FE-4 | frontend | Keşif tetikleme + `/jobs/{id}` yoklama UI'ı; tablo artık gerçek DB verisini gösteriyor | BE-6 ✅ (sözleşme), canlı: BE-9 |

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

## Bloke

_(başka ajanın dizininde sorun gördüğünde buraya yaz, kendin düzeltme)_

### Karara bağlananlar (orkestra şefi, dalga 1 sonu)

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
