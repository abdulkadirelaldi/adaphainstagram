import type { IsletmeListesi, Istatistik } from "@/lib/api/tipler";

/**
 * REST istemcisi. Taban URL ortam değişkeninden okunur; sabit kodlama yok.
 * `NEXT_PUBLIC_API_URL` verilmezse yerel geliştirme varsayılanına düşer
 * (openapi `servers` ile aynı: http://localhost:8000).
 */
const TABAN =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** Panelin `/businesses` sorgusu — openapi query parametreleriyle birebir. */
export type IsletmeSorgusu = {
  status?: string;
  category?: string;
  min_score?: number;
  limit: number;
  offset: number;
};

export class ApiHatasi extends Error {
  constructor(
    public durum: number,
    mesaj: string,
  ) {
    super(mesaj);
    this.name = "ApiHatasi";
  }
}

async function getir<T>(yol: string, imza?: AbortSignal): Promise<T> {
  let yanit: Response;
  try {
    yanit = await fetch(`${TABAN}${yol}`, {
      headers: { accept: "application/json" },
      signal: imza,
    });
  } catch {
    // Ağ/CORS/DNS — sunucuya hiç ulaşılamadı.
    throw new ApiHatasi(0, "Sunucuya ulaşılamadı.");
  }
  if (!yanit.ok) {
    throw new ApiHatasi(yanit.status, `İstek ${yanit.status} döndü.`);
  }
  return (await yanit.json()) as T;
}

function sorguDizesi(sorgu: IsletmeSorgusu): string {
  const p = new URLSearchParams();
  if (sorgu.status !== undefined) p.set("status", sorgu.status);
  if (sorgu.category !== undefined) p.set("category", sorgu.category);
  if (sorgu.min_score !== undefined) p.set("min_score", String(sorgu.min_score));
  p.set("limit", String(sorgu.limit));
  p.set("offset", String(sorgu.offset));
  return p.toString();
}

export function getStats(imza?: AbortSignal): Promise<Istatistik> {
  return getir<Istatistik>("/stats", imza);
}

export function getBusinesses(
  sorgu: IsletmeSorgusu,
  imza?: AbortSignal,
): Promise<IsletmeListesi> {
  return getir<IsletmeListesi>(`/businesses?${sorguDizesi(sorgu)}`, imza);
}
