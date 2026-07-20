# Görev tahtası

Ajanlar arası tek senkronizasyon noktası. Her ajan görevine başlarken bu dosyayı okur,
bitirince günceller. Orkestra şefi yeni görev ekler, diğerleri kendi satırını taşır.

Görev id formatı: `BE-1`, `FE-1`, `SEC-1`. Numara asla geri kullanılmaz.

---

## Aktif faz

**Faz 1 — iskelet.** Bitiş kriteri: panel boş aday listesini çiziyor, `/stats` sahte veri dönüyor.

## Açık

| id | ajan | görev | bağımlı |
|---|---|---|---|
| BE-1 | backend | Repo iskeleti, docker-compose (postgres 16 + redis), FastAPI app, sağlık ucu | — |
| BE-2 | backend | SQLAlchemy modelleri ve ilk Alembic migration (SPEC §3) | BE-1 |
| BE-3 | backend | `docs/openapi.yaml` v0: `/stats` ve `/businesses`, sahte veri döner | BE-2 |
| FE-1 | frontend | Next.js iskeleti, tasarım token'ları, `docs/DESIGN.md` yazımı | — |
| FE-2 | frontend | Panel kabuğu: üst şerit + aday tablosu + filtre, mock veriyle | FE-1 |
| FE-3 | frontend | `docs/openapi.yaml`'dan tip üretimi, TanStack Query bağlantısı | BE-3, FE-2 |
| SEC-1 | güvenlik | ruff + mypy + pytest kurulumu, CI workflow, `.env.example` denetimi | BE-1 |

## Devam eden

_(ajan görevi alınca satırı buraya taşır ve yanına oturum tarihini yazar)_

## Bloke

_(başka ajanın dizininde sorun gördüğünde buraya yaz, kendin düzeltme)_

## Biten

_(tek satır sonuç notuyla)_
