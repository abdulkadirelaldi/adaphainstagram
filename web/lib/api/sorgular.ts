import { useQuery } from "@tanstack/react-query";
import {
  getBusinesses,
  getStats,
  type IsletmeSorgusu,
} from "@/lib/api/istemci";

/** openapi `limit` üst sınırı — kohort kaynağı bu kadar kaydı kapsar. */
const KOHORT_LIMITI = 200;

/** Üst şerit sayaçları — `/stats`. */
export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: ({ signal }) => getStats(signal),
  });
}

/** Filtreli, sayfalı aday listesi — `/businesses`. */
export function useBusinesses(sorgu: IsletmeSorgusu) {
  return useQuery({
    queryKey: ["businesses", sorgu],
    queryFn: ({ signal }) => getBusinesses(sorgu, signal),
    // Sayfa değişiminde tablo boşalıp yeniden dolmasın; eski veri yeni gelene
    // dek durur (TanStack v5 `placeholderData` ile önceki sonucu tutar).
    placeholderData: (onceki) => onceki,
  });
}

/**
 * Kohort kaynağı — filtresiz tüm liste, yalnızca kohort rayının dağılımı için.
 * Ana listeden ayrı tutulur ki filtre uygulansa bile ray tüm kohortu göstersin
 * ve görece konum bozulmasın. Tek istek, 30s cache.
 *
 * Sınır: `KOHORT_LIMITI` kaydı aşan bir kohort kaynağı eksik kalır — Faz 1 sahte
 * verisinde sorun değil. Kalıcı çözüm için kategori-dağılım ucu gerekir; bkz.
 * docs/TASKS.md ## Bloke (FE-3 notu).
 */
export function useKohortKaynagi() {
  return useQuery({
    queryKey: ["kohort-kaynagi"],
    queryFn: ({ signal }) =>
      getBusinesses({ limit: KOHORT_LIMITI, offset: 0 }, signal),
    staleTime: 30_000,
  });
}
