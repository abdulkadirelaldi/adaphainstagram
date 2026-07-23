# [FRONTEND] Faz 2 · FE-4 canlı doğrulama (görevi kapat)

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. FE-4'ün UI'ı zaten
`## Devam eden`'de tamam — bu tur **yeni özellik yok**, yalnızca BE-9 canlıyken uçtan uca
doğrulama ve görevi `## Biten`'e taşıma. Kod değişmesi gerekirse yalnız `web/**` ve
`docs/DESIGN.md`.

## Amaç

BE-9 keşif akışını canlıya aldı (`POST /discovery/run` + `GET /jobs/{id}` + arq worker).
FE-4'ün route-mock'la kanıtladığı akışı şimdi **gerçek backend'e karşı** doğrula.

**Oku:** `docs/TASKS.md` `## Biten` → BE-9 satırı (uçları nasıl ayağa kaldıracağın: DATABASE_URL
+ REDIS_URL, migration, arq worker, demo). Kendi FE-4 çıktın (`## Devam eden`).

**Backend'i çalıştırmak yazmak değildir** — `api/`'ye dokunmadan, backend'i lokalde ayağa
kaldırıp panelden doğrulayabilirsin. `api/` içinde bir sorun görürsen düzeltme, `## Bloke`'ya yaz.

## Doğrulama adımları (headless veya Network ile kanıtla)
1. Backend'i ayağa kaldır: postgres + redis + migration + FastAPI (`uvicorn`) + arq worker.
   (BE-9'un demo/README talimatı yol gösterir.)
2. Panel `localhost:3000`, API `localhost:8000` ayaktayken keşif çubuğundan tara.
3. **Gerçek `job_id`** dönüyor, uç anında (senkron değil).
4. `GET /jobs/{id}` **gerçek durum geçişini** yokluyor: `queued → running → done`; UI her
   durumu gösteriyor.
5. İş bitince aday tablosu + üst şerit **gerçek DB verisiyle** tazeleniyor (keşfedilen ~20
   işletme, handle'lılar snapshot'lı).
6. **Poll `done`'da gerçekten duruyor** (Network'te sonsuz istek yok).
7. Hata dalı: geçersiz/başarısız bir işle `error` durumu tetiklenip gösteriliyor.

## Kabul kriterleri
- Yukarıdaki 7 adım gerçek backend'e karşı doğrulandı (headless çıktısı/Network kanıtı kapanış
  notunda).
- Route-mock kaldırıldıysa ya da yalnız test amaçlı kaldıysa belirt; üretim yolu gerçek uçları
  kullanıyor.
- `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş; yasak-metrik grep boş.
- Panelde erişim/gösterim/kaydetme/demografi gösteren hiçbir alan yok (kural 7).

## Kapanış
`docs/TASKS.md`'de FE-4'ü `## Devam eden`'den `## Biten`'e taşı, canlı doğrulama sonucuyla.
`docs/DESIGN.md` güncel değilse güncelle. `git add web/ docs/DESIGN.md docs/TASKS.md`,
`fe:` prefix'iyle commit'le. Sonra orkestra şefine "FE-4 canlı doğrulandı, panel gerçek keşfi
gösteriyor" de.
