import { para, sayi, YOK } from "@/lib/bicim";
import type { Istatistik } from "@/lib/api/tipler";

/**
 * Üst şerit — SPEC §7 `/stats`: taranan, nitelikli, rapor, aylık maliyet.
 *
 * Dört ölçü, tek satır, kart yok. Rakamlar mono ve iri; etiketler küçük ve
 * kurşun. Veri gelmediğinde rakam yerine yarım tire durur — şerit asla kaybolmaz,
 * yeri korunur ki yükleme sırasında düzen zıplamasın.
 */
export function UstSerit({ istatistik }: { istatistik?: Istatistik }) {
  const olculer = [
    { etiket: "Taranan", deger: istatistik ? sayi(istatistik.scanned) : YOK },
    { etiket: "Nitelikli", deger: istatistik ? sayi(istatistik.qualified) : YOK },
    { etiket: "Rapor", deger: istatistik ? sayi(istatistik.reports) : YOK },
    {
      etiket: "Aylık maliyet",
      deger: istatistik ? para(istatistik.monthly_cost_usd) : YOK,
    },
  ];

  return (
    <div className="flex border-b border-cizgi">
      {olculer.map((olcu) => (
        <div
          key={olcu.etiket}
          className="flex flex-col gap-1 border-r border-cizgi px-6 py-4 last:border-r-0"
          style={{ minWidth: "180px" }}
        >
          <span className="text-mikro text-kursun uppercase">{olcu.etiket}</span>
          <span className="sayi text-rakam tabular-nums">{olcu.deger}</span>
        </div>
      ))}
    </div>
  );
}
