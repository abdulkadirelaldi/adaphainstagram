import { Suspense } from "react";
import { AdayPaneli } from "@/components/aday-paneli";

/**
 * Panel ana ekranı. Tek işi var: hangi hesabın rapora gideceğine karar
 * verdirmek.
 *
 * FE-2'de veri mock; filtre durumu URL query'sinde. `useSearchParams` bir Suspense
 * sınırı ister (Next 15). Gerçek istek FE-3'te bağlanır.
 */
export default function AdaylarSayfasi() {
  return (
    <Suspense>
      <AdayPaneli />
    </Suspense>
  );
}
