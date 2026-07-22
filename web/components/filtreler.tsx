"use client";

import type { Route } from "next";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useId } from "react";
import { sorguYaz } from "@/lib/sorgu-durumu";
import { STATUS_ETIKET, type TriageStatus } from "@/lib/skor";

/**
 * Filtre şeridi: status · category · min_score. Değerler URL query'de tutulur;
 * bileşen yerel state tutmaz, doğrudan URL'i yazar (router.replace ile — geçmişi
 * filtre değişiklikleriyle kirletmez).
 *
 * Kategori listesi filtresiz `/businesses` kohort kaynağından türetilir.
 */

const STATUS_SIRA: readonly TriageStatus[] = ["qualified", "watch", "rejected"];

export function Filtreler({
  kategoriler,
  toplam,
}: {
  kategoriler: readonly string[];
  toplam: number;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const statusId = useId();
  const kategoriId = useId();
  const skorId = useId();

  const seciliStatus = params.get("status") ?? "";
  const seciliKategori = params.get("category") ?? "";
  const seciliSkor = params.get("min_score") ?? "";

  function yaz(anahtar: string, deger: string) {
    const qs = sorguYaz(params, anahtar, deger);
    // Tek statik rota var (/) + dinamik query; typedRoutes dinamik query'yi
    // doğrulayamaz, bu yüzden hedef Route olarak işaretlenir.
    router.replace((qs ? `${pathname}?${qs}` : pathname) as Route, {
      scroll: false,
    });
  }

  const filtreVar = seciliStatus !== "" || seciliKategori !== "" || seciliSkor !== "";

  return (
    <div className="flex flex-wrap items-end gap-6 border-b border-cizgi px-6 py-4">
      <Alan etiket="Durum" htmlFor={statusId}>
        <select
          id={statusId}
          value={seciliStatus}
          onChange={(e) => yaz("status", e.target.value)}
          className="h-8 border border-cizgi bg-kagit px-2 text-govde"
        >
          <option value="">Tümü</option>
          {STATUS_SIRA.map((s) => (
            <option key={s} value={s}>
              {STATUS_ETIKET[s]}
            </option>
          ))}
        </select>
      </Alan>

      <Alan etiket="Kategori" htmlFor={kategoriId}>
        <select
          id={kategoriId}
          value={seciliKategori}
          onChange={(e) => yaz("category", e.target.value)}
          className="h-8 border border-cizgi bg-kagit px-2 text-govde"
        >
          <option value="">Tümü</option>
          {kategoriler.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </Alan>

      <Alan etiket="En düşük triyaj skoru" htmlFor={skorId}>
        <input
          id={skorId}
          type="number"
          inputMode="numeric"
          min={0}
          max={100}
          step={1}
          value={seciliSkor}
          placeholder="0"
          onChange={(e) => yaz("min_score", e.target.value)}
          className="sayi h-8 w-20 border border-cizgi bg-kagit px-2 text-govde tabular-nums"
        />
      </Alan>

      <div className="ml-auto flex items-center gap-4 self-center">
        {filtreVar && (
          <button
            type="button"
            onClick={() =>
              router.replace(pathname as Route, { scroll: false })
            }
            className="text-govde text-kursun underline underline-offset-2"
          >
            Filtreleri temizle
          </button>
        )}
        <span className="text-kucuk text-kursun">
          <span className="sayi tabular-nums">{toplam}</span> aday
        </span>
      </div>
    </div>
  );
}

function Alan({
  etiket,
  htmlFor,
  children,
}: {
  etiket: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="flex flex-col gap-1">
      <span className="text-mikro text-kursun uppercase">{etiket}</span>
      {children}
    </label>
  );
}
