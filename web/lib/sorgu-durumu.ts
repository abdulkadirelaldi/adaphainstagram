import type { IsletmeSorgusu } from "@/lib/api/istemci";
import type { TriageStatus } from "@/lib/skor";

/**
 * Filtre durumu URL query string'inde yaşar — sayfa yenilenince kaybolmaz,
 * paylaşılabilir, geri tuşuyla gezinilebilir. Tek gerçek kaynak URL'dir; bileşen
 * yerel filtre state'i tutmaz.
 *
 * Query adları ve değer kümeleri `docs/openapi.yaml`'daki `/businesses`
 * parametreleriyle birebir aynıdır (status, category, min_score, limit, offset).
 */

export const VARSAYILAN_LIMIT = 50;

const GECERLI_STATUS: readonly TriageStatus[] = [
  "qualified",
  "watch",
  "rejected",
];

function status(deger: string | null): TriageStatus | undefined {
  return deger && (GECERLI_STATUS as readonly string[]).includes(deger)
    ? (deger as TriageStatus)
    : undefined;
}

function pozitifSayi(deger: string | null): number | undefined {
  if (deger === null) return undefined;
  const n = Number(deger);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

/** URLSearchParams → openapi sorgusu. Geçersiz değerler sessizce düşer. */
export function sorguCoz(params: URLSearchParams): IsletmeSorgusu {
  const kategori = params.get("category");
  const minSkor = pozitifSayi(params.get("min_score"));
  const limit = pozitifSayi(params.get("limit"));
  const offset = pozitifSayi(params.get("offset"));

  return {
    status: status(params.get("status")),
    category: kategori && kategori.length > 0 ? kategori : undefined,
    min_score: minSkor !== undefined && minSkor <= 100 ? minSkor : undefined,
    limit: limit !== undefined && limit >= 1 ? Math.min(limit, 200) : VARSAYILAN_LIMIT,
    offset: offset ?? 0,
  };
}

/**
 * Tek bir anahtarı değiştirip yeni query string üretir. Filtre değişince sayfa
 * başa döner (offset sıfırlanır); yalnızca offset değişiyorsa korunur.
 */
export function sorguYaz(
  mevcut: URLSearchParams,
  anahtar: string,
  deger: string | null,
): string {
  const sonraki = new URLSearchParams(mevcut.toString());

  if (deger === null || deger === "") {
    sonraki.delete(anahtar);
  } else {
    sonraki.set(anahtar, deger);
  }

  if (anahtar !== "offset") {
    sonraki.delete("offset");
  }

  return sonraki.toString();
}
