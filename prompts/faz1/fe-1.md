# [FRONTEND] Faz 1 · FE-1 — iskelet ve tasarım dili

Sen Radar projesinin **frontend** ajanısın. `CLAUDE.md`'yi oku ve dosya sahipliği kurallarına
harfiyen uy: sadece `web/**` ve `docs/DESIGN.md` altına yazarsın. `api/**`,
`docs/openapi.yaml`, `tests/**` dosyalarına **dokunmazsın** — orada sorun görürsen
`docs/TASKS.md` içindeki `## Bloke` başlığına not düşersin.

## GÖREV FE-1

**Amaç:** Next.js 15 uygulamasını kurmak ve panelin tasarım dilini `docs/DESIGN.md`'de
sabitlemek.

**Oku:** `docs/SPEC.md` §7 (`/stats` ve `/businesses` panelde ne gösterecek) ve §4 (triyaj
skoru — skorun üç alt bileşeni var, tasarım bunu taşımalı).

**Dokunabileceğin dosyalar:**
- `web/**` (tamamı)
- `docs/DESIGN.md` (yeni dosya)

**Yapılacaklar:**
- Next.js 15 App Router, TypeScript **strict** (`strict: true`,
  `noUncheckedIndexedAccess: true`), Tailwind, TanStack Query kurulumu.
- Tasarım token'ları: renk, tipografi ölçeği, boşluk, yarıçap. Tailwind config'e ver,
  bileşenlerde çıplak hex kullanma.
- Skor için renk skalası tanımla: `< 40` elendi, `40–69` izlemede, `≥ 70` nitelikli
  (SPEC §1'deki eşikler). Bu üç durum panelde tek bakışta ayırt edilmeli.
- `docs/DESIGN.md`: token tablosu, skor renk skalası ve eşikleri, tablo/üst şerit yerleşim
  kuralları, boş durum ve yükleniyor durumu davranışı.
- Uygulama kabuğu: sol gezinme + içerik alanı, tek sayfa (`/`) yeterli. Veri **yok** bu
  görevde; FE-2'de mock, FE-3'te gerçek gelecek.

**Yapmayacakların:**
- Elle API tipi yazma. Tipler FE-3'te `docs/openapi.yaml`'dan üretilecek (`CLAUDE.md` kural 3).
  Şimdilik veri katmanına hiç dokunma.
- Erişim, gösterim, kaydetme, profil ziyareti veya demografi gösteren hiçbir
  kart/sütun/grafik tasarlama. Bu veriler sistemde yok (`CLAUDE.md` kural 7).

**Kabul kriterleri:**
- `npm run build` (veya `pnpm build`) `web/` içinde hatasız.
- `npx tsc --noEmit` sıfır hata.
- `npx next lint` sıfır hata.
- `docs/DESIGN.md` skor eşiklerini (40 / 70) sayısal olarak içeriyor ve SPEC §1 ile uyuşuyor.
- `git grep -nE "#[0-9a-fA-F]{6}" -- web/app web/components` çıktısı boş (renkler yalnızca
  token dosyasında).

**Kapanış:** `docs/TASKS.md`'de FE-1'i `## Biten` altına tek satır sonuç notuyla taşı.
`git add web/ docs/DESIGN.md docs/TASKS.md` ile stage et (`git add -A` yasak), `fe:`
prefix'iyle commit'le. Sonra dur ve FE-2 için beklemede olduğunu bildir.
