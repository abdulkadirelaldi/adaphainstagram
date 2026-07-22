import { KohortRayi } from "@/components/kohort-rayi";
import { YOK } from "@/lib/bicim";
import {
  skorBandi,
  statusBandi,
  STATUS_ETIKET,
  type TriageStatus,
} from "@/lib/skor";

/**
 * Skor hücresi: mono rakam + kohort rayı.
 *
 * Rakam daima mürekkep rengindedir (17.01:1). Renk yalnızca raydaki dolu
 * çentikte yaşar — böylece bant kodlaması okunabilirlikten ödün vermez ve
 * "renkli olan tek şey skordur" kuralı bozulmaz.
 *
 * Bant otoriter olarak `status`'tan gelir. Skor null ama status varsa (kohort<5,
 * SPEC §4) rakam yerine yarım tire, yanında status etiketi durur — ray boş kalır.
 */
export function SkorHucresi({
  skor,
  status,
  kohort,
}: {
  skor: number | null;
  status: TriageStatus | null;
  kohort: readonly number[];
}) {
  const bant =
    status !== null
      ? statusBandi(status)
      : skor !== null
        ? skorBandi(skor)
        : null;

  return (
    <div className="flex items-center gap-3">
      <span className="sayi w-7 shrink-0 text-right text-orta tabular-nums">
        {skor === null ? YOK : Math.round(skor)}
      </span>
      <KohortRayi skor={skor} bant={bant} kohort={kohort} />
      {/* Skor yokken durum sözle söylenir; ray konumu olmadığından tek işaret budur. */}
      {skor === null && status !== null && (
        <span className="text-kucuk text-kursun">{STATUS_ETIKET[status]}</span>
      )}
    </div>
  );
}
