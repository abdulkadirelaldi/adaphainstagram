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
