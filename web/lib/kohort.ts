import type { KategoriKohort, KategoriKohortListesi } from "@/lib/api/tipler";

/**
 * Kohort istatistiklerine kategori adıyla erişim. Kaynak `GET /stats/categories`
 * (BE-23): kategori başına skor dağılımı (medyan + çeyrekler) + skorlanmış hesap
 * sayısı. FE-3'ün `/businesses?limit=200` türetimi bununla söküldü (FE-3-B1).
 *
 * SPEC §4: kohort<5 → dağılım hesaplanmaz (`score_median` null). Ray o durumda
 * çeyrek bandı çizmez; skorsuz `watch` hesap zaten "—" + status gösterir (FE-2).
 */

/** Kategori adı → kohort kaydı haritası. */
export function kohortHaritasi(
  liste: KategoriKohortListesi | undefined,
): Map<string, KategoriKohort> {
  const m = new Map<string, KategoriKohort>();
  if (!liste) return m;
  for (const k of liste.items) m.set(k.category, k);
  return m;
}

/** Filtre açılır listesi için kategoriler (kohort ucundan, tr sıralı). */
export function kategoriler(
  liste: KategoriKohortListesi | undefined,
): string[] {
  if (!liste) return [];
  return liste.items
    .map((k) => k.category)
    .filter((c) => c.length > 0)
    .sort((a, b) => a.localeCompare(b, "tr"));
}
