# Radar — panel

Kıyı Medya aday tarama ve denetim panelinin arayüzü.
Next.js 15 (App Router) · TypeScript strict · Tailwind v4 · TanStack Query.

```bash
npm install
npm run dev     # http://localhost:3000
npm run build
npx tsc --noEmit
npx eslint .
```

## Yapı

| yol | ne |
|---|---|
| `app/` | App Router sayfaları ve kök düzen |
| `components/` | Arayüz bileşenleri |
| `lib/` | Eşikler ve biçimlendiriciler — sabit sayı bileşenlere yazılmaz |
| `styles/tokens.css` | **Ham renk değerlerinin tek kaynağı** |

## Uyulacak kurallar

- `app/` ve `components/` altında **çıplak hex yok.** Her renk token'dan gelir.
- **Hiçbir sayı sans yüzle dizilmez.** Rakam taşıyan her öğe `.sayi` sınıfını alır.
- **API tipleri elle yazılmaz.** `docs/openapi.yaml`'dan üretilir (`CLAUDE.md` kural 3).
- Erişim, gösterim, kaydetme, profil ziyareti ve demografi bu sistemde **yoktur**; bu
  metrikler için sütun, kart veya grafik tasarlanmaz (`CLAUDE.md` kural 7).
- Panelde ters yönlü **iki skor** var ve asla aynı isimle anılmazlar.
  Bkz. `docs/DESIGN.md` §5.

Tasarım kararları ve gerekçeleri: `docs/DESIGN.md`.
