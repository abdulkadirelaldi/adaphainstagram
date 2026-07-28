"use client";

import { useId, useState } from "react";
import { ApiHatasi } from "@/lib/api/istemci";
import { useUpdateOutreach } from "@/lib/api/sorgular";
import { tarih } from "@/lib/bicim";
import { ERISIM_ETIKET, ERISIM_SIRA } from "@/lib/erisim";
import type {
  ErisimDurumu,
  ErisimKaydi as Kayit,
  ErisimTaslagi as Taslak,
} from "@/lib/api/tipler";

/**
 * Erişim kaydı — mesaj taslağı (kopyalanabilir) + durum takibi (insan elle).
 *
 * CLAUDE.md hukuki sınır: sistem hiçbir koşulda otomatik mesaj göndermez. Bu
 * yüzden burada iki eylem var, ikisi de insan kararı: **kopyala** (metni al) ve
 * **durumu güncelle** (nerede kaldığını kaydet). "Gönder / DM at / e-posta yolla"
 * gibi bir eylem **bilinçle yoktur**. "Sent" bir insanın mesajı elle gönderip
 * işaretlemesidir; arayüz göndermez, kaydeder.
 */
export function ErisimKaydi({ taslak }: { taslak: Taslak }) {
  const durumId = useId();
  const [kopyalandi, setKopyalandi] = useState(false);
  const [durum, setDurum] = useState<ErisimDurumu>(taslak.status);
  // PATCH sonrası tam kayıt (sent_at/replied_at damgaları).
  const [kayit, setKayit] = useState<Kayit | null>(null);

  const guncelle = useUpdateOutreach();

  async function kopyala() {
    try {
      await navigator.clipboard.writeText(taslak.draft);
      setKopyalandi(true);
      window.setTimeout(() => setKopyalandi(false), 2000);
    } catch {
      setKopyalandi(false);
    }
  }

  function durumDegistir(yeni: ErisimDurumu) {
    if (yeni === durum || guncelle.isPending) return;
    guncelle.mutate(
      { id: taslak.id, status: yeni },
      {
        onSuccess: (k) => {
          setDurum(k.status);
          setKayit(k);
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-mikro text-kursun uppercase">
          Erişim mesajı · taslak
        </span>
        <span className="sayi text-mikro text-kursun">{taslak.channel}</span>
      </div>

      <p className="border border-cizgi p-3 whitespace-pre-wrap">
        {taslak.draft}
      </p>

      <button
        type="button"
        onClick={kopyala}
        className="h-8 self-start border border-murekkep px-4 text-govde"
      >
        {kopyalandi ? "Kopyalandı" : "Kopyala"}
      </button>

      {/* Durum takibi — insan kararını kaydeder, mesaj göndermez. */}
      <div className="mt-1 flex flex-col gap-1">
        <label htmlFor={durumId} className="text-mikro text-kursun uppercase">
          Erişim durumu
        </label>
        <div className="flex items-center gap-3">
          <select
            id={durumId}
            value={durum}
            disabled={guncelle.isPending}
            onChange={(e) => durumDegistir(e.target.value as ErisimDurumu)}
            className="h-8 border border-cizgi bg-kagit px-2 text-govde disabled:text-kursun"
          >
            {ERISIM_SIRA.map((d) => (
              <option key={d} value={d}>
                {ERISIM_ETIKET[d]}
              </option>
            ))}
          </select>
          {guncelle.isPending && (
            <span className="text-kucuk text-kursun">Kaydediliyor…</span>
          )}
        </div>

        {guncelle.isError && (
          <p className="text-kucuk">
            Durum güncellenemedi.{" "}
            {guncelle.error instanceof ApiHatasi && guncelle.error.durum === 422
              ? "Bu geçiş geçerli değil."
              : "Bağlantıyı kontrol edip yeniden deneyin."}
          </p>
        )}

        {/* Sunucu damgaları — yalnız ilgili duruma geçilmişse dolu. */}
        {kayit && (kayit.sent_at !== null || kayit.replied_at !== null) && (
          <div className="mt-1 flex gap-4 text-kucuk text-kursun">
            {kayit.sent_at !== null && (
              <span>
                Gönderildi:{" "}
                <span className="sayi tabular-nums">{tarih(kayit.sent_at)}</span>
              </span>
            )}
            {kayit.replied_at !== null && (
              <span>
                Yanıtlandı:{" "}
                <span className="sayi tabular-nums">
                  {tarih(kayit.replied_at)}
                </span>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
