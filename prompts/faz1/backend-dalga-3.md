# [BACKEND] Faz 1 · Dalga 3 — BE-4

Sen Radar projesinin **backend** ajanısın. `CLAUDE.md`'yi oku. Sadece `api/**`,
`docs/openapi.yaml` ve backend'in kök dosyaları (`pyproject.toml`, `.env.example`) altına
yazarsın.

## GÖREV BE-4 — `/stats` ve `/businesses` uçları

**Amaç:** BE-3 sözleşmesindeki iki uca sahte veri döndüren gerçek FastAPI handler'ları yazmak.
Bu görev Faz 1'in son iki çıkış kutusundan birini kapatıyor.

**Oku:** `docs/openapi.yaml` (BE-3 sözleşmesi — `Stats`, `Business`, liste yanıtı ve query
parametreleri burada tanımlı, birebir uyacaksın), `docs/SPEC.md` §7. Ayrıca `docs/TASKS.md`
`## Biten` → FE-2 satırı: frontend'in hangi alan adlarını ve query parametrelerini beklediğini
oradan gör.

**Dokunabileceğin dosyalar:** `api/**`, `docs/openapi.yaml` (yalnızca sözleşmede eksik/yanlış
bulursan), `.env.example`

**Yapılacaklar:**
- `GET /stats` → `Stats` şeması: `scanned`, `qualified`, `reports`, `monthly_cost_usd`.
  Sahte ama tutarlı sabit değerler.
- `GET /businesses` → `{items: Business[], total: int}`. Sahte bir aday listesi döndür.
  Her `Business` `openapi.yaml`'daki şemayla birebir — fazladan/eksik alan yok, `score` ve
  `status` dahil.
- **Query parametreleri gerçekten uygulanmalı** (sahte veri üstünde bile): `status`,
  `category`, `min_score` filtreler; `limit`/`offset` sayfalar; `total` filtrelenmiş toplam.
  Boş sonuç mümkün olmalı — panelin boş-durum çıkış kriteri buna bağlı
  (`?min_score=100&status=rejected` gibi bir sorgu `items: []` döndürebilmeli).
- **Veri henüz DB'den gelmiyor.** Sabit sahte veri kabul (Faz 1). Ama handler imzaları ve
  Pydantic yanıt modelleri gerçek olsun ki Faz 3'te DB'ye bağlarken yüzey değişmesin.
  Yasak metrik alanı (`impressions`/`reach`/`saves`/`profile_views`/demografi) hiçbir yanıtta
  yok (`CLAUDE.md` kural 7).
- **CORS:** frontend `http://localhost:3000`'den bu API'ye istek atacak (FE-3). `CORSMiddleware`
  ekle, izin verilen origin'leri `.env`'den oku (`pydantic-settings`), varsayılan
  `http://localhost:3000`. `.env.example`'a yeni anahtarı **değersiz** ekle. `allow_origins=["*"]`
  **kullanma** — açık liste.
- Yanıt modelleri FastAPI `response_model=` ile bağlansın; `/docs` şeması `openapi.yaml` ile
  çelişmemeli.

**Sözleşme kuralı:** `openapi.yaml`'da bir eksik/hata görürsen **önce onu düzeltip ayrı bir
`be:` commit'iyle** commit'le, sonra kodu yaz (`CLAUDE.md` kural 3 — sözleşme önce). Frontend
tipini o dosyadan üretiyor; sessizce koddan sapma.

**Kabul kriterleri:**
- `curl -s localhost:8000/stats` → 200, dört alanın hepsi dolu, `Stats` şemasına uyuyor.
- `curl -s "localhost:8000/businesses?limit=2"` → 200, en fazla 2 `items`, `total` gerçek
  toplam.
- `curl -s "localhost:8000/businesses?min_score=100&status=rejected"` → 200 ve `items: []`
  (boş durum kanıtı).
- `status`/`category`/`min_score` filtreleri sonucu gerçekten daraltıyor (elle en az birer
  örnekle doğrula, kapanış notuna yaz).
- Frontend origin'inden preflight/`GET` CORS başlıklarıyla geçiyor; `curl -si -H "Origin:
  http://localhost:3000" localhost:8000/businesses` yanıtında `access-control-allow-origin`
  var ve `*` değil.
- `ruff check .` + `ruff format --check` + `mypy api/` + `pytest` hepsi yeşil (CI pin'leriyle:
  ruff 0.12.0, mypy 2.3.0).
- `git grep -nE "impressions|reach|saves|profile_views|demographics" -- api/` boş.

**Kapanış:** `docs/TASKS.md`'de BE-4'ü `## Biten` altına taşı; `openapi.yaml`'a dokunduysan
sözleşme commit'ini önce attığını not et. `git add api/ docs/openapi.yaml .env.example
docs/TASKS.md`, `be:` prefix'iyle commit'le. Sonra orkestra şefine "BE-4 ayakta, FE-3 canlı
doğrulama yapabilir" de.
