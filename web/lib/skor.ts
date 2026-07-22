/**
 * Triyaj skoru ve durumu — eşikler SPEC §1'den, durum değerleri SPEC §3'ten gelir
 * ve tek yerde burada durur.
 *
 *   score < 40   →  bant: elendi     (status: rejected, arşiv)
 *   40 ≤ s < 70  →  bant: izlemede   (status: watch, 90 gün sonra tekrar)
 *   score ≥ 70   →  bant: nitelikli  (status: qualified, derin denetim)
 *
 * Bu, panelde ölçülen İKİ skordan biridir ve yönü YUKARI'dır: yüksek skor iyi
 * adaydır. Denetimdeki görünürlük skoru ters yönde çalışır (düşükse hesap kötü
 * yönetiliyor) ve asla bu modülden geçmez. Bkz. docs/DESIGN.md § "İki skor".
 *
 * ÖNEMLİ: Otoriter triyaj kararı `status`'tur, `score` değil. SPEC §4 gereği kohort
 * 5 hesabın altındaysa potansiyel alt skoru hesaplanmaz ve hesap skoru ne olursa
 * olsun `watch` olur. Bu yüzden bant DAİMA `status`'tan türetilir; `score` yalnızca
 * raydaki konumu belirler.
 */

import type { TriageStatus } from "@/lib/api/tipler";

export type { TriageStatus };

export const ESIK_NITELIKLI = 70;
export const ESIK_IZLEMEDE = 40;

/** Kohort medyanı bu sayının altındaki kohortlarda hesaplanmaz (SPEC §4). */
export const ASGARI_KOHORT = 5;

/** Görsel bant. Statusun panel karşılığı; renk ve çentik yüksekliği buna bağlanır. */
export type SkorBandi = "elendi" | "izlemede" | "nitelikli";

const STATUS_BANT: Record<TriageStatus, SkorBandi> = {
  qualified: "nitelikli",
  watch: "izlemede",
  rejected: "elendi",
};

/** Otoriter yol: backend durumundan görsel banda. */
export function statusBandi(status: TriageStatus): SkorBandi {
  return STATUS_BANT[status];
}

/**
 * Yalnızca status yokken (henüz durum atanmamış ama skor varsa) başvurulan yedek.
 * Normal akışta statusBandi kullanılır — bu fonksiyon kohort<5 kuralını bilmez.
 */
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

export const STATUS_ETIKET: Record<TriageStatus, string> = {
  qualified: "Nitelikli",
  watch: "İzlemede",
  rejected: "Elendi",
};

/** Skoru 0–100 aralığına sıkıştırır; ray dışına taşan çentik çizilmez. */
export function kelepcele(skor: number): number {
  return Math.min(100, Math.max(0, skor));
}
