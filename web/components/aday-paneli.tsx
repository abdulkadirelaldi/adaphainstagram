"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AdayTablosu } from "@/components/aday-tablosu";
import { DenetimPaneli } from "@/components/denetim-paneli";
import { Filtreler } from "@/components/filtreler";
import { KesifCubugu } from "@/components/kesif-cubugu";
import { Sayfalama } from "@/components/sayfalama";
import { UstSerit } from "@/components/ust-serit";
import type { Isletme } from "@/lib/api/tipler";
import {
  useBusinesses,
  useCategoryCohorts,
  useStats,
} from "@/lib/api/sorgular";
import { kategoriler as kohortKategorileri, kohortHaritasi } from "@/lib/kohort";
import { sorguCoz } from "@/lib/sorgu-durumu";

/**
 * Panel gövdesi. Filtre durumunu URL'den okur, gerçek `/stats` ve `/businesses`
 * uçlarını TanStack Query ile çağırır, üst şeridi ve tabloyu çizer.
 *
 * Üç durum artık gerçek: ağ/CORS hatası hata durumunu, `items: []` boş durumu
 * tetikler. Kohort rayı ayrı bir uçtan (`/stats/categories`) beslenir ki filtre
 * altında bile görece konum bozulmasın (FE-3-B1 bununla kapandı).
 */
export function AdayPaneli() {
  const params = useSearchParams();

  const sorgu = useMemo(
    () => sorguCoz(new URLSearchParams(params.toString())),
    [params],
  );

  const [secili, setSecili] = useState<Isletme | null>(null);

  const stats = useStats();
  const liste = useBusinesses(sorgu);
  const kohortlarSorgu = useCategoryCohorts();

  const kohortlar = useMemo(
    () => kohortHaritasi(kohortlarSorgu.data),
    [kohortlarSorgu.data],
  );
  const kategoriler = useMemo(
    () => kohortKategorileri(kohortlarSorgu.data),
    [kohortlarSorgu.data],
  );

  const durum = liste.isError
    ? ({
        tip: "hata",
        yeniden: () => void liste.refetch(),
      } as const)
    : liste.isPending
      ? ({ tip: "yukleniyor" } as const)
      : ({ tip: "hazir", kayitlar: liste.data.items } as const);

  return (
    <div className="flex flex-col gap-6 p-6 lg:p-8">
      <KesifCubugu />
      <UstSerit istatistik={stats.data} />
      <section className="overflow-hidden rounded-kart border border-ayrac bg-yuzey shadow-kart">
        <Filtreler kategoriler={kategoriler} toplam={liste.data?.total ?? 0} />
        <AdayTablosu durum={durum} kohortlar={kohortlar} onSec={setSecili} />
        <Sayfalama
          offset={sorgu.offset}
          limit={sorgu.limit}
          toplam={liste.data?.total ?? 0}
        />
      </section>
      {secili && (
        <DenetimPaneli isletme={secili} onKapat={() => setSecili(null)} />
      )}
    </div>
  );
}
