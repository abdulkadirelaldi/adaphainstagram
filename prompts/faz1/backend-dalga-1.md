# [BACKEND] Faz 1 · Dalga 1 — BE-3 + BE-1

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku ve dosya sahipliği kurallarına
harfiyen uy: sadece `api/**` ve `docs/openapi.yaml` altına yazarsın. `web/**`, `tests/**`,
`.github/**` dosyalarına dokunmazsın.

Bu turda **iki görev** var. Sırayla yap, her birini ayrı commit'le.

---

## GÖREV BE-3 — sözleşme (önce bu, diğer ajanları bloke ediyor)

**Amaç:** `docs/openapi.yaml` v0'ı yazmak; frontend tiplerini bu dosyadan üretecek.

**Oku:** `docs/SPEC.md` §3 (veri modeli) ve §7 (API yüzeyi).

**Dokunabileceğin dosya:** yalnızca `docs/openapi.yaml`

**Kapsam:** sadece üç uç — `GET /health`, `GET /stats`, `GET /businesses`. Faz 1'de olmayan
uçları yazma.

- `GET /stats` → `scanned`, `qualified`, `reports`, `monthly_cost_usd` (SPEC §7'deki panel
  üst şeridi).
- `GET /businesses` → sayfalanmış liste. Query parametreleri: `status`
  (`qualified|watch|rejected`), `category`, `min_score`, `limit`, `offset`. Yanıt
  `{items: Business[], total: int}`.
- `Business` şeması `businesses` tablosunun alanlarından türer, üzerine son triyaj skorunu
  taşıyan `score` ve `status` alanları eklenir.

**Kabul kriterleri:**
- `openapi: 3.1.0` ve dosya geçerli YAML.
- Şema doğrulaması geçiyor: `npx @redocly/cli lint docs/openapi.yaml` hatasız (uyarı kabul).
- Her yanıt gövdesi `components/schemas` altında adlandırılmış bir şemaya işaret ediyor;
  inline gövde yok — frontend tip üretimi buna bağlı.
- Erişim/gösterim/kaydetme/profil ziyareti/demografi alanı **hiçbir şemada geçmiyor**
  (`CLAUDE.md` kural 7). `impressions`, `reach`, `saves`, `profile_views` gibi alan adları
  dosyada aranınca bulunmamalı.
- Tüm alanlar `required` veya açıkça `nullable`; belirsiz alan bırakma.

**Kapanış:** `docs/TASKS.md`'de BE-3'ü `## Biten` altına tek satır sonuç notuyla taşı.
`git add docs/openapi.yaml docs/TASKS.md` ile stage et (`git add -A` yasak), `be:` prefix'iyle
commit'le. **Bu commit'i diğer görevden önce at** — frontend bekliyor.

---

## GÖREV BE-1 — iskelet

**Amaç:** Çalışan bir FastAPI servisi ve yerel altyapıyı ayağa kaldırmak.

**Oku:** `CLAUDE.md` "Teknoloji" bölümü, `docs/SPEC.md` §8 Faz 1.

**Dokunabileceğin dosyalar:**
- `api/**` (tamamı)
- `docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `.env.example` (repo kökünde,
  backend'in)

**Yapılacaklar:**
- Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2 bağımlılıkları
  `pyproject.toml`'da.
- `docker compose`: postgres 16 + redis + api servisi. Postgres ve redis için named volume.
- `GET /health` → `{"status": "ok", "db": "ok", "redis": "ok"}`; db ve redis'e gerçekten
  bağlanıp kontrol etsin, sabit string dönme.
- Ayarlar `pydantic-settings` ile `.env`'den okunur. `.env.example` tüm anahtarların adını
  içerir, **hiçbir gerçek değer içermez** (`CLAUDE.md` kural 4).

**ÖNEMLİ — dosya çakışması:** `pyproject.toml` içine `[tool.ruff]`, `[tool.mypy]` veya
`[tool.pytest.ini_options]` bölümü **koyma**. Bunlar güvenlik & test ajanının sahibi olduğu
ayrı dosyalarda (`ruff.toml`, `mypy.ini`, `pytest.ini`) duracak. Detay: `docs/TASKS.md`
"Araç konfigürasyonu sahipliği".

**Kabul kriterleri:**
- `docker compose up -d` sonrası üç servis de `healthy`.
- `curl -s localhost:8000/health` → HTTP 200 ve üç alanı da `"ok"`.
- Postgres veya redis durdurulduğunda `/health` 503 dönüyor ve ilgili alan `"ok"` değil.
- `git grep -nE "(sk-|AKIA|apify_api_|password.*=.*['\"][^'\"]{8,})" -- ':!*.example'`
  çıktısı boş.
- `.env` git'te izlenmiyor (`.gitignore`'da mevcut, doğrula).

**Kapanış:** `docs/TASKS.md`'de BE-1'i `## Biten` altına taşı. Sadece kendi dosyalarını stage
et, `be:` prefix'iyle commit'le. Commit sonrası dur ve orkestra şefine BE-2'nin hazır olduğunu
bildir.
