"use client";

import { useEffect } from "react";
import { useState } from "react";
import { ApiHatasi } from "@/lib/api/istemci";
import { useAudit, useJob, useRunAudit } from "@/lib/api/sorgular";
import { BulguListesi } from "@/components/bulgu-listesi";
import { ErisimTaslagi } from "@/components/erisim-taslagi";
import { para, tarih } from "@/lib/bicim";
import type { Isletme } from "@/lib/api/tipler";

/**
 * Denetim paneli — sağdan açılan drawer. Nitelikli bir hesap için derin denetimi
 * tetikler, işi yoklar ve sonucu (görünürlük skoru + bulgular + rapor + erişim
 * taslağı) gösterir.
 *
 * Yalnızca `qualified` hesap denetlenir (SPEC §1); düğme yalnız onlarda aktif.
 * İş deseni keşifle aynı: uç anında `job_id`, `GET /jobs/{id}` yoklaması (useJob),
 * `done`'da `result.audit_id` ile denetim çekilir.
 */
export function DenetimPaneli({
  isletme,
  onKapat,
}: {
  isletme: Isletme;
  onKapat: () => void;
}) {
  const [jobId, setJobId] = useState<string | null>(null);
  const denetle = useRunAudit();
  const is = useJob(jobId);

  const auditId =
    is.data?.status === "done" ? (is.data.result?.audit_id ?? null) : null;
  const denetim = useAudit(auditId);

  const nitelikli = isletme.status === "qualified";
  const yokluyor =
    jobId !== null && is.data?.status !== "done" && is.data?.status !== "error";
  const mesgul = denetle.isPending || yokluyor;

  // Esc ile kapat.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onKapat();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onKapat]);

  function baslat() {
    if (!nitelikli || mesgul) return;
    denetle.mutate(isletme.id, { onSuccess: (k) => setJobId(k.job_id) });
  }

  return (
    <>
      {/* Şeffaf tık-kapat alanı — karartma yok (DESIGN: gölge/karartma yok). */}
      <div className="fixed inset-0 z-10" aria-hidden onClick={onKapat} />
      <aside
        role="dialog"
        aria-label={`${isletme.name} denetimi`}
        className="fixed inset-y-0 right-0 z-20 flex w-[520px] max-w-full flex-col border-l border-cizgi bg-kagit"
      >
        <header className="flex items-start justify-between gap-4 border-b border-cizgi px-6 py-4">
          <div className="flex flex-col">
            <span className="text-buyuk">{isletme.name}</span>
            {isletme.ig_handle && (
              <span className="sayi text-kucuk text-kursun">
                @{isletme.ig_handle}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onKapat}
            className="text-govde text-kursun underline underline-offset-2"
          >
            Kapat
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          <Icerik
            nitelikli={nitelikli}
            mesgul={mesgul}
            hal={is.data?.status}
            progress={is.data?.progress ?? null}
            baslatHatasi={denetle.isError ? denetle.error : null}
            isHatasi={is.isError ? is.error : null}
            jobHata={is.data?.status === "error" ? is.data.error : null}
            denetim={denetim}
            onBaslat={baslat}
          />
        </div>
      </aside>
    </>
  );
}

function Icerik({
  nitelikli,
  mesgul,
  hal,
  progress,
  baslatHatasi,
  isHatasi,
  jobHata,
  denetim,
  onBaslat,
}: {
  nitelikli: boolean;
  mesgul: boolean;
  hal: string | undefined;
  progress: { processed: number; total: number | null } | null;
  baslatHatasi: unknown;
  isHatasi: unknown;
  jobHata: string | null;
  denetim: ReturnType<typeof useAudit>;
  onBaslat: () => void;
}) {
  // Nitelikli değil — düğme yok, sebep açık (SPEC §1).
  if (!nitelikli) {
    return (
      <p className="text-kursun">
        Derin denetim yalnızca nitelikli hesaplara üretilir. Bu hesap henüz
        nitelikli değil; triyaj skoru 70&apos;e ulaştığında denetlenebilir.
      </p>
    );
  }

  // Denetim başlatılamadı (mutation hatası — ör. 409 nitelikli değil).
  if (baslatHatasi !== null) {
    const dokuz =
      baslatHatasi instanceof ApiHatasi && baslatHatasi.durum === 409;
    return (
      <SatirHata onTekrar={onBaslat}>
        {dokuz
          ? "Bu hesap artık nitelikli değil; denetim başlatılamadı."
          : `Denetim başlatılamadı. ${apiMesaj(baslatHatasi)}`}
      </SatirHata>
    );
  }

  // İş kaybolmuş / yoklama hatası.
  if (isHatasi !== null) {
    return (
      <SatirHata onTekrar={onBaslat}>
        İş durumu alınamadı. {apiMesaj(isHatasi)}
      </SatirHata>
    );
  }

  // İş hatası.
  if (hal === "error") {
    return (
      <SatirHata onTekrar={onBaslat}>
        Denetim başarısız. {jobHata ?? "Bilinmeyen hata."}
      </SatirHata>
    );
  }

  // Çalışıyor.
  if (mesgul || hal === "queued" || hal === "running") {
    return (
      <p className="text-kursun">
        Denetleniyor…
        {progress && progress.total !== null && (
          <span className="sayi ml-2 tabular-nums">
            {progress.processed}/{progress.total}
          </span>
        )}
      </p>
    );
  }

  // İş bitti — denetim yükleniyor / geldi.
  if (hal === "done") {
    if (denetim.isPending) return <p className="text-kursun">Rapor yükleniyor…</p>;
    if (denetim.isError)
      return (
        <p className="text-kursun">
          Rapor yüklenemedi. {apiMesaj(denetim.error)}
        </p>
      );
    if (denetim.data) return <Sonuc denetim={denetim.data} />;
  }

  // Henüz tetiklenmedi.
  return (
    <div className="flex flex-col gap-3">
      <p className="text-kursun">
        Bu hesap nitelikli. Derin denetim, deterministik bulguları çıkarır ve
        ajans kalitesinde bir rapor taslağı hazırlar.
      </p>
      <button
        type="button"
        onClick={onBaslat}
        className="h-8 self-start border border-murekkep px-4 text-govde"
      >
        Derin denetim
      </button>
    </div>
  );
}

function Sonuc({ denetim }: { denetim: import("@/lib/api/tipler").Denetim }) {
  return (
    <div className="flex flex-col gap-6">
      {/* Görünürlük skoru — DİKKAT: triyaj skorunun TERSİ yönde. Düşük skor kötü.
          İki skor asla karıştırılmaz (DESIGN §5); yön burada metinle söylenir. */}
      <section>
        <span className="text-mikro text-kursun uppercase">
          Görünürlük skoru
        </span>
        <div className="mt-1 flex items-baseline gap-3">
          <span className="sayi text-rakam tabular-nums">
            {Math.floor(denetim.visibility_score)}
          </span>
          <span className="text-kucuk text-kursun">/ 100</span>
        </div>
        <p className="mt-1 text-kucuk text-kursun">
          Düşük skor, hesabın kötü yönetildiğini gösterir — fırsat bu.
          (Tablodaki triyaj skorunun tersi yönde okunur.)
        </p>
      </section>

      <section>
        <span className="text-mikro text-kursun uppercase">Bulgular</span>
        <div className="mt-2">
          <BulguListesi bulgular={denetim.findings} />
        </div>
      </section>

      <section>
        <span className="text-mikro text-kursun uppercase">Rapor metni</span>
        {denetim.report_text !== null && denetim.report_text.trim() !== "" ? (
          <p className="mt-2 whitespace-pre-wrap">{denetim.report_text}</p>
        ) : (
          <p className="mt-2 text-kursun">
            Rapor metni yapay zekâ sentezi tamamlanınca burada görünür; henüz
            üretilmedi.
          </p>
        )}
      </section>

      <section>
        {denetim.outreach !== null ? (
          <ErisimTaslagi taslak={denetim.outreach} />
        ) : (
          <>
            <span className="text-mikro text-kursun uppercase">
              Erişim mesajı · taslak
            </span>
            <p className="mt-2 text-kursun">
              Erişim taslağı rapor senteziyle birlikte üretilir; henüz hazır
              değil. Üretildiğinde yalnızca kopyalanabilir olacak — gönderme
              kararı insanda.
            </p>
          </>
        )}
      </section>

      <footer className="flex justify-between border-t border-cizgi pt-3 text-mikro text-kursun">
        <span>
          LLM maliyeti{" "}
          <span className="sayi tabular-nums">
            {para(denetim.llm_cost_usd)}
          </span>
        </span>
        <span className="sayi tabular-nums">{tarih(denetim.generated_at)}</span>
      </footer>
    </div>
  );
}

function SatirHata({
  children,
  onTekrar,
}: {
  children: React.ReactNode;
  onTekrar: () => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p>{children}</p>
      <button
        type="button"
        onClick={onTekrar}
        className="h-8 self-start border border-cizgi px-3 text-govde"
      >
        Tekrar dene
      </button>
    </div>
  );
}

function apiMesaj(hata: unknown): string {
  if (hata instanceof ApiHatasi) return hata.message;
  return "Bağlantıyı kontrol edip yeniden deneyin.";
}
