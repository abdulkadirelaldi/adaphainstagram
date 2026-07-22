"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AdayTablosu } from "@/components/aday-tablosu";
import { Filtreler } from "@/components/filtreler";
import { Sayfalama } from "@/components/sayfalama";
import { UstSerit } from "@/components/ust-serit";
import {
  MOCK_ISLETMELER,
  MOCK_ISTATISTIK,
  sorgula,
} from "@/lib/mock-veri";
import { sorguCoz } from "@/lib/sorgu-durumu";

/**
 * Panel gövdesi. Filtre durumunu URL'den okur, mock kaynağı sorgular, üst şeridi
 * ve tabloyu çizer.
 *
 * FE-2 mock veriyi SENKRON tüketir; tablo durumu bu turda daima "hazir" (liste
 * boşsa boş durum). Yükleniyor ve hata durumları tabloda birinci sınıf tasarlıdır
 * ve FE-3'te TanStack Query'nin isLoading / isError bayraklarına bağlanacaktır —
 * o bağlantı dışında hiçbir şey değişmez.
 */
export function AdayPaneli() {
  const params = useSearchParams();

  const sorgu = useMemo(
    () => sorguCoz(new URLSearchParams(params.toString())),
    [params],
  );

  const liste = useMemo(() => sorgula(sorgu), [sorgu]);

  const kategoriler = useMemo(
    () =>
      Array.from(
        new Set(
          MOCK_ISLETMELER.map((i) => i.category).filter(
            (c): c is string => c !== null,
          ),
        ),
      ).sort((a, b) => a.localeCompare(b, "tr")),
    [],
  );

  return (
    <div className="flex flex-col">
      <UstSerit istatistik={MOCK_ISTATISTIK} />
      <Filtreler kategoriler={kategoriler} toplam={liste.total} />
      <AdayTablosu durum={{ tip: "hazir", kayitlar: liste.items }} />
      <Sayfalama
        offset={sorgu.offset}
        limit={sorgu.limit}
        toplam={liste.total}
      />
    </div>
  );
}
