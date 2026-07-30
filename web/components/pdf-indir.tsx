"use client";

import { useState } from "react";
import { ApiHatasi, getAuditPdf } from "@/lib/api/istemci";

/**
 * PDF indir düğmesi. `pdf_path` null iken PDF henüz üretilmemiştir (uç 409
 * dönerdi) — düğme **pasif** ve sebep açık. Üretildiyse düğme, raporu binary
 * olarak çekip tarayıcıya indirtir (blob → geçici bağlantı).
 */
export function PdfIndir({
  auditId,
  hazir,
}: {
  auditId: number;
  /** `Audit.pdf_path` dolu mu — PDF üretildi mi. */
  hazir: boolean;
}) {
  const [iniyor, setIniyor] = useState(false);
  const [hata, setHata] = useState<string | null>(null);

  async function indir() {
    if (!hazir || iniyor) return;
    setHata(null);
    setIniyor(true);
    try {
      const blob = await getAuditPdf(auditId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `radar-denetim-${auditId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setHata(
        e instanceof ApiHatasi && e.durum === 409
          ? "PDF henüz üretilmedi."
          : "PDF indirilemedi. Yeniden deneyin.",
      );
    } finally {
      setIniyor(false);
    }
  }

  if (!hazir) {
    return (
      <div className="flex flex-col gap-1">
        <button
          type="button"
          disabled
          className="h-10 self-start rounded-buton border border-ayrac px-4 text-govde font-medium text-metin-2 opacity-60"
        >
          PDF indir
        </button>
        <span className="text-kucuk text-metin-2">
          PDF rapor üretiliyor; hazır olduğunda indirilebilir.
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={indir}
        disabled={iniyor}
        className="h-10 self-start rounded-buton border border-marka px-4 text-govde font-semibold text-marka transition-colors hover:bg-marka-yumusak disabled:opacity-50"
      >
        {iniyor ? "İndiriliyor" : "PDF indir"}
      </button>
      {hata && <span className="text-kucuk">{hata}</span>}
    </div>
  );
}
