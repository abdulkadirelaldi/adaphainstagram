import { YOK } from "@/lib/bicim";

/**
 * Üst şerit — SPEC §7 `/stats`: taranan, nitelikli, rapor, aylık maliyet.
 *
 * Dört ölçü, tek satır, kart yok. Rakamlar mono ve iri; etiketler küçük ve
 * kurşun. Veri gelmediğinde rakam yerine yarım tire durur — şerit asla
 * kaybolmaz, yeri korunur ki yükleme sırasında düzen zıplamasın.
 */

type Olcu = { etiket: string; deger: string };

export function UstSerit({ olculer }: { olculer?: readonly Olcu[] }) {
  const gosterilecek: readonly Olcu[] = olculer ?? [
    { etiket: "Taranan", deger: YOK },
    { etiket: "Nitelikli", deger: YOK },
    { etiket: "Rapor", deger: YOK },
    { etiket: "Aylık maliyet", deger: YOK },
  ];

  return (
    <div className="flex border-b border-cizgi">
      {gosterilecek.map((olcu) => (
        <div
          key={olcu.etiket}
          className="flex flex-col gap-1 border-r border-cizgi px-6 py-4 last:border-r-0"
          style={{ minWidth: "180px" }}
        >
          <span className="text-mikro text-kursun uppercase">
            {olcu.etiket}
          </span>
          <span className="sayi text-rakam">{olcu.deger}</span>
        </div>
      ))}
    </div>
  );
}
