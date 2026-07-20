# Görev tahtası

Ajanlar arası tek senkronizasyon noktası. Her ajan görevine başlarken bu dosyayı okur,
bitirince günceller. Orkestra şefi yeni görev ekler, diğerleri kendi satırını taşır.

Görev id formatı: `BE-1`, `FE-1`, `SEC-1`. Numara asla geri kullanılmaz.

---

## Aktif faz

**Faz 1 — iskelet.** (SPEC §8)

Bitiş kriteri kutusu — üçü de işaretlenmeden Faz 2 açılmaz:

- [ ] `docker compose up` ile postgres + redis + api ayağa kalkıyor, `GET /health` 200 dönüyor
- [ ] `GET /stats` ve `GET /businesses` sahte veriyle 200 dönüyor ve `docs/openapi.yaml` ile birebir uyuşuyor
- [ ] Panel üst şeridi `/stats` verisini, tablo `/businesses` boş listesini gerçek istekle çiziyor
- [ ] CI yeşil: ruff, mypy, pytest

## Açık

| id | ajan | görev | bağımlı |
|---|---|---|---|
| BE-1 | backend | Repo iskeleti, docker-compose (postgres 16 + redis), FastAPI app, `/health` | — |
| BE-2 | backend | SQLAlchemy modelleri ve ilk Alembic migration (SPEC §3) | BE-1 |
| BE-4 | backend | `/stats` ve `/businesses` uçları, sahte veri, BE-3 sözleşmesine birebir uyumlu | BE-2, BE-3 |
| FE-1 | frontend | Next.js iskeleti, tasarım token'ları, `docs/DESIGN.md` yazımı | — |
| FE-2 | frontend | Panel kabuğu: üst şerit + aday tablosu + filtre, mock veriyle | FE-1 |
| FE-3 | frontend | `docs/openapi.yaml`'dan tip üretimi, TanStack Query bağlantısı | başlar: BE-3 + FE-2 · canlı doğrulama: BE-4 |
| SEC-1 | güvenlik | ruff + mypy + pytest kurulumu, CI workflow, `.env.example` denetimi | BE-1 |

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

## Devam eden

_(ajan görevi alınca satırı buraya taşır ve yanına oturum tarihini yazar)_

## Bloke

_(başka ajanın dizininde sorun gördüğünde buraya yaz, kendin düzeltme)_

## Biten

_(tek satır sonuç notuyla)_

- **BE-3** · `docs/openapi.yaml` v0 yazıldı: `/health`, `/stats`, `/businesses`; 8 adlandırılmış şema, inline gövde yok, redocly lint 0 hata. FE-3 tip üretimi için hazır. Faz 1'de auth yok, `security: []` ile açıkça beyan edildi.
