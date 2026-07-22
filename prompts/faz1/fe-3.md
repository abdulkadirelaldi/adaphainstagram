# [FRONTEND] Faz 1 · FE-3 — sözleşmeden tip + canlı bağlantı

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. `api/**`, `docs/openapi.yaml`, `tests/**` dosyalarına
dokunmazsın — sorun görürsen `docs/TASKS.md` `## Bloke`'ya yazarsın.

## GÖREV FE-3 — tip üretimi, TanStack Query, mock sökümü

**Amaç:** Elle yazılmış mock tiplerini `docs/openapi.yaml`'dan üretilen tiplerle değiştirmek
ve paneli gerçek `/stats` + `/businesses` uçlarına bağlamak. Bu görev Faz 1'in son çıkış
kutusunu kapatıyor.

**Oku:** `docs/openapi.yaml` (tek doğ­ruluk kaynağı — tipler buradan üretilir, elle yazılmaz,
`CLAUDE.md` kural 3), `docs/TASKS.md` `## Biten` → BE-4 satırı (uçların ayakta olup olmadığı,
CORS origin'i), kendi FE-2 çıktın.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Tip üretimi:** `openapi-typescript` (veya eşdeğeri) ile `docs/openapi.yaml`'dan
  `web/` içine tip üret. Üretim bir `package.json` script'i olsun (`npm run gen:api` gibi) ki
  sözleşme değişince tek komutla tekrarlansın. Üretilen dosya elle düzenlenmez; başına üretildiği
  ve düzenlenmemesi gerektiği notu düşülür.
- **Mock sökümü:** FE-2'nin `web/lib/mock-veri.ts` dosyasını ve `// FE-3'te değiştirilecek`
  notlu yerel tipleri kaldır. Tablo, üst şerit ve filtreler artık üretilen tipleri kullanır.
- **TanStack Query:** `/stats` ve `/businesses` için query hook'ları. Filtre/sayfalama query
  parametreleri (`status`/`category`/`min_score`/`limit`/`offset`) FE-2'de URL'de tuttuğun
  durumdan gelir ve isteğe birebir geçer. API taban URL'i bir ortam değişkeninden okunur
  (`NEXT_PUBLIC_API_URL`, varsayılan `http://localhost:8000`) — sabit kodlama yok.
- **Üç durum korunur:** yükleniyor (skeleton), hata, boş liste. Artık gerçek: ağ hatası hata
  durumunu, `items: []` boş durumu tetikler. FE-2'de tasarladığın boş durum aynı kalır.
- Skor bandının renk-dışı ikinci işareti (ray/çentik) korunur — üretilen tip alan adlarını
  değiştirse bile görsel kodlama bozulmaz.

**Yapmayacakların:**
- Üretilen tipin üstüne elle tip yazma, `any`'ye kaçma. Sözleşmede eksik varsa **`## Bloke`'ya
  yaz**, kendi tarafında uydurma.
- Yasak metrik alanı (`impressions`/`reach`/`saves`/`profile_views`/demografi) için UI ekleme.
- `openapi.yaml`'ı düzenleme (backend'in). Tip üretimi onu **okur**, yazmaz.

**Kabul kriterleri:**
- `npm run gen:api` çalışıyor ve `web/`'e tip üretiyor; ürettikten sonra `npx tsc --noEmit`
  sıfır hata.
- `web/lib/mock-veri.ts` **silinmiş**; `git grep -n "mock" -- web/` yalnızca test/yorum
  bağlamında kalıyor, veri kaynağı olarak mock yok.
- `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- **Canlı uçtan-uca (BE-4 ayaktayken):** backend `localhost:8000`'de koşarken panel açılıyor,
  üst şerit `/stats` sayılarını **gerçek istekle** gösteriyor, tablo `/businesses`'ten geliyor.
  Filtre değiştirince ağ isteği yeni query parametreleriyle gidiyor (Network sekmesi veya
  headless ile doğrula).
- `?min_score=100&status=rejected` gibi bir filtre boş durumu çiziyor, panel çökmüyor.
- CORS engeli yok — istek backend'in izin verdiği origin'den gidiyor.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` hâlâ boş (renk token disiplini).

**BE-4 ayakta değilse:** tip üretimi, mock sökümü, build/tsc/lint ve query hook'larını yine
tamamla; yalnızca canlı uçtan-uca doğrulamayı BE-4 ayağa kalkınca yap. Bu durumda kapanış
notunda "canlı doğrulama BE-4 bekliyor" de ve görevi `## Biten`'e taşıma — `## Devam eden`'de
bırak.

**Kapanış:** `docs/TASKS.md`'de FE-3'ü `## Biten` altına tek satır sonuç notuyla taşı (canlı
doğrulama tamamsa). `docs/DESIGN.md`'i veri-bağlı son haliyle güncelle. `git add web/
docs/DESIGN.md docs/TASKS.md`, `fe:` prefix'iyle commit'le. Sonra orkestra şefine Faz 1'in
bittiğini bildir.
