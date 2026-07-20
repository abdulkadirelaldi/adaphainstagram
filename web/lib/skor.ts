/**
 * Triyaj skoru bantları — eşikler SPEC §1'den gelir ve burada tek yerde durur.
 *
 *   < 40   elendi     (arşiv)
 *   40–69  izlemede   (90 gün sonra tekrar)
 *   ≥ 70   nitelikli  (derin denetim)
 *
 * Bu, panelde ölçülen İKİ skordan biridir ve yönü YUKARI'dır: yüksek skor iyi
 * adaydır. Denetimdeki görünürlük skoru ters yönde çalışır (düşükse hesap kötü
 * yönetiliyor) ve asla bu modülden geçmez. Bkz. docs/DESIGN.md § "İki skor".
 */

export const ESIK_NITELIKLI = 70;
export const ESIK_IZLEMEDE = 40;

/** Kohort medyanı bu sayının altındaki kohortlarda hesaplanmaz (SPEC §4). */
export const ASGARI_KOHORT = 5;

export type SkorBandi = "elendi" | "izlemede" | "nitelikli";

export function skorBandi(skor: number): SkorBandi {
  if (skor >= ESIK_NITELIKLI) return "nitelikli";
  if (skor >= ESIK_IZLEMEDE) return "izlemede";
  return "elendi";
}

export const BANT_ETIKET: Record<SkorBandi, string> = {
  elendi: "Elendi",
  izlemede: "İzlemede",
  nitelikli: "Nitelikli",
};

/** Skoru 0–100 aralığına sıkıştırır; ray dışına taşan çentik çizilmez. */
export function kelepcele(skor: number): number {
  return Math.min(100, Math.max(0, skor));
}
