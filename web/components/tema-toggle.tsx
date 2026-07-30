"use client";

import { useEffect, useState } from "react";

type Tema = "acik" | "koyu";

/**
 * Açık / koyu tema anahtarı. Kullanıcı seçimi localStorage'da kalır ve
 * `<html>`'e `tema-acik` / `tema-koyu` sınıfı olarak yazılır (tokens.css okur).
 * Seçim yoksa sistem tercihi (`prefers-color-scheme`) geçerlidir.
 */
export function TemaToggle() {
  const [tema, setTema] = useState<Tema | null>(null);

  // İlk render'da mevcut durumu oku (init script <html>'e zaten uygulamış olabilir).
  useEffect(() => {
    const kok = document.documentElement;
    if (kok.classList.contains("tema-koyu")) setTema("koyu");
    else if (kok.classList.contains("tema-acik")) setTema("acik");
    else {
      const sistem = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTema(sistem ? "koyu" : "acik");
    }
  }, []);

  function degistir() {
    const yeni: Tema = tema === "koyu" ? "acik" : "koyu";
    const kok = document.documentElement;
    kok.classList.remove("tema-koyu", "tema-acik");
    kok.classList.add(yeni === "koyu" ? "tema-koyu" : "tema-acik");
    try {
      localStorage.setItem("radar-tema", yeni);
    } catch {
      // localStorage erişilemezse sessiz geç; seçim oturumluk kalır.
    }
    setTema(yeni);
  }

  const koyu = tema === "koyu";

  return (
    <button
      type="button"
      onClick={degistir}
      aria-label={koyu ? "Açık temaya geç" : "Koyu temaya geç"}
      className="flex h-9 w-9 items-center justify-center rounded-buton text-metin-2 hover:bg-yuzey-2 hover:text-metin"
    >
      {/* İkon renk taşımaz; simge + aria-label birlikte durumu söyler. */}
      {tema === null ? null : koyu ? <GunesIkon /> : <AyIkon />}
    </button>
  );
}

function GunesIkon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

function AyIkon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
