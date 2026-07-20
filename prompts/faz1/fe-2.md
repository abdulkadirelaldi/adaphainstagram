# [FRONTEND] Faz 1 · FE-2 — panel kabuğu

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku. Sadece `web/**` ve
`docs/DESIGN.md` altına yazarsın. `api/**`, `docs/openapi.yaml`, `tests/**`, `.gitignore`
dosyalarına dokunmazsın — sorun görürsen `docs/TASKS.md` `## Bloke` altına yazarsın.

## GÖREV FE-2

**Amaç:** Panelin üst şeridini, aday tablosunu ve filtrelerini mock veriyle çizmek.

**Oku:** `docs/SPEC.md` §7 (uçların ne döndüğü), §1 (durum eşikleri: <40 elendi, 40–69
izlemede, ≥70 nitelikli), §4 (skorun üç alt bileşeni). Ayrıca **`docs/openapi.yaml`** —
BE-3 sözleşmesi hazır, mock verinin şekli oradaki `Business` ve `Stats` şemalarına birebir
uymalı. Bir de kendi `docs/DESIGN.md`'ini.

**Dokunabileceğin dosyalar:** `web/**`, `docs/DESIGN.md`

**Yapılacaklar:**
- **Üst şerit:** `/stats` alanları — taranan, nitelikli, üretilen rapor, aylık maliyet.
  Dört sayı kartı.
- **Aday tablosu:** `Business` şemasının alanları. Skor sütunu FE-1'de tanımladığın üç
  duraklı skalayı kullanır; rakam daima okunur (renk tek taşıyıcı değil).
- **Filtreler:** `status`, `category`, `min_score` — `openapi.yaml`'daki query parametreleriyle
  aynı adlar ve aynı değer kümeleri. Filtre durumu URL query string'inde tutulsun ki sayfa
  yenilenince kaybolmasın.
- **Sayfalama:** `limit` / `offset`, yanıttaki `total` ile.
- **Üç durum çizilmeli:** yükleniyor (skeleton), boş liste, hata. Faz 1'in çıkış kriteri
  panelin **boş listeyi** düzgün çizmesi — boş durumu baştan savma, birinci sınıf tasarla.
- Mock veri `web/` içinde tek bir dosyada toplansın ve **`_mock` gibi açıkça işaretli** olsun;
  FE-3'te tek yerden sökülecek.

**Yapmayacakların:**
- **Elle API tipi yazma.** Tipler FE-3'te `docs/openapi.yaml`'dan üretilecek (`CLAUDE.md`
  kural 3). Bu turda mock veriyi yerel bir tiple modelle ama o tipi `openapi.yaml`'dan
  kopyalayarak elle yazma yerine, mock dosyasına dar bir yerel tip koy ve dosyanın başına
  `// FE-3'te üretilen tiplerle değiştirilecek` notunu düş.
- `fetch`/TanStack Query ile gerçek istek atma — bu FE-3'ün işi.
- Erişim, gösterim, kaydetme, profil ziyareti, demografi gösteren sütun/kart/grafik ekleme
  (`CLAUDE.md` kural 7). Mock veriye bile bu alanları koyma.
- Skor eşiklerini kendi kafandan değiştirme; 40 ve 70 SPEC §1'den gelir.

**Kabul kriterleri:**
- `npm run build` hatasız, `npx tsc --noEmit` sıfır hata, `npx next lint` sıfır hata.
- Mock veri kaynağını boş diziye çevirdiğinde panel çökmüyor, boş durumu çiziyor —
  bu Faz 1'in çıkış kriteri.
- Filtreleri değiştirip sayfayı yenileyince filtreler korunuyor (URL'de duruyorlar).
- Mock'taki alan adları `docs/openapi.yaml`'daki `Business` şemasıyla birebir aynı; fazladan
  veya eksik alan yok. Farkı bulursan **kendi tarafında uydurma** — `## Bloke`'ya yaz.
- `git grep -nE "impressions|reach|saves|profile_views|demographics" -- web/` çıktısı boş.
- Skor bandı renk dışında ikinci bir işaretle de kodlanıyor (FE-1'de kurduğun ray/çentik
  yaklaşımı) — renk körlüğünde bant ayırt edilebiliyor.

**Kapanış:** `docs/DESIGN.md`'i tablo, filtre ve boş/yükleniyor/hata durumlarının son haliyle
güncelle. `docs/TASKS.md`'de FE-2'yi `## Biten` altına tek satır sonuç notuyla taşı.
`git add web/ docs/DESIGN.md docs/TASKS.md` (`git add -A` yasak), `fe:` prefix'iyle commit'le.
Sonra dur ve FE-3 için hazır olduğunu bildir.
