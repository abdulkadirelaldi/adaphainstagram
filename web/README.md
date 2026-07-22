# Radar — panel

Kıyı Medya aday tarama ve denetim panelinin arayüzü.
Next.js 15 (App Router) · TypeScript strict · Tailwind v4 · TanStack Query.

```bash
npm install
npm run gen:api   # docs/openapi.yaml → lib/api/schema.ts (sözleşme değişince tekrarla)
npm run dev       # http://localhost:3000
npm run build
npx tsc --noEmit
npx eslint .
```

## API bağlantısı

Panel `/stats` ve `/businesses` uçlarını çağırır. Taban URL `NEXT_PUBLIC_API_URL`
ortam değişkeninden okunur; verilmezse `http://localhost:8000` kullanılır (openapi
`servers` ile aynı). Yerelde farklı bir port için:

```bash
# web/.env.local  (izlenmez)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Tarayıcıdan istek atıldığından backend'in CORS'unda bu origin (`http://localhost:3000`)
izinli olmalıdır — backend varsayılanı zaten budur.

## Yapı

| yol | ne |
|---|---|
| `app/` | App Router sayfaları ve kök düzen |
| `components/` | Arayüz bileşenleri |
| `lib/api/` | Üretilen tipler (`schema.ts`), tip alias'ları, REST istemci, TanStack Query hook'ları |
| `lib/` | Eşikler, biçimlendiriciler, kohort — sabit sayı bileşenlere yazılmaz |
| `styles/tokens.css` | **Ham renk değerlerinin tek kaynağı** |

## Uyulacak kurallar

- `app/` ve `components/` altında **çıplak hex yok.** Her renk token'dan gelir.
- **Hiçbir sayı sans yüzle dizilmez.** Rakam taşıyan her öğe `.sayi` sınıfını alır.
- **API tipleri elle yazılmaz.** `npm run gen:api` ile `docs/openapi.yaml`'dan üretilir
  (`CLAUDE.md` kural 3). `lib/api/schema.ts` elle düzenlenmez; alias'lar `lib/api/tipler.ts`'te.
- Erişim, gösterim, kaydetme, profil ziyareti ve demografi bu sistemde **yoktur**; bu
  metrikler için sütun, kart veya grafik tasarlanmaz (`CLAUDE.md` kural 7).
- Panelde ters yönlü **iki skor** var ve asla aynı isimle anılmazlar.
  Bkz. `docs/DESIGN.md` §5.

Tasarım kararları ve gerekçeleri: `docs/DESIGN.md`.
