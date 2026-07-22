import { Suspense } from "react";
import { AdayPaneli } from "@/components/aday-paneli";

/**
 * Panel ana ekranı. Tek işi var: hangi hesabın rapora gideceğine karar
 * verdirmek.
 *
 * Veri gerçek `/stats` + `/businesses` uçlarından; filtre durumu URL query'sinde.
 * `useSearchParams` bir Suspense sınırı ister (Next 15).
 */
export default function AdaylarSayfasi() {
  return (
    <Suspense>
      <AdayPaneli />
    </Suspense>
  );
}
