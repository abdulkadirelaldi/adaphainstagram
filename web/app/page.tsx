import { AdayTablosu } from "@/components/aday-tablosu";
import { UstSerit } from "@/components/ust-serit";

/**
 * Panel ana ekranı. Tek işi var: hangi hesabın rapora gideceğine karar
 * verdirmek.
 *
 * FE-1'de veri katmanı bağlanmaz — üst şerit yarım tirelerle, tablo boş
 * durumla çizilir. Mock veri FE-2'de, gerçek istek FE-3'te gelir.
 */
export default function AdaylarSayfasi() {
  return (
    <div className="flex flex-col">
      <UstSerit />
      <AdayTablosu durum="bos" />
    </div>
  );
}
