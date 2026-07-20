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
| BE-2 | backend | SQLAlchemy modelleri ve ilk Alembic migration (SPEC §3) | BE-1 |
| BE-4 | backend | `/stats` ve `/businesses` uçları, sahte veri, BE-3 sözleşmesine birebir uyumlu | BE-2, BE-3 |
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

- **Docker bu geliştirme makinesinde kurulu değil** (backend, BE-1 sırasında fark edildi).
  `/usr/local/bin/docker` var ama kaldırılmış `Docker.app`'e işaret eden kopuk bir symlink.
  Sonucu: `docker-compose.yml` ve `Dockerfile` yazıldı fakat **hiç çalıştırılamadı** —
  Faz 1 çıkış kriterlerinden "`docker compose up` ile üç servis healthy" kutusu bu makinede
  doğrulanamaz. `/health` bunun yerine brew ile kurulu yerel postgres@16 + redis'e karşı
  doğrulandı (sağlıklı yol, iki ayrı arıza yolu ve toparlanma — hepsi geçti). Compose
  dosyasında yazım hatası kalmış olabilir; ilk `docker compose up` deneyen ajan bunu
  hesaba katsın. Karar orkestra şefinin: Docker Desktop kurulacak mı, yoksa Faz 1 çıkış
  kriteri yerel servislerle mi kabul edilecek?

## Biten

_(tek satır sonuç notuyla)_

- **BE-1** · FastAPI iskeleti, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`. `/health` postgres'e `SELECT 1` ve redis'e `PING` atıyor; sağlıklı yol 200, her iki arıza yolu 503 olarak yerel servislerle doğrulandı. `docker compose` doğrulanamadı — bkz. `## Bloke`. BE-2 hazır.
- **BE-3** · `docs/openapi.yaml` v0 yazıldı: `/health`, `/stats`, `/businesses`; 8 adlandırılmış şema, inline gövde yok, redocly lint 0 hata. FE-3 tip üretimi için hazır. Faz 1'de auth yok, `security: []` ile açıkça beyan edildi.
- **FE-1** · Next 15.5 + React 19 + Tailwind v4 + TanStack Query iskeleti, token'lar `web/styles/tokens.css`'te tek kaynakta; `docs/DESIGN.md` yazıldı. İleri taşınan eksen: patina düz değerden 40/70 eşiklerine bağlı üç duraklı skalaya dönüştü — komşu duraklar 1.38:1 ölçüldüğü için bant ayrıca ray konumu ve çentik yüksekliğiyle kodlanıyor, rakam okunabilirlik için daima mürekkep. build + `tsc --noEmit` + lint sıfır hata, `/` 200 dönüyor. FE-2 hazır.
