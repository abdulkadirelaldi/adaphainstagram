"use client";

import { useState } from "react";
import type { ErisimTaslagi as Taslak } from "@/lib/api/tipler";

/**
 * Erişim mesajı taslağı — kopyalanabilir, ASLA gönderilebilir değil.
 *
 * CLAUDE.md hukuki sınır: sistem hiçbir koşulda otomatik mesaj göndermez; kayıt
 * `draft` durumunda doğar, gönderme kararı insandadır. Bu yüzden burada tek eylem
 * **kopyalamaktır** — "gönder" düğmesi bilinçle yoktur. "Taslak" etiketi bunu
 * her bakışta hatırlatır.
 */
export function ErisimTaslagi({ taslak }: { taslak: Taslak }) {
  const [kopyalandi, setKopyalandi] = useState(false);

  async function kopyala() {
    try {
      await navigator.clipboard.writeText(taslak.draft);
      setKopyalandi(true);
      window.setTimeout(() => setKopyalandi(false), 2000);
    } catch {
      // Pano erişimi reddedildiyse sessiz kal; metin zaten seçilip kopyalanabilir.
      setKopyalandi(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
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
    </div>
  );
}
