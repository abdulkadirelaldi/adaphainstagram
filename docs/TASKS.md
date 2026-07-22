# Görev tahtası

Ajanlar arası tek senkronizasyon noktası. Her ajan görevine başlarken bu dosyayı okur,
bitirince günceller. Orkestra şefi yeni görev ekler, diğerleri kendi satırını taşır.

Görev id formatı: `BE-1`, `FE-1`, `SEC-1`. Numara asla geri kullanılmaz.

---

## Aktif faz

**Faz 1 — iskelet.** (SPEC §8)

Bitiş kriteri kutusu — üçü de işaretlenmeden Faz 2 açılmaz:

- [x] Servisler ayağa kalkıyor, `GET /health` 200 dönüyor — yerel postgres@16 + redis ile
      doğrulandı (sağlıklı yol + iki arıza yolu), CI'da servis konteyneriyle tekrarlanıyor.
      **`docker compose` bu makinede doğrulanmadı**, bkz. `## Bloke` → Docker kararı.
- [ ] `GET /stats` ve `GET /businesses` sahte veriyle 200 dönüyor ve `docs/openapi.yaml` ile birebir uyuşuyor
- [ ] Panel üst şeridi `/stats` verisini, tablo `/businesses` boş listesini gerçek istekle çiziyor
- [ ] CI yeşil: ruff, mypy, pytest

## Açık

| id | ajan | görev | bağımlı |
|---|---|---|---|
| BE-4 | backend | `/stats` ve `/businesses` uçları, sahte veri, BE-3 sözleşmesine birebir uyumlu | BE-2, BE-3 |
| FE-3 | frontend | `docs/openapi.yaml`'dan tip üretimi, TanStack Query bağlantısı | başlar: BE-3 + FE-2 · canlı doğrulama: BE-4 |
| SEC-2 | güvenlik | `.gitignore` sahiplendi: `.env.local` + `.env.*.local` eklensin (SEC-1-B3) | — |

### Sıralama notu

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

- **BE-2-B1** · `düşük` · **güvenlik & test** — `ruff.toml:15` `extend-exclude` içindeki `migrations/versions` yolu Alembic çıktısını dışlamak için yazılmış ("Alembic üretir, elle yazılmaz") ama migration dizini backend sahipliğindeki `api/migrations/versions`'ta duruyor; bu yol eşleşmiyor, dolayısıyla autogenerate dosyaları lint'leniyor. Bu turdaki migration elle `ruff --fix`+format ile temizlendi ve `ruff check .` yeşil, ama **gelecekte üretilecek her migration** aynı gürültüyü doğurabilir. Kalıcı çözüm: exclude'u `api/migrations/versions` yap (dosya senin, ben dokunmadım). mypy tarafında sorun yok — `api/migrations/**` strict mypy'den temiz geçiyor, exclude gerekmez.

- **UP042** · `düşük` · **bilgi, güvenlik & test'e** — Yerel ruff **0.15.22** `api/schemas.py:12`'de `ComponentStatus(str, Enum)` için `UP042` üretiyor (öneri: `enum.StrEnum`). CI'nın sabit ruff'unda (**0.12.0**) bu kural tetiklenmiyor, bu yüzden kapı yeşil ve BE-5 kapsamına girmedi (BE-5 yalnızca health.py + config.py). Düzeltme doğru ve zararsız (`StrEnum`, py312) ama `schemas.py` sahibi backend; ruff sürümü yükseltildiğinde tek satırlık değişiklikle kapatılır. Ruff pin'ini yükseltme kararı `ruff.toml`/CI sahibinin.
- **SEC-1-B3** · `orta` · **sahibi atanmalı** — `.gitignore:1-5` içinde `.env.local` ve `.env.*.local` yok. `web/` Next.js projesi ve Next bu dosyayı standart kullanıyor; frontend yerel anahtar koyduğunda dosya izlenmeye açık. `.gitignore` sahipliği "Araç konfigürasyonu sahipliği" tablosunda tanımsız — orkestra şefi sahip atamalı.

## Biten

_(tek satır sonuç notuyla)_

- **BE-2** · SPEC §3 altı tablosu (`businesses`, `snapshots`, `posts`, `triage_scores`, `audits`, `outreach`) SQLAlchemy 2.0 `Mapped[]` stiliyle; tek Alembic migration (`a8d531be140e`). **Enum kararı: CHECK constraint** (`Enum(native_enum=False)`), native PG ENUM değil — gerekçe: (1) geri alınabilirlik temiz kalır, downgrade tabloyu düşürünce CHECK onunla gider, native tipin bıraktığı yetim `DROP TYPE` sorunu yok; (2) `alembic check` varchar+CHECK'i sahte diff üretmeden round-trip ediyor; (3) DB seviyesinde domain yine de zorlanıyor ve Python'da `Mapped[TriageStatus]` tiplemesi korunuyor. `values_callable` ile değerler küçük harf saklanıyor (SPEC/openapi ile aynı) — onsuz SQLAlchemy üye adını ('DRAFT') saklayıp `server_default='draft'` CHECK'ini kırardı. Doğrulandı: upgrade→check(boş diff)→downgrade→upgrade temiz; `outreach.status` varsayılansız satırda `draft`; `audits.llm_cost_usd` (Numeric, NOT NULL) boş bırakılınca hata; geçersiz status CHECK hatası; ruff+mypy+pytest(11/11) yeşil. Not: ruff exclude yolu düzeltilmeli, bkz. `## Bloke` BE-2-B1. BE-4 hazır.
- **BE-5** · SEC-1-B1 (`ASYNC109`) ve SEC-1-B2 (`unused-ignore`) kapatıldı. `_check_*` fonksiyonları `timeout` parametresini bıraktı; `get_health` içindeki `bounded` closure zaman aşımını `asyncio.timeout()` ile sarıyor, her yoklama ayrı sarıldığı için granülerlik korundu (asılı db → 503 `db=error` ama `redis=ok`, 0.3s sınırda kesildiği elle doğrulandı). Sabit CI sürümleriyle (ruff 0.12.0, mypy 2.3.0) `ruff check .` + `ruff format --check` + `mypy` + `pytest` (11/11) hepsi yeşil.
- **BE-1** · FastAPI iskeleti, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`. `/health` postgres'e `SELECT 1` ve redis'e `PING` atıyor; sağlıklı yol 200, her iki arıza yolu 503 olarak yerel servislerle doğrulandı. `docker compose` doğrulanamadı — bkz. `## Bloke`. BE-2 hazır.
- **BE-3** · `docs/openapi.yaml` v0 yazıldı: `/health`, `/stats`, `/businesses`; 8 adlandırılmış şema, inline gövde yok, redocly lint 0 hata. FE-3 tip üretimi için hazır. Faz 1'de auth yok, `security: []` ile açıkça beyan edildi.
- **SEC-1** · `ruff.toml` + `mypy.ini` (strict) + `pytest.ini` + `.github/workflows/ci.yml` (3 paralel job, postgres 16 + redis 7 servis konteyneri). 11 test geçiyor: `/health` sağlıklı/db-arızalı/redis-arızalı/ikisi-de-arızalı yolları sahte bağımlılıklarla, artı ağ muhafızı. Kural 6 artık makine tarafından uygulanıyor — `tests/conftest.py` dış soket çağrısını düşürüyor, `tests/test_network_guard.py` bunun regresyon testi. Dört gizlilik denetim maddesi de PASS (`.env.example` temiz, `.env` izlenmemiş, gömülü sır yok, yasak metrik yok). `ruff` ve `mypy` **kırmızı** — 3 bulgu `api/` içinde, sahibine bırakıldı (SEC-1-B1/B2, bkz. `## Bloke`). SQLAlchemy mypy eklentisi bilinçli açılmadı (2.0'da kaldırıldı) — gerekçe `docs/REVIEW.md`.
- **FE-1** · Next 15.5 + React 19 + Tailwind v4 + TanStack Query iskeleti, token'lar `web/styles/tokens.css`'te tek kaynakta; `docs/DESIGN.md` yazıldı. İleri taşınan eksen: patina düz değerden 40/70 eşiklerine bağlı üç duraklı skalaya dönüştü — komşu duraklar 1.38:1 ölçüldüğü için bant ayrıca ray konumu ve çentik yüksekliğiyle kodlanıyor, rakam okunabilirlik için daima mürekkep. build + `tsc --noEmit` + lint sıfır hata, `/` 200 dönüyor. FE-2 hazır.
- **FE-2** · Panel kabuğu: üst şerit (`Stats`) + aday tablosu + filtre + sayfalama, mock veriyle. Mock `web/lib/mock-veri.ts`'te tek dosyada, alan adları `openapi.yaml` `Business`/`Stats` ile birebir; FE-3'te tek yerden sökülecek (yerel tipler `// FE-3'te üretilen tiplerle değiştirilecek` notlu). Filtre durumu URL query'de (`status`/`category`/`min_score`/`limit`/`offset`, openapi adlarıyla birebir), yenilemede korunuyor. **Bant `status`'tan, ray konumu `score`'dan** — kohort<5'te skor eşiği yanıltıcı (SPEC §4), o durumda “—” + status etiketi. Üç durum (yükleniyor/hata/boş) birinci sınıf; boş durum çıkış kriteri (`MOCK_ISLETMELER=[]` → çökmeden boş). **FE-1 hatası düzeltildi:** “Takipçi”/“Son gönderi” sütunları `Business`'ta yok (snapshots/posts), sözleşmeye uygun sütunlarla (Değerlendirme/Keşfedildi) değiştirildi. **İkinci FE-1 hatası düzeltildi:** font değişkenleri `@theme`'den `:root`'a + `next/font` `<html>`'e taşındı; öncesinde tüm sayılar sessizce sans yüze düşüyordu (mono disiplini kırıktı) — headless tarayıcıda computed-font ile doğrulandı. build + `tsc` + lint sıfır hata; filtre/sayfalama/kohort saf mantığı ve üç durum ayrı ayrı headless doğrulandı. FE-3 hazır (canlı doğrulama BE-4 bekler).
- **Bloke → FE (BE'ye):** yok. `openapi.yaml` `Business` şeması takipçi/gönderi taşımıyor; bu doğru (onlar snapshots/posts). Panelin tabloda gösterebileceği tek nicel Business sinyali `rating_count` — triyaj skoru dışında. FE bunu bir eksik olarak görmüyor, not olarak bırakıyor.
