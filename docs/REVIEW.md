# Denetim defteri

Güvenlik & test ajanının bulgu kaydı. Her faz sonunda güncellenir.

Bulgu şiddeti: `kritik` (akış durur) · `yüksek` (faz kapanmadan çözülmeli) ·
`orta` (sonraki fazda çözülebilir) · `düşük` (not).

Adresi olmayan bulgu yazılmaz — her satırda dosya ve satır numarası vardır.

---

## SEC-1 · Faz 1 — kalite kapısı

**Tarih:** 2026-07-20
**Denetlenen ağaç:** BE-1 çalışma ağacı (henüz commit'lenmemiş) + BE-3 `659618e`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest 9.1.1 + pytest-asyncio 1.4.0

### Kabul kriterleri

| Kriter | Durum | Kanıt |
|---|---|---|
| `ruff check .` sıfır hata | **FAIL** | 2 hata, ikisi de `api/` içinde → bulgu SEC-1-B1 |
| `ruff format --check .` temiz | **PASS** | `12 files already formatted` |
| `mypy` sıfır hata | **FAIL** | 1 hata, `api/` içinde → bulgu SEC-1-B2 |
| `pytest` yeşil, ≥1 test | **PASS** | `11 passed` — `tests/test_health.py` (5), `tests/test_network_guard.py` (6) |
| Ağ kapalıyken pytest yeşil | **PASS** | Kanıt aşağıda, "Ağ muhafızı" |
| CI üç adımı da koşuyor | **PASS (yapısal)** | `.github/workflows/ci.yml` — 3 paralel job, YAML doğrulandı. GitHub üzerinde henüz koşmadı; commit edilmedi (bkz. "Açık kalan"). |

`ruff` ve `mypy` kriterleri FAIL — üçünün de kaynağı `api/` içinde ve **düzeltilmedi**.
`CLAUDE.md` sahiplik kuralı gereği başka ajanın kodu bu ajan tarafından değiştirilmez.

### Dört denetim maddesi

| # | Madde | Durum | Kanıt |
|---|---|---|---|
| 1 | `.env.example` içinde gerçek değer var mı | **PASS** | Tüm değerler yer tutucu (`change-me-locally`, boş `=`). Faz 2/4 anahtarları (`GOOGLE_PLACES_API_KEY`, `APIFY_TOKEN`, `ANTHROPIC_API_KEY`) yorumda ve değersiz — `.env.example:29-34`. |
| 2 | `.env` ignore'da ve geçmişte izlenmemiş | **PASS** | `git check-ignore -v .env` → `.gitignore:1`. `git ls-files .env` → eşleşme yok. `git log --all --full-history -- .env` → boş. |
| 3 | `api/` içinde sabit kodlanmış sır | **PASS** | `api/config.py` tüm ayarı `BaseSettings` ile ortamdan okuyor, gömülü değer yok. Anahtar-değer ve bilinen önek (`sk-ant-`, `AIza`, `apify_api_`, `AKIA`, `ghp_`) taraması tüm repoda boş. |
| 4 | Yasak veri alanları (kural 7) | **PASS** | `impressions`, `reach`, `saves`, `profile_views`, `demographics`, `follower_age`, `age_range`, `gender` ve TR karşılıkları için `api/`, `web/`, `tests/`, `docs/openapi.yaml` tarandı. Tek eşleşme `docs/openapi.yaml:14` — bu alanların **yokluğunu** açıkça belirten açıklama metni, sızıntı değil. |

Faz 1'de değerlendirilemeyen denetim başlıkları — kod henüz yok, bulgu değil:
maliyet kaçağı (LLM katmanı Faz 4), otomatik gönderim (`outreach` Faz 5),
180 günlük saklama (Faz 6).

### Ağ muhafızı — kural 6'nın makine tarafından uygulanması

`CLAUDE.md` kural 6 artık yorum değil, çalışan bir kontrol. `tests/conftest.py:48`
içindeki autouse oturum fixture'ı `socket.socket.connect`, `connect_ex` ve
`socket.create_connection` çağrılarını sarar; `localhost`/`127.0.0.1`/`::1` dışına
çıkan her deneme `NetworkCallBlockedError` ile testi düşürür.

`tests/test_network_guard.py` bunun regresyon testidir: muhafız kaldırılır veya bozulursa
6 test kırmızıya döner. Böylece "hiçbir test dış çağrı yapmıyor" iddiası ölçülmüş olur,
varsayılmaz.

Yerel adresler bilinçli olarak serbest — CI'daki postgres/redis servis konteynerleri
ve `httpx.ASGITransport` oradan geçer.

---

### Bulgular

#### SEC-1-B1 · `orta` · sahibi: **backend**

`api/routes/health.py:22` ve `api/routes/health.py:34` — ruff `ASYNC109`:
async fonksiyon `timeout` parametresi alıyor.

```
async def _check_db(engine: AsyncEngine, timeout: float) -> ComponentStatus:
async def _check_redis(redis: Redis, timeout: float) -> ComponentStatus:
```

Kuralın gerekçesi: zaman aşımı çağıranın iptal kapsamıyla yönetilmeli ki iç içe
zaman aşımları doğru biçimde birleşsin. Buradaki kod zaten `asyncio.timeout()`
kullanıyor, yani davranış **doğru** — bu bir hata değil, üslup uyarısı.

İki meşru çözüm var, seçim sahibinin:
1. `timeout` parametresini kaldır, çağıran `get_health` içinde `async with
   asyncio.timeout(...)` ile sar.
2. Kuralın bu projede değeri yoksa `ruff.toml` `ignore` listesine `ASYNC109` eklenmesini
   iste — bu dosya güvenlik & test ajanınındır, gerekçeyle birlikte eklenir.

Bu bulgu çözülmeden `ruff check .` yeşile dönmez.

#### SEC-1-B2 · `orta` · sahibi: **backend**

`api/config.py:47` — mypy `unused-ignore`:

```
return Settings()  # type: ignore[call-arg]  # alanlar ortamdan doldurulur
```

`mypy.ini` içinde `plugins = pydantic.mypy` açık; eklenti `BaseSettings` alanlarının
ortamdan doldurulduğunu zaten biliyor, dolayısıyla `call-arg` bastırması gereksiz.
`warn_unused_ignores = True` altında bu bir hata. Yorum satırının silinmesi yeterli.

Bu bulgu çözülmeden `mypy` yeşile dönmez.

#### SEC-1-B3 · `orta` · sahibi: **güvenlik & test** · **PASS → SEC-2 ile kapatıldı**

**Bulgu (SEC-1'de):** `.gitignore` yalnızca `.env` biliyordu; `.env.local` ve `.env.*.local`
yoktu. `web/` Next.js projesi ve Next bu dosyaları standart kullanıyor; kökte veya `api/`
içinde bir `.env.local` izlenmeye açıktı — sır sızıntısının en olası yolu.

**Sahiplik (SEC-2'de):** Orkestra şefi `.gitignore` sahipliğini güvenlik & test'e verdi
(`docs/TASKS.md` "Araç konfigürasyonu sahipliği", 5. madde).

**Çözüm (SEC-2, 2026-07-22):** Kök `.gitignore` bir kere doğru kuruldu. Eklenenler ve
gerekçeleri:
- `.env.local`, `.env.*.local` — asıl bulgu; Next.js + genel geliştirme standardı.
- `*.pem`, `*.key` — özel anahtar/sertifika sızıntısı (CLAUDE.md kural 4).
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` — kendi `.gitignore`'unu yazıyorlar,
  açık olması zararsız ve niyeti belgeler.
- `.coverage`, `.coverage.*`, `htmlcov/`, `coverage.xml` — pytest-cov çıktısı.
- `test-results/`, `playwright-report/`, `playwright/.cache/` — Playwright e2e (Faz 6).
- `.DS_Store` — macOS (geliştirme darwin üzerinde).

**Kanıt:**
- `git check-ignore -v .env .env.local .env.production.local` → üçü de eşleşiyor
  (`.gitignore:8`, `:9`, `:10`).
- `git status --porcelain -uall | grep .env` → boş; izlenmeye aday `.env*` yok.
- Regresyon testi: `tests/test_gitignore.py`, 11 parametre + `.env.example` ters-yön
  koruması. `git check-ignore`'a soruyor, desen eşleşmesini elle taklit etmiyor.
- Testin gerçekten ölçtüğü doğrulandı: `.gitignore`'dan `.env.local` satırı geçici
  silinince test **kırmızı** (`1 failed`), geri konunca **yeşil** (`11 passed`).
  `.gitignore` bit-bit aynı geri yüklendi (`diff` boş).

**Not — kapsam:** `web/.gitignore` (Next.js üretti) `web/` alt ağacında `.env*`,
`.DS_Store`, `*.pem`, coverage'ı zaten kapsıyor. Kök `.gitignore` tüm repoyu kapsadığı
için `web/` dışındaki (kök, `api/`) env dosyaları da artık korunuyor.

#### İncelenip elenen — bulgu değil

- `.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/` `.gitignore`'da yok. **Sorun değil:**
  üç araç da kendi cache dizinine `*` içeren bir `.gitignore` yazıyor, git dizinleri
  görmüyor. `git status --porcelain -uall` çıktısında yoklar.
- `pyproject.toml` içinde `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`
  bölümü **yok** (`pyproject.toml:19-22` konuyu açıkça not etmiş). Araç konfigürasyonu
  çakışması yaşanmadı, sınır korunmuş.

---

### Sapma notu — SQLAlchemy mypy eklentisi

`prompts/faz1/sec-1.md` "Pydantic v2 ve SQLAlchemy 2.0 eklentileri açık" diyor.
`mypy.ini` içinde yalnızca `pydantic.mypy` açıldı; SQLAlchemy eklentisi **bilinçli olarak
açılmadı**.

Gerekçe: `sqlalchemy.ext.mypy.plugin` SQLAlchemy 2.0'da kullanımdan kaldırıldı. 2.0
`Mapped[]` ile PEP 484 yerel tiplemesi kullanır ve eski eklenti açıldığında yanlış
pozitif üretir. Doğru kurulum eklentisiz olandır. `mypy.ini:39-43` bunu not ediyor.

### Açık kalan (SEC-1 anında)

~~Bu görevin çıktısı commit edilmedi.~~ **Güncelleme:** BE-1 (`c42d8ff`) indi, SEC-1
(`09958c4`) commit'lendi. SEC-1-B1/B2 backend tarafından BE-5 (`4d819b7`) ile kapatıldı;
`ruff`/`mypy` artık yeşil.

---

## SEC-2 · Faz 1 — `.gitignore` sahipliği

**Tarih:** 2026-07-22
**Denetlenen ağaç:** `58a0599` (FE-2) + çalışma ağacındaki `.gitignore` + `tests/`

**Sonuç:** SEC-1-B3 kapatıldı (yukarıda PASS'a çevrildi). Kök `.gitignore` bir kere
doğru kuruldu, `tests/test_gitignore.py` regresyon testi bulgunun sessizce dönmesini
engelliyor. Test suite 11 → 22 test.

Bu turda yeni gizlilik/sır bulgusu yok: `git status` içinde izlenmeye aday `.env*`
dosyası yok, `web/.gitignore` alt ağacı ayrıca kapsıyor.

---

## SEC-3 · Faz 1 — ruff konfig temizliği

**Tarih:** 2026-07-22
**Denetlenen ağaç:** `f98eb99` (FE-3) + çalışma ağacındaki `ruff.toml`
**Araç:** ruff 0.12.0 (CI ile aynı pin, yerelde de aynı)

İki ruff bloğu kapatıldı: BE-2-B1 (exclude yolu) düzeltildi, UP042 kararı belgelendi.

#### BE-2-B1 · `düşük` · sahibi: **güvenlik & test** · **PASS → SEC-3 ile kapatıldı**

**Bulgu (BE-2'de):** `ruff.toml` `extend-exclude` içindeki `migrations/versions` yolu
hiçbir şeye uymuyordu; gerçek migration dizini `api/migrations/versions`. Autogenerate
edilen her migration lint gürültüsü yapardı.

**Çözüm (SEC-3):** `ruff.toml:12-19` — exclude `api/migrations/versions` yapıldı. Yalnızca
Alembic'in ürettiği `versions/` dizini dışlanır; `env.py` ve `script.py.mako` gibi elle
yazılan altyapı bilinçli olarak lint kapsamında kalır.

**Kanıt — ikisi de ölçüldü:**
- `versions/` **atlanıyor:** `api/migrations/versions/zzz_dummy_lint_probe.py` içine kasıtlı
  E401/F401/E702 hataları olan geçici dosya kondu; `ruff check .` (CI'ın kullandığı dizin
  taraması) çıktısında **görünmedi** → dışlanıyor. Dosya sonra silindi.
- `env.py` **lint'leniyor:** `api/migrations/env.py`'ye geçici `import os,sys` eklendi;
  `ruff check .` `env.py:77` için E401/E402/I001/F401 **raporladı** → kapsamda. Dosya
  bit-bit geri yüklendi (`git diff` boş, backend'in dosyasına iz bırakılmadı).
- `ruff check .` → `All checks passed!` (mevcut `a8d531be140e` migration dahil).

**Not — ruff yol argümanı davranışı:** Bir dosya ruff'a *doğrudan argüman* olarak
verildiğinde exclude uygulanmaz (`force-exclude` kapalı olduğu için); dışlama yalnızca
dizin taramasında (`ruff check .`) etkindir. CI tam olarak `ruff check .` kullandığından
kapı doğru davranır. `force-exclude` eklenmedi — görev kapsamı dışı ve CI için gereksiz.

#### UP042 · `düşük` · **ertelendi — ruff pin 0.12.0'da sabit**

**Karar (orkestra şefi):** ruff pin **yükseltilmiyor.** CI 0.12.0'da sabit kalır; bu
sürümde `UP042` (`ComponentStatus(str, Enum)` → `enum.StrEnum` önerisi) **tetiklenmiyor**,
dolayısıyla kapı zaten yeşil. `api/schemas.py` `StrEnum` düzeltmesi ileride pin bir üst
sürüme çıkınca, tek satırlık değişiklikle yapılacak.

**Uygulama (SEC-3):** UP042 `ruff.toml` `ignore`/`extend-ignore` listesine **eklenmedi.**
Bu bilinçli: kural susturulmadı, yalnızca ertelendi — pin çıktığında gerçekten düzeltilecek
bir bulgu olarak kalmalı, kalıcı olarak bastırılmamalı. `api/schemas.py` sahibi backend.

---

## SEC-4 · Faz 2 — fixture'lar + normalize kontrat testleri

**Tarih:** 2026-07-22
**Denetlenen ağaç:** `5b7062f` (BE-6) + çalışma ağacındaki `tests/`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest — 52 test (30 yeni)

BE-7/BE-8'i bloke eden fixture'lar yazıldı ve BE-6 normalize şemalarının kontratı test
edildi. Adaptör gövdesi henüz yok; adaptör-entegrasyon testi SEC-5'te (BE-9 sonrası).

### Üretilenler

| Dosya | Ne |
|---|---|
| `tests/fixtures/places_response.json` | Google Places (New) `searchText` ham yanıtı, 4 işletme; `Sahil Kahve Evi` telefonsuz+websitesiz (None yolu), `Karadeniz Oto Galeri` websitesiz |
| `tests/fixtures/ig_business_discovery.json` | IG Graph BD ham yanıtı; 3 gönderi `like_count`+`comments_count` taşıyor; **temiz kaynak** (yasak alan yok) |
| `tests/fixtures/apify_profile.json` | Apify Scraper ham çıktısı; **yasak alanlar bilerek var** (kural 7) |
| `tests/fixtures/README.md` | Üç kaynak için ham→normalize alan eşlemesi; hangi alan `raw`'da kalıyor |
| `tests/test_normalize_contract.py` | 22 şema kontrat testi |
| `tests/test_fixtures_valid.py` | 8 fixture geçerlilik testi |

### Kabul kriterleri

| Kriter | Durum | Kanıt |
|---|---|---|
| 3 JSON + README, hepsi geçerli JSON | **PASS** | `test_fixture_gecerli_json` (parametreli) yeşil |
| `pytest` yeşil (forbid reddi, ge=0 reddi, fixture yükleme) | **PASS** | 52 passed |
| Yasak-alan testi gerçekten ölçüyor | **PASS** | Aşağıda "Karşı-kanıt" |
| Ağ kapalıyken pytest yeşil | **PASS** | `conftest.py` ağ muhafızı altında 30 yeni test geçti; dış çağrı olsa kırmızı olurdu |
| `ruff check .` + `mypy` temiz | **PASS** | `All checks passed!` / `Success: no issues found in 29 source files` |

### Yasak-alan reddi kural 7'nin makine hali — karşı-kanıt

`extra="forbid"`'in gerçekten devrede olduğu iki yönlü kanıtlandı (base.py'ye dokunmadan):
- **Gerçek durum:** `NormalizedProfile.model_validate({"source":"apify","raw":{},"impressions":15234})`
  → `ValidationError`, kod `extra_forbidden`. Yasak metrik reddedildi.
- **Karşı-kanıt:** `extra="allow"`'a çevrilmiş bir alt sınıfla aynı çağrı → `impressions=15234`
  **sızdı**. Testimiz bu durumda `ValidationError` beklediğinden **kırmızıya dönerdi**. Yani
  test bir davranışı gerçekten ölçüyor, tavsiye yazmıyor.

`test_yasak_alan_adlari_fixturede_gercekten_var` listeyi fixture'a bağlıyor: Apify fixture'ından
bir yasak alan düşerse test uyarır, kontrat hayali değil gerçek ham veriyi kovalar.

### Denetim — bu turda yeni gizlilik/sır bulgusu yok

- **Sır sızıntısı:** Fixture'larda gerçek anahtar deseni (`sk-ant-`, `AIza`, `apify_api_`,
  `AKIA`, `ghp_`) taraması **boş**. Tüm veri uydurma Samsun örneği, `example.com`/`example`
  alan adları, sahte `place_id`/IG `id`'leri.
- **Yasak veri (kural 7):** Apify fixture'ı yasak alanları **bilerek** taşıyor (görev şartı) —
  ama bunlar ham `raw` katmanında; normalize şema `extra="forbid"` ile yüzeye çıkışı reddediyor
  ve `test_raw_serbest_dict_kabul_eder` yasak metriğin `raw`'da yaşayıp normalize alanlarda
  görünmediğini doğruluyor. BD fixture'ı ise `test_ig_business_discovery_yasak_alan_icermiyor`
  ile temiz kaynak varsayımını koruyor.
- **Ağ çağrısı:** Yeni testlerin hiçbiri dış çağrı yapmıyor; `conftest.py` muhafızı devrede.

### Backend'e not

**SEC-4 fixture'lar hazır — BE-7/BE-8 başlayabilir.** Ham→normalize eşlemesi
`tests/fixtures/README.md`'de. Adaptör gövdesini yazarken:
- Ham dict'i `Normalized*.model_validate(...)` ile doğrula (kontrat testi bu yolu izliyor).
- Apify'ın yasak alanlarını (`impressions`, `reach`, `saves`, `profileVisits`,
  `followerDemographics`; gönderide `impressions`/`reach`/`saved`) normalize alana **taşıma**;
  bütün ham nesneyi `raw`'a göm. `extra="forbid"` zaten reddeder ama yükü sen düşürmelisin.
- Alan adı farklarına dikkat: BD `comments_count`→`comment_count`, Apify `type`→`media_type`,
  `videoViewCount`→`view_count`.

---

## SEC-6 · Faz 2 — keşif demo fixture'ı (20 işletme + handle eşleme)

**Tarih:** 2026-07-23
**Denetlenen ağaç:** `a291c9e` + çalışma ağacındaki `tests/`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest — 60 test (8 yeni)

Places fixture'ı 4→20 işletmeye genişledi, iki profil fixture'ı handle-anahtarlı yapıya
geçti, handle eşleme sözleşmesine (docs/TASKS.md) uygun bağlantılar yerleştirildi.

### Kabul kriterleri

| Kriter | Durum | Kanıt |
|---|---|---|
| ~20 işletme, kategori çeşitliliği, geçerli JSON | **PASS** | 20 işletme, 6 kategori (2×5 + 4×<5); `test_yirmi_isletme_var`, `test_kategori_cesitliligi_kohort_icin_yeterli` |
| Handle çıkarımı test edilebilir (açık/yok/tuzak) | **PASS** | 14 handle'lı, 6 handle'sız (3 tuzak + 1 düz + 2 alansız); `test_handle_tasiyan_ve_tasimayan_isletmeler`, `test_tuzak_linkler_handle_uretmiyor` |
| Handle→profil eşleme README'de belgeli + tutarlı | **PASS** | `profiles` sözlüğü; `test_her_handle_bir_profille_cozulebiliyor` |
| Fallback + cache işaretli handle'lar | **PASS** | fallback: `sahilkahveevi`+`cadde19kafe` (BD boş → Apify); cache: `atakumdisklinigi` README'de işaretli |
| `pytest` yeşil (genişletilmiş fixture'la) + ağ kapalı | **PASS** | 60 passed; ağ muhafızı altında geçti |
| `ruff` + `mypy` temiz | **PASS** | `All checks passed!` / `no issues in 35 source files` |

### Fixture ↔ gerçek adaptör tutarlılığı (elle, api/'ye yazmadan)

Fixture'ı teslim etmeden önce backend'in saf normalize fonksiyonlarını **import edip**
çağırarak (yalnız okuma/çalıştırma; `api/`'ye yazma yok) tutarlılığı doğruladım:
- `normalize_places(places_response)` → 20 `NormalizedBusiness`; website `None`=2, phone `None`=2.
- `normalize_business_discovery` her BD profiline → 12 dolu, 2 `ProfileUnavailableError`
  (fallback tetikleyici). Sözleşmeyle birebir.
- `normalize_apify` her Apify profiline → yasak alanlar (`impressions`/`reach`/`saves`/
  `profileVisits`/`followerDemographics` + gönderi `impressions`/`reach`/`saved`) normalize
  çıktıda **yok**, `raw`'da **korunuyor**. (Bunun resmi entegrasyon kanıtı SEC-5'te.)

### Bulgu

#### SEC-6-N1 · `düşük` · **bilgi — sahibi: backend (BE-9)**

**Handle yalnızca `websiteUri`'den türetilebiliyor.** Handle eşleme sözleşmesi "website veya
sosyal bağlantılardan" der, ama Places (New) alan maskesi (`api/adapters/places.py:_FIELD_MASK`)
ayrı bir sosyal-bağlantı alanı istemiyor — ham `place` nesnesinde URL taşıyan tek alan
`websiteUri`. Sonuç: handle'lı işletmelerin instagram URL'si `websiteUri`'de duruyor ve
fixture buna göre kuruldu. BE-9 çıkarımı `raw` içindeki instagram URL'sini (pratikte
`websiteUri`) taramalı.

Bu bir **kısıt, bulgu değil** — sözleşme yine sağlanıyor (açık URL var, ad tahmini yok).
Ama BE-9 gelecekte Places'ten sosyal bağlantı da çekmek isterse alan maskesine ekleme
gerekir; o gün fixture da genişletilir. Kayıt için.

### Denetim — yeni gizlilik/sır bulgusu yok

- **Sır:** Fixture'larda gerçek anahtar deseni taraması boş; tüm veri uydurma Samsun örneği,
  `example.com`/`example` alan adları, sahte `place_id`/handle/IG `id`.
- **Yasak veri (kural 7):** Apify fixture'ı yasak alanları **bilerek** korudu (BE-9 düşürecek,
  SEC-5 doğrulayacak); `test_apify_fallback_profilleri_yasak_alanlari_koruyor` bunu güvenceye
  aldı. BD fixture'ı **temiz**: `impressions|reach|saves|profilevisits|demographic` taraması
  boş; `test_ig_business_discovery_yasak_alan_icermiyor` bekçi.
- **Yanlış-pozitif tuzağı:** 4 tuzak link (facebook ad-eşleşme, `help.instagram.com` alt alan
  adı, `instagramm` benzer alan adı, düz site) `test_tuzak_linkler_handle_uretmiyor` ile
  handle üretmediği doğrulandı — sözleşmenin "ad benzerliğinden tahmin yok" maddesinin makine hali.
- **Ağ:** Yeni testlerin hiçbiri dış çağrı yapmıyor; muhafız devrede.

### Backend'e not

**Fixture 20 işletmeye genişledi, handle→profil eşlemesi `tests/fixtures/README.md`'de,
BE-9 başlayabilir.** Handle çıkarımı `raw.websiteUri`'deki `instagram.com/{handle}` URL'sinden
(host tam olarak `(www.)instagram.com`); 4 tuzak linki handle üretmemeli. Fallback:
`sahilkahveevi`+`cadde19kafe` BD'de `{}` → Apify. Cache (SEC-5): `atakumdisklinigi` tekrar-çekim
handle'ı, persist idempotent kalmalı.

---

## SEC-5 · Faz 2 — entegrasyon + cache + gizlilik denetimi (bağımsız doğrulama)

**Tarih:** 2026-07-23
**Denetlenen ağaç:** `3cc67f6` + çalışma ağacındaki `tests/`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest — 93 test (33 yeni), yerel pg16 + redis

BE-7/BE-8/BE-9'un iddiaları (normalize, fallback, 7 gün cache, yasak-alan düşürme)
backend'in elle doğrulamasından **bağımsız** olarak, güvenlik ajanının kendi testleriyle
makineye bağlandı. DB testleri yalnız **yerel** postgres/redis kullanır (kural 6 dış
Instagram/Apify/Places'i yasaklar, yerel altyapıyı değil); erişilemezse SKIP, CI'da servis
konteyneriyle koşar.

### Beş blok — kabul kriterleri

| Blok | Durum | Kanıt (test) |
|---|---|---|
| 1. Adaptör→normalize (alan eşlemesi) | **PASS** | `test_adapter_integration.py`: Places→20, None yolu; BD `comments_count→comment_count`, `view_count=None`; Apify `type→media_type`, `videoViewCount→view_count`, yasak düşüyor |
| 2. Handle sözleşmesi + regresyon | **PASS** | `test_handle_contract.py`: 14 handle/6 NULL, 4 tuzak NULL, ad-tahmini regresyon testi |
| 3. Fallback (BD→Apify) | **PASS** | `test_adapter_integration.py` + DB'de `snapshots.source`: fallback→apify, diğerleri business_discovery; HTTP hatası **yükseliyor**, sessiz düşüş yok |
| 4. 7 gün cache | **PASS** | `test_discovery_integration.py`: 2. koşu 0 profil çağrısı, çift snapshot yok; TTL≈7 gün; süre dolunca yeniden çekiliyor |
| 5. Gizlilik zinciri (kural 7) | **PASS** | aşağıda, 5 aşama |

### Yasak-alan gizlilik zinciri — ham → normalize → persist → sütun → API

Apify fixture'ı yasak metrik taşıyor (`impressions`/`reach`/`saves`/`profileVisits`/
`followerDemographics` + gönderi `impressions`/`reach`/`saved`). Zincirin her aşamasında
bu alanların normalize yüzeye, DB sütununa veya API yanıtına çıkmadığı, yalnız
`snapshots.raw` JSONB'de arşivlendiği doğrulandı:

| Aşama | Durum | Kanıt |
|---|---|---|
| ① ham fixture | **PASS (yasak var)** | `apify_profile.json` yasak alanları taşıyor (SEC-6, kasıtlı) |
| ② normalize | **PASS** | `test_apify_normalize_yasak_alanlari_dusuruyor`: `model_dump(exclude raw)` içinde yasak yok; `raw["impressions"]=15234` |
| ③ persist → snapshots | **PASS** | `test_yasak_metrik_yalnizca_raw_jsonda...`: `snap.raw["impressions"]=15234` (arşiv) ama tipli sütunlar (`followers`/`media_count`) yalnız SPEC §3 |
| ④ snapshots/posts sütunları | **PASS** | `test_privacy_chain.py`: `Snapshot.__table__`/`Post.__table__` sütun adlarında yasak token yok; posts yalnız `like_count`/`comment_count`/`view_count` |
| ⑤ `/businesses` yanıtı | **PASS** | `test_businesses_yaniti_yasak_anahtar_icermiyor` + `Business`/`BusinessList`/`JobResult`/`JobStatus`/`Stats` şema alanlarında yasak yok |

**Sonuç:** yasak metrikler zincirin hiçbir aşamasında yüzeye çıkmıyor; yalnız denetim izi
olarak `snapshots.raw` JSONB'de kalıyor. Kural 7 uçtan uca korunuyor.

### İki testin gerçekten ölçtüğü — karşı-kanıt

- **Cache testi:** `test_cache_devre_disi_ikinci_kosu_cagri_yapar_karsi_kanit` — cache
  anahtarları silinince (cache devre dışı gibi) ikinci koşu 14 BD + 2 Apify çağrısı yapıyor.
  Yani cache sarmalı çalışmasaydı `test_ikinci_kosu...` kırmızı olurdu. Cache testi bir
  davranışı ölçüyor, varsaymıyor.
- **Handle sözleşmesi:** `test_ad_benzerligi_tahmin_edilmiyor_regresyon` — adı 'Elmas
  Kuyumculuk', elinde yalnız `facebook.com/elmaskuyumculuk` ve metinde ad geçen bir işletme
  → NULL. Çıkarım ad-tahminine açılırsa (regex gevşetilir) bu test kırmızıya döner. "Ad
  tahmini yok" (hukuki sınır) makineye bağlı.

### `.env.example` + sır denetimi

| Kontrol | Durum | Kanıt |
|---|---|---|
| Yeni anahtarlar değersiz | **PASS** | `GOOGLE_PLACES_API_KEY=`, `IG_BUSINESS_DISCOVERY_TOKEN=`, `APIFY_TOKEN=` boş; `SNAPSHOT_CACHE_TTL_SECONDS` yorumlu; `CORS_ALLOW_ORIGINS=` boş (`.env.example:26-37`) |
| `api/` sabit kodlanmış sır | **PASS** | anahtar-değer ve bilinen önek (`sk-ant-`/`AIza`/`apify_api_`/`AKIA`/`ghp_`) taraması boş; tüm kimlikler `pydantic-settings` ile ortamdan |
| Opus çağrısı | **PASS (yok)** | `api/`'de `claude-opus`/`opus-4` yok (LLM katmanı Faz 4) |

### Ağ muhafızı — DB testleri kural 6'ya aykırı değil

DB/redis testleri yalnız `localhost:5432`/`localhost:6379`'a bağlanır; `conftest.py` ağ
muhafızı localhost'a izin verir, dış dünyaya değil. Adaptör çağrıları `httpx.MockTransport`
ile karşılanır (soket açılmaz). 93 test ağ muhafızı altında geçti. Yerelde postgres/redis
yoksa DB testleri SKIP olur — süit yeşil kalır, ama CI'da (servis konteyneri + env) ve DB'li
makinede gerçekten koşar (skip yok, kanıtlandı).

### Bu turda yeni bulgu yok

Faz 2 backend'i (BE-7/BE-8/BE-9) beş kritere göre bağımsız doğrulandı; gizlilik/maliyet/sır
ihlali bulunmadı. SEC-6-N1 (websiteUri handle taşıyıcısı) hâlâ geçerli bir kayıt, bulgu değil.

---

## SEC-8 · Faz 3 — skorlama fixture'ı (100 hesap, skor sinyalleri çeşitli)

**Tarih:** 2026-07-23
**Denetlenen ağaç:** `2da4b32` + çalışma ağacındaki `tests/`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest — 94 test, yerel pg16 + redis

Places + profil fixture'ları 20→100 hesaba çıkarıldı; SPEC §4 skor sinyalleri (aktiflik/
potansiyel/kapasite) skorlar tüm bantlara yayılacak ve kohort<5 test edilebilecek biçimde
çeşitlendirildi. **SEC-6'nın ilk 20 hesabı aynen korundu** — adaptör/cache/fallback
testlerinin dayandığı bilinen değerler değişmedi.

### Kabul kriterleri

| Kriter | Durum | Kanıt |
|---|---|---|
| ~100 işletme, geçerli JSON, kategori dağılımı README'de | **PASS** | 100 işletme, 12 kategori; `test_yuz_isletme_var` |
| En az bir kategori <5 (kohort) | **PASS** | florist(3)/gift_shop(3)/pet_store(2) <5; 9 kategori ≥5; `test_kategori_cesitliligi_kohort_icin_yeterli` |
| Profiller 100 hesabı kapsıyor, handle-anahtarlı korundu | **PASS** | 83 handle → 71 BD-dolu + 12 fallback; hepsi çözülebilir; `test_her_handle_bir_profille_cozulebiliyor` |
| Skor sinyalleri belirgin çeşitli | **PASS** | arketipler README'de: aktiflik dead/active/moderate/dormant, yönetim bad/good/avg, kapasite kategori+takipçi+rating |
| Tarihler sabit ISO, göreli "bugün" yok, referans README'de | **PASS** | `REFERENCE_NOW=2026-07-15`; `test_referans_zaman_gecmiste_sabit` tüm damgaların 2026- sabit olduğunu doğrular |
| `pytest` yeşil (genişletilmiş fixture'la), ağ kapalı | **PASS** | 94 passed; ağ muhafızı altında; DB testleri yerel pg/redis |
| `ruff` + `mypy` temiz | **PASS** | `All checks passed!` / `no issues in 49 source files` |
| Apify yasak alanları korundu | **PASS** | 12 apify profilinin hepsinde `impressions`/`reach`/`saves`/`profileVisits`/demografi var (74 örnek); `test_apify_profilleri_yasak_alanlari_koruyor` |

### Sayı-tabanlı testler magic number'dan arındırıldı

Fixture 20→100 büyüyünce SEC-5/SEC-6'nın sabit sayıları (14 handle, 2 fallback, 20 işletme)
kırılırdı. Bunları `tests/_fixture_facts.py`'den **türetilir** hale getirdim: testler
fixture'ı okuyup beklenen handle/fallback/snapshot sayısını hesaplar. Sonuç: fixture yeniden
boyutlanınca testler kendiliğinden uyar, davranış yine tam olarak doğrulanır (ör.
`handles_matched == fixture'daki handle sayısı`, `fallback_used == BD-boş & Apify-var sayısı`).

Handle sözleşme testi ise production `extract_ig_handle`'ı `_fixture_facts.ref_extract_handle`
(bağımsız referans regex) ile 100 işletmede karşılaştırır — production'ın sözleşmeye uyduğunu
kendi kopyası olmayan bir kaynaktan doğrular.

### Denetim — bu turda yeni gizlilik/sır bulgusu yok

- **Sır:** Fixture'larda gerçek anahtar deseni taraması boş; tüm veri uydurma, `example.com`.
- **Yasak veri (kural 7):** `places_response.json` ve `ig_business_discovery.json`
  `impressions|reach|saves|profilevisits|demographic` taraması **boş** (BD temiz kaynak).
  Apify fixture'ı yasak alanları **bilerek** korur — normalize düşürür (SEC-5 doğruladı).
- **Zaman:** Göreli "bugün" yok; sabit referans (2026-07-15) README'de sözleşme olarak yazıldı.

### Üretim yöntemi (izlenebilirlik)

Yeni 80 hesap deterministik (indeks tabanlı, rastgelelik yok) bir üreticiyle kuruldu; çıktı
statik JSON olarak commit'lendi (fixture = tek doğruluk kaynağı, kural 6 "sabit/tekrarlanabilir").
Arketip mekaniği ve referans zaman README'de belgelidir; bir hesabın hangi banda düşeceği
"nasıl kuruldu" sütunundan izlenebilir. Kesin skor/durum BE-11 motorundan çıkar.

### Backend'e not

**Fixture 100 hesap, skor sinyalleri çeşitli, referans zaman `REFERENCE_NOW=2026-07-15`
README'de — BE-11 skorlamayı 100 ile doğrulayabilir.** 90 gün penceresini bu sabit referansa
göre kur. Kohort<5 kategorileri: florist/gift_shop/pet_store (potansiyel hesaplanmaz → watch).
Skor-bandı hedefleri README'de (yaklaşık; kesin skor senin motorundan).

---

## SEC-7 · Faz 3 — triyaj skorlama motoru bağımsız doğrulama

**Tarih:** 2026-07-23
**Denetlenen ağaç:** `bf543a7` + çalışma ağacındaki `tests/`
**Araçlar:** ruff 0.12.0, mypy 2.3.0 (strict), pytest — 110 test (16 yeni), yerel pg16 + redis

BE-11'in skorlama iddiaları (çarpım çökme, kohort<5→watch, eşikler, mutlak-eşik yokluğu,
referans zaman, persist idempotent) backend'in elle doğrulamasından **bağımsız** olarak
16 yeni testle makineye bağlandı. `tests/test_scoring.py` (12 saf motor testi) +
`tests/test_scoring_persist.py` (4 DB testi, fixture'a bağlı).

### Kabul kriterleri — altı başlık

| Başlık | Durum | Kanıt (test) |
|---|---|---|
| Çarpım çökme (karşı-kanıtlı) | **PASS** | `test_carpim_cokme_bir_alt_skor_sifir`, `test_carpim_dusuk_aktiflik_...`, `test_olu_hesap_yuksek_kapasiteyle_bile_rejected` |
| Kohort<5 → watch | **PASS** | saf: `test_kohort_bes_altinda_potansiyel_none_watch`; DB fixture-türetilmiş: `test_kohort_bes_alti_kategoriler_watch_potansiyel_none` |
| Durum eşikleri (off-by-one) | **PASS** | `test_durum_esikleri_sinir_degerleri`: 39.99→rejected, 40.0→watch, 69.99→watch, 70.0→qualified |
| Mutlak eşik yokluğu (karşı-kanıtlı) | **PASS** | `test_mutlak_esik_yok_ayni_etkilesim_farkli_medyanda_farkli_potansiyel` |
| Referans zaman | **PASS** | `test_aktiflik_referans_zamana_bagli_deterministik`: referans +200g → aktiflik 0 |
| Persist + idempotent | **PASS** | `test_triage_persist_ve_idempotent`, `test_triage_satiri_tum_alanlari_tasiyor` |

Ek: `test_bantlar_ucune_de_yayiliyor` — SEC-8 fixture'ı skorları üç banda da yayıyor
(rejected/watch/qualified hepsi DB'de mevcut), skor sinyali çeşitliliğini uçtan uca doğrular.

### İki testin gerçekten ölçtüğü — karşı-kanıt

- **Çarpım çökme:** `combined_score(1, 95, 95) = 24.23` (<40 → rejected). Aynı değerlerin
  aritmetik ortalaması **63.67** (≥60 → watch/üstü). Formül toplama/ortalamaya çevrilseydi
  `score < 40` assert'i kırmızıya dönerdi. Test bir davranışı ölçüyor, varsaymıyor.
- **Mutlak eşik yok:** aynı ham etkileşim (0.05) kohort medyanı 0.10'da potansiyel **83.3**,
  medyan 0.02'de **66.7**. Mutlak eşik olsaydı ikisi eşit çıkardı → `p_high > p_low` assert'i
  kırmızı olurdu. Karşılaştırmanın kohort-göreli olduğu (SPEC §4) böyle kanıtlandı.

### Magic number yok — fixture/DB'den türetme

DB testleri kohort<5 kategori kümesini **DB'deki taranmış sayıdan** hesaplar (`MIN_COHORT`
sabitiyle), sabit "florist/gift/pet" listesi gömmez — fixture yeniden boyutlanınca uyar.
İdempotency "toplam satır == farklı işletme sayısı" ile doğrulanır (sabit sayı değil).

### Denetim — motor temiz, yeni bulgu yok

- **LLM/maliyet:** `api/core/scoring.py` saf ve deterministik — `anthropic`/`claude-opus`/
  `httpx` import etmiyor, `datetime.now()` çağırmıyor (referans enjekte). SPEC §8 "triyaj LLM
  kullanmaz" korunuyor. Maliyet kaçağı yok.
- **Yasak veri (kural 7):** skorlama girdisi (`PostData`/`AccountData`) yalnız SPEC §3
  alanları (like/comment/followers/category…); erişim/gösterim/kaydetme/demografi yok.
  **BE-11 kararı doğru:** potansiyel dört değil **üç** sinyalden hesaplanıyor — dördüncü
  (yorum-yanıt oranı) Faz 2'de çekilmediği için (SPEC §3'te "kim yanıtladı" yok) skora
  sokulmamış. Bu, kural 7'ye (ölçmediğini iddia etme) **uyum**dur, bulgu değil.
- **Ağ:** skorlama testleri ağ muhafızı altında geçti (16/16); DB testleri yalnız yerel
  pg/redis, erişilemezse SKIP.

### Backend'e not

Skorlama motoru altı kritere göre bağımsız doğrulandı; gizlilik/maliyet/LLM ihlali yok.
Yorum-yanıt sinyalinin Faz 4'te (Apify yorum çekimi) eklenmesi planı doğru — o gün potansiyel
dört sinyale çıkarken bu testler güncellenecek.
