# [GÜVENLİK & TEST] Faz 1 · SEC-1 — kalite kapısı

**BEKLET: BE-1 bitene kadar gönderme.** `docs/TASKS.md` içinde BE-1 `## Biten` altına
taşınmış olmalı — `api/` dizini ve `pyproject.toml` var olmadan bu görev çalışmaz.

---

Sen Radar projesinin **güvenlik & test** ajanısın. `CLAUDE.md`'yi oku ve dosya sahipliği
kurallarına harfiyen uy: sadece `tests/**`, `.github/**`, `docs/REVIEW.md` ve lint konfig
dosyaların altına yazarsın. `api/**` veya `web/**` içinde **hiçbir düzeltme yapmazsın** —
bulduğunu `docs/TASKS.md` içindeki `## Bloke` başlığına yazıp sahibine bırakırsın.

## GÖREV SEC-1

**Amaç:** Lint, tip kontrolü, test altyapısı ve CI'ı kurmak; ilk gizlilik denetimini yapmak.

**Oku:** `CLAUDE.md` "Değişmez kurallar" (özellikle 4, 6, 7) ve `docs/TASKS.md` "Araç
konfigürasyonu sahipliği".

**Dokunabileceğin dosyalar:**
- `ruff.toml`, `mypy.ini`, `pytest.ini` (repo kökünde — bunlar senin)
- `tests/**`, `.github/**`, `docs/REVIEW.md`

**ÖNEMLİ — dosya çakışması:** `pyproject.toml` backend'in. İçine `[tool.ruff]`, `[tool.mypy]`
veya `[tool.pytest.ini_options]` **ekleme**, orada böyle bir bölüm görürsen `## Bloke`'ya yaz.
Ayarlarını kendi dosyalarında tut.

**Yapılacaklar:**
- `ruff.toml`: lint + format, `api/` hedefli, satır uzunluğu ve kural seti açıkça belirtilmiş.
- `mypy.ini`: `api/` için strict mod; Pydantic v2 ve SQLAlchemy 2.0 eklentileri açık.
- `pytest.ini`: `pytest-asyncio` `asyncio_mode = auto`, test yolu `tests/`.
- `tests/conftest.py` ve `tests/fixtures/` dizini (şimdilik boş bir `.gitkeep` yeterli).
- `tests/test_health.py`: `/health` ucunu FastAPI `TestClient`/`httpx.ASGITransport` ile test
  eder. **Canlı postgres/redis'e bağlanmaz** — bağımlılıklar mock'lanır (`CLAUDE.md` kural 6).
- `.github/workflows/ci.yml`: push ve PR'da ruff, mypy, pytest çalışır. Job'lar paralel.

**Denetim — bulguları `docs/REVIEW.md`'ye yaz, düzeltme:**
1. `.env.example` içinde gerçek değer var mı? Sadece anahtar adları olmalı.
2. `.env` `.gitignore`'da mı ve git geçmişinde izlenmiş mi?
   `git log --all --full-history -- .env` boş olmalı.
3. `api/` içinde sabit kodlanmış sır var mı?
4. Kod veya şemalarda `impressions`, `reach`, `saves`, `profile_views`, `demographics`,
   `follower_age`, `gender` geçen alan var mı? (`CLAUDE.md` kural 7 — bu metrikler sistemde
   yok.) Bulursan kritik bulgu olarak yaz.

**Kabul kriterleri:**
- `ruff check .` sıfır hata.
- `mypy api/` sıfır hata.
- `pytest` yeşil, en az 1 test geçiyor.
- Ağ kapalıyken `pytest` yine yeşil (hiçbir test dış çağrı yapmıyor — kural 6'nın kanıtı).
- CI workflow'u GitHub Actions üzerinde üç adımı da çalıştırıyor ve yeşil.
- `docs/REVIEW.md` dört denetim maddesinin her biri için `PASS`/`FAIL` + kanıt satırı içeriyor.

**Kapanış:** `docs/TASKS.md`'de SEC-1'i `## Biten` altına taşı; `FAIL` çıkan madde varsa
`## Bloke` altına sahibiyle birlikte yaz. `git add tests/ .github/ ruff.toml mypy.ini
pytest.ini docs/REVIEW.md docs/TASKS.md` ile stage et (`git add -A` yasak), `sec:` prefix'iyle
commit'le.
