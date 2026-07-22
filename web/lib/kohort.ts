import type { Isletme } from "@/lib/api/tipler";

/**
 * Bir işletmenin kohortu: AYNI kategorideki taranmış (skoru olan) tüm hesapların
 * skorları. Kohort rayının soluk çentikleri budur (SPEC §4: karşılaştırma daima
 * aynı kategorideki taranmış hesapların dağılımına göre).
 *
 * Kaynak, filtreden BAĞIMSIZ tüm liste olmalıdır — yoksa "status=qualified"
 * filtresi altında ray yalnızca qualified skorları gösterir ve görece konum
 * yanıltıcı olur. Bu yüzden panel kohortu ayrı, filtresiz bir istekten besler.
 */
export function kategoriKohortu(
  kategori: string | null,
  kaynak: readonly Isletme[],
): number[] {
  if (kategori === null) return [];
  return kaynak
    .filter((i) => i.category === kategori && i.score !== null)
    .map((i) => i.score as number);
}

/** Kaynaktaki benzersiz kategoriler, filtre açılır listesi için (tr sıralı). */
export function kategoriler(kaynak: readonly Isletme[]): string[] {
  return Array.from(
    new Set(
      kaynak
        .map((i) => i.category)
        .filter((c): c is string => c !== null && c.length > 0),
    ),
  ).sort((a, b) => a.localeCompare(b, "tr"));
}
