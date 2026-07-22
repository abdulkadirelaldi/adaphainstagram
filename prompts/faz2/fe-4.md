# [FRONTEND] Faz 2 · FE-4 — keşif tetikleme + job yoklama

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. `api/**`, `docs/openapi.yaml`, `tests/**`'e dokunmazsın.

## GÖREV FE-4 — keşif başlat + `/jobs/{id}` yoklama UI'ı

**Amaç:** Kullanıcının keşif taraması başlatabildiği ve işin ilerlemesini gördüğü arayüzü
kurmak. Sözleşme (BE-6) donmuş durumda; tip üretimini yenile ve iki yeni ucu bağla.

**Oku:** `docs/openapi.yaml` — BE-6'nın eklediği `POST /discovery/run` ve `GET /jobs/{id}`
şemaları (job durumu enum'u, gövde alanları). SPEC §7 (uzun iş kuyruğa gider, uç anında
`job_id` döner, arayüz `/jobs/{id}` ile yoklar). Kendi FE-3 query katmanın.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Tip yenileme:** `npm run gen:api` ile `openapi.yaml`'dan tipleri yeniden üret; iki yeni
  uç tipleri gelsin. Elle tip yazma.
- **Keşif tetikleme:** bir form/düğme — bölge (varsayılan Samsun) ve sorgu/kategori girdisi
  (`POST /discovery/run` gövdesine göre). Gönderince `job_id` alınır. **Senkron beklenmez** —
  uç anında döner (SPEC §7).
- **Job yoklama:** `job_id` alınınca `GET /jobs/{id}`'i TanStack Query ile **poll** et
  (`refetchInterval`), durum `done`/`error` olunca dur. Durum enum'unun her değeri için
  görünür bir state (kuyrukta / çalışıyor / bitti / hata). İş bitince aday tablosu tazelensin
  (`/businesses` invalidate).
- **Poll disiplini:** iş bitince/hataya düşünce `refetchInterval` durur — süresiz poll yok.
  Hata durumunda kullanıcıya net mesaj + tekrar dene yolu.
- **DESIGN.md:** yoklama durum makinesini ve keşif akışının yerleşimini belgelendir.

**Yapmayacakların:**
- `openapi.yaml`'ı düzenleme (backend'in). Sözleşmede eksik görürsen `## Bloke`'ya yaz.
- Yasak metrik (`impressions`/`reach`/`saves`/`profile_views`/demografi) için UI ekleme.
- Sabit URL kodlama — `NEXT_PUBLIC_API_URL` (FE-3'te kurdun) kullan.
- `["*"]` benzeri gevşetme veya poll'u sonsuz bırakma.

**Kabul kriterleri:**
- `npm run gen:api` + `npm run build` + `npx tsc --noEmit` + `npx next lint` sıfır hata.
- **BE-9 ayakta değilken:** UI tamamlanır; tip üretimi, form, poll hook'u, durum state'leri
  hazır. Canlı uçtan-uca (gerçek `job_id`, gerçek durum geçişi, tablo tazeleme) **BE-9 ayağa
  kalkınca** doğrulanır. Bu durumda görevi `## Devam eden`'de bırak, `## Biten`'e taşıma.
- Canlı doğrulama (BE-9 ayaktayken): keşif başlat → `job_id` → durum `queued→running→done`
  yoklanıyor → tablo tazeleniyor; `error` durumu da elle tetiklenip gösteriliyor (headless
  veya Network ile doğrula).
- Poll, iş bitince gerçekten duruyor (sonsuz istek yok — Network'te doğrula).
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` boş; yasak metrik grep boş.

**Kapanış:** Canlı doğrulama tamamsa `docs/TASKS.md`'de FE-4'ü `## Biten`'e taşı; değilse
`## Devam eden`'de bırak ve "canlı doğrulama BE-9 bekliyor" not düş. `docs/DESIGN.md`'i
güncelle. `git add web/ docs/DESIGN.md docs/TASKS.md`, `fe:` prefix'iyle commit'le.
