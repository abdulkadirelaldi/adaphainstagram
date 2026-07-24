import type { Bulgu, Onem } from "@/lib/api/tipler";

/**
 * Bulgu önemi (SPEC §5). Önem = ceza ağırlığı; görünürlük skoru bu bulguların
 * ağırlıklı cezasıdır. Panelde bulgular **öneme göre** sıralanır, kritik üstte.
 *
 * Renk kararı DESIGN §1: önem KROMATİK olarak kodlanmaz — yalnızca kritik oksit
 * alır (tek kritik sinyal), kalan üç seviye sıralama ve tipografik ağırlıkla
 * ayrışır. Dört önemi dört renge dağıtmak "renkli olan tek şey skordur"u bozardı.
 */

const SIRA: Record<Onem, number> = {
  kritik: 0,
  yüksek: 1,
  orta: 2,
  düşük: 3,
};

export const ONEM_ETIKET: Record<Onem, string> = {
  kritik: "Kritik",
  yüksek: "Yüksek",
  orta: "Orta",
  düşük: "Düşük",
};

/** Bulguları öneme göre sıralar (kritik üstte). Girdiyi bozmaz. */
export function onemeSirali(bulgular: readonly Bulgu[]): Bulgu[] {
  return [...bulgular].sort((a, b) => SIRA[a.severity] - SIRA[b.severity]);
}

/** Yalnızca kritik önem oksit alır; gerisi mürekkep (DESIGN §1). */
export function kritikMi(onem: Onem): boolean {
  return onem === "kritik";
}
