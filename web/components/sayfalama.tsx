"use client";

import type { Route } from "next";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { sorguYaz } from "@/lib/sorgu-durumu";

/**
 * Sayfalama: limit / offset, yanıttaki total ile. Offset URL query'de tutulur.
 * Tek sayfa varsa hiç çizilmez — boş şeritle yer kaplamaz.
 */
export function Sayfalama({
  offset,
  limit,
  toplam,
}: {
  offset: number;
  limit: number;
  toplam: number;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  if (toplam <= limit) return null;

  const ilk = toplam === 0 ? 0 : offset + 1;
  const son = Math.min(offset + limit, toplam);
  const oncekiVar = offset > 0;
  const sonrakiVar = son < toplam;

  function git(yeniOffset: number) {
    const qs = sorguYaz(params, "offset", String(Math.max(0, yeniOffset)));
    router.replace((qs ? `${pathname}?${qs}` : pathname) as Route, {
      scroll: false,
    });
  }

  return (
    <div className="flex items-center justify-between border-t border-cizgi px-6 py-3">
      <span className="text-kucuk text-kursun">
        <span className="sayi tabular-nums">{ilk}</span>–
        <span className="sayi tabular-nums">{son}</span> /{" "}
        <span className="sayi tabular-nums">{toplam}</span>
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={!oncekiVar}
          onClick={() => git(offset - limit)}
          className="h-8 border border-cizgi px-3 text-govde disabled:text-cizgi"
        >
          Önceki
        </button>
        <button
          type="button"
          disabled={!sonrakiVar}
          onClick={() => git(offset + limit)}
          className="h-8 border border-cizgi px-3 text-govde disabled:text-cizgi"
        >
          Sonraki
        </button>
      </div>
    </div>
  );
}
