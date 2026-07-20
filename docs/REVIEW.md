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

#### SEC-1-B3 · `orta` · sahibi: **belirsiz — orkestra şefi ataması gerekiyor**

`.gitignore:1-5` — `.env` var ama `.env.local` ve `.env.*.local` yok.

`web/` Next.js projesi ve Next `.env.local` dosyasını standart olarak kullanır. Frontend
ajanı yerel bir anahtar koyduğunda dosya **izlenmeye açık** olur ve commit'lenebilir.
Sır sızıntısının en olası yolu şu an burası.

Ayrıca Faz 6'da Playwright gelince `test-results/` ve `playwright-report/` de eklenmeli.

`.gitignore` sahipliği `docs/TASKS.md` "Araç konfigürasyonu sahipliği" tablosunda tanımsız.
Bu ajan dosyayı düzeltmedi; sahibi atanmalı.

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

### Açık kalan

Bu görevin çıktısı **commit edilmedi.** Sebep: BE-1 (`api/`, `pyproject.toml`,
`docker-compose.yml`) çalışma ağacında duruyor ama henüz commit'lenmemiş. Testler ve
mypy konfigürasyonu `api/` dizinine bağlı; BE-1'den önce commit'lenirse CI ana dalda
`api/` bulunamadığı için kırmızı doğar.

Sıra: **BE-1 commit'lenir → SEC-1 commit'lenir.**
