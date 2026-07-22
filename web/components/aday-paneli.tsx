"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AdayTablosu } from "@/components/aday-tablosu";
import { Filtreler } from "@/components/filtreler";
import { KesifCubugu } from "@/components/kesif-cubugu";
import { Sayfalama } from "@/components/sayfalama";
import { UstSerit } from "@/components/ust-serit";
import { useBusinesses, useKohortKaynagi, useStats } from "@/lib/api/sorgular";
import { kategoriler as benzersizKategoriler } from "@/lib/kohort";
import { sorguCoz } from "@/lib/sorgu-durumu";

/**
 * Panel gövdesi. Filtre durumunu URL'den okur, gerçek `/stats` ve `/businesses`
 * uçlarını TanStack Query ile çağırır, üst şeridi ve tabloyu çizer.
 *
 * Üç durum artık gerçek: ağ/CORS hatası hata durumunu, `items: []` boş durumu
 * tetikler. Kohort rayı ayrı, filtresiz bir kaynaktan beslenir ki filtre altında
 * bile görece konum bozulmasın.
 */
export function AdayPaneli() {
  const params = useSearchParams();

  const sorgu = useMemo(
    () => sorguCoz(new URLSearchParams(params.toString())),
    [params],
  );

  const stats = useStats();
  const liste = useBusinesses(sorgu);
  const kohort = useKohortKaynagi();

  const kohortKaynagi = useMemo(() => kohort.data?.items ?? [], [kohort.data]);
  const kategoriler = useMemo(
    () => benzersizKategoriler(kohortKaynagi),
    [kohortKaynagi],
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
    <div className="flex flex-col">
      <KesifCubugu />
      <UstSerit istatistik={stats.data} />
      <Filtreler kategoriler={kategoriler} toplam={liste.data?.total ?? 0} />
      <AdayTablosu durum={durum} kohortKaynagi={kohortKaynagi} />
      <Sayfalama
        offset={sorgu.offset}
        limit={sorgu.limit}
        toplam={liste.data?.total ?? 0}
      />
    </div>
  );
}
