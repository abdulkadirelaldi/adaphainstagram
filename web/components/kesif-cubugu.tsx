"use client";

import { useId, useState } from "react";
import { useJob, useRunDiscovery } from "@/lib/api/sorgular";
import { ApiHatasi } from "@/lib/api/istemci";
import { sayi } from "@/lib/bicim";
import type { IsHali } from "@/lib/api/tipler";

/**
 * Keşif çubuğu — üst şeridin üstünde ince bir eylem satırı.
 *
 * Kullanıcı bir sorgu (ör. "kuyumcu") ile keşif taraması başlatır. Uç anında
 * `job_id` döner (senkron scraping yok, SPEC §7); iş `GET /jobs/{id}` ile yoklanır.
 * İş bitince aday tablosu ve üst şerit otomatik tazelenir (useJob invalidate eder).
 *
 * Durum makinesi (JobState) — her değerin görünür bir karşılığı var:
 *   queued   → "Kuyrukta"                (poll sürer)
 *   running  → "Taranıyor" + ilerleme    (poll sürer)
 *   done     → "Tarama bitti" + sonuç    (poll durur)
 *   error    → hata mesajı + tekrar dene (poll durur)
 */
export function KesifCubugu() {
  const sorguId = useId();
  const bolgeId = useId();
  const limitId = useId();

  const [jobId, setJobId] = useState<string | null>(null);
  const [sorgu, setSorgu] = useState("");
  const [bolge, setBolge] = useState("Samsun");
  const [limit, setLimit] = useState("");

  const kesif = useRunDiscovery();
  const is = useJob(jobId);

  const hal: IsHali | undefined = is.data?.status;
  const yokluyor = jobId !== null && hal !== "done" && hal !== "error";
  const mesgul = kesif.isPending || yokluyor;

  function baslat(e: React.FormEvent) {
    e.preventDefault();
    if (sorgu.trim() === "" || mesgul) return;
    const govde = {
      query: sorgu.trim(),
      region: bolge.trim() === "" ? "Samsun" : bolge.trim(),
      ...(limit.trim() === "" ? {} : { limit: Number(limit) }),
    };
    kesif.mutate(govde, {
      onSuccess: (kabul) => setJobId(kabul.job_id),
    });
  }

  function sifirla() {
    setJobId(null);
    kesif.reset();
  }

  return (
    <section
      aria-label="Keşif taraması"
      className="flex flex-wrap items-end gap-5 rounded-kart border border-ayrac bg-yuzey px-6 py-5 shadow-kart"
    >
      <form onSubmit={baslat} className="flex flex-wrap items-end gap-4">
        <Alan etiket="Keşif sorgusu" htmlFor={sorguId}>
          <input
            id={sorguId}
            value={sorgu}
            onChange={(e) => setSorgu(e.target.value)}
            disabled={mesgul}
            placeholder="kuyumcu, diş kliniği…"
            className="h-10 w-60 rounded-girdi border border-ayrac bg-yuzey px-3 text-govde text-metin placeholder:text-metin-2 disabled:opacity-60"
          />
        </Alan>
        <Alan etiket="Bölge" htmlFor={bolgeId}>
          <input
            id={bolgeId}
            value={bolge}
            onChange={(e) => setBolge(e.target.value)}
            disabled={mesgul}
            className="h-10 w-40 rounded-girdi border border-ayrac bg-yuzey px-3 text-govde text-metin disabled:opacity-60"
          />
        </Alan>
        <Alan etiket="En fazla" htmlFor={limitId}>
          <input
            id={limitId}
            type="number"
            inputMode="numeric"
            min={1}
            max={200}
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            disabled={mesgul}
            placeholder="varsayılan"
            className="sayi h-10 w-32 rounded-girdi border border-ayrac bg-yuzey px-3 text-govde text-metin tabular-nums placeholder:text-metin-2 disabled:opacity-60"
          />
        </Alan>
        <button
          type="submit"
          disabled={mesgul || sorgu.trim() === ""}
          className="h-10 rounded-buton bg-marka px-5 text-govde font-semibold text-marka-metin transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {mesgul ? "Taranıyor" : "Tara"}
        </button>
      </form>

      <div className="ml-auto self-center">
        <Durum
          kesifHatasi={kesif.isError ? kesif.error : null}
          isSorgusuHatasi={is.isError ? is.error : null}
          hal={hal}
          progress={is.data?.progress ?? null}
          sonuc={is.data?.result ?? null}
          hataMesaji={is.data?.error ?? null}
          onKapat={sifirla}
          onTekrar={sifirla}
        />
      </div>
    </section>
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
      <span className="text-mikro text-metin-2 uppercase">{etiket}</span>
      {children}
    </label>
  );
}

function Durum({
  kesifHatasi,
  isSorgusuHatasi,
  hal,
  progress,
  sonuc,
  hataMesaji,
  onKapat,
  onTekrar,
}: {
  kesifHatasi: unknown;
  isSorgusuHatasi: unknown;
  hal: IsHali | undefined;
  progress: { processed: number; total: number | null } | null;
  sonuc: { businesses: number; snapshots: number } | null;
  hataMesaji: string | null;
  onKapat: () => void;
  onTekrar: () => void;
}) {
  // Keşif hiç başlatılamadıysa (mutation hatası).
  if (kesifHatasi !== null) {
    return (
      <SatirMesaj>
        <span>Keşif başlatılamadı. {apiMesaj(kesifHatasi)}</span>
        <Baglanti onClick={onTekrar}>Tekrar dene</Baglanti>
      </SatirMesaj>
    );
  }

  // Job kaybolmuş / süresi dolmuş (yoklama hatası, ör. 404).
  if (isSorgusuHatasi !== null) {
    return (
      <SatirMesaj>
        <span>İş durumu alınamadı. {apiMesaj(isSorgusuHatasi)}</span>
        <Baglanti onClick={onTekrar}>Kapat</Baglanti>
      </SatirMesaj>
    );
  }

  if (hal === undefined) return null;

  if (hal === "queued") {
    return <SatirMesaj>Kuyrukta…</SatirMesaj>;
  }

  if (hal === "running") {
    return (
      <SatirMesaj>
        <span>Taranıyor</span>
        <Ilerleme progress={progress} />
      </SatirMesaj>
    );
  }

  if (hal === "done") {
    return (
      <SatirMesaj>
        <span>
          Tarama bitti · <span className="sayi tabular-nums">{sayi(sonuc?.businesses ?? 0)}</span>{" "}
          işletme, <span className="sayi tabular-nums">{sayi(sonuc?.snapshots ?? 0)}</span>{" "}
          snapshot
        </span>
        <Baglanti onClick={onKapat}>Kapat</Baglanti>
      </SatirMesaj>
    );
  }

  // hal === "error"
  return (
    <SatirMesaj>
      <span>Tarama başarısız. {hataMesaji ?? "Bilinmeyen hata."}</span>
      <Baglanti onClick={onTekrar}>Tekrar dene</Baglanti>
    </SatirMesaj>
  );
}

function Ilerleme({
  progress,
}: {
  progress: { processed: number; total: number | null } | null;
}) {
  if (progress === null) return null;
  const { processed, total } = progress;

  // total bilinmiyorsa sadece işlenen sayıyı göster; sahte bir oran çizme.
  if (total === null || total === 0) {
    return (
      <span className="sayi text-kucuk text-metin-2 tabular-nums">
        {sayi(processed)}
      </span>
    );
  }

  const oran = Math.min(100, Math.round((processed / total) * 100));
  return (
    <span className="flex items-center gap-2">
      <span
        className="h-1 w-24 bg-ayrac"
        role="progressbar"
        aria-valuenow={processed}
        aria-valuemin={0}
        aria-valuemax={total}
      >
        <span className="block h-1 bg-marka" style={{ width: `${oran}%` }} />
      </span>
      <span className="sayi text-kucuk text-metin-2 tabular-nums">
        {sayi(processed)}/{sayi(total)}
      </span>
    </span>
  );
}

// Not: hata durumlarında oksit KULLANILMAZ. Oksit yalnızca kritik denetim
// bulgusuna ayrılmış sinyal rengidir (DESIGN §1); keşif operasyon hatası bir
// bulgu değildir. Mesaj mürekkeple okunur — renkli olan tek şey skordur.
function SatirMesaj({ children }: { children: React.ReactNode }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 text-govde"
    >
      {children}
    </div>
  );
}

function Baglanti({
  onClick,
  children,
}: {
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-govde underline underline-offset-2"
    >
      {children}
    </button>
  );
}

function apiMesaj(hata: unknown): string {
  if (hata instanceof ApiHatasi) return hata.message;
  return "Bağlantıyı kontrol edip yeniden deneyin.";
}
