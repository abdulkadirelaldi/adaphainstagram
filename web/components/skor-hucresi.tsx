import { KohortRayi } from "@/components/kohort-rayi";

/**
 * Skor hücresi: mono rakam + kohort rayı.
 *
 * Rakam daima mürekkep rengindedir (17.01:1). Renk yalnızca raydaki dolu
 * çentikte yaşar — böylece bant kodlaması okunabilirlikten ödün vermez ve
 * "renkli olan tek şey skordur" kuralı bozulmaz.
 */
export function SkorHucresi({
  skor,
  kohort,
}: {
  skor: number;
  kohort: readonly number[];
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="sayi w-7 text-right text-orta tabular-nums">
        {Math.round(skor)}
      </span>
      <KohortRayi skor={skor} kohort={kohort} />
    </div>
  );
}
